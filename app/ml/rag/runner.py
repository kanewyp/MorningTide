"""
RAG Pipeline Runner - Orchestrates the complete RAG workflow

Coordinates diary analysis, retrieval, and generation for therapy suggestions.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from .embedding import SentenceTransformerEmbedder
from .vector_store import FAISSVectorStore
from .retriever import TherapyRetriever
from . generator import OllamaGenerator, OllamaConfig
from .utils import chunk_text, summarize_diary_entries


logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline for generating therapy suggestions."""

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_device: str = "cpu",
        vector_store_path: str = "./data/vector_store",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model:  str = "mistral",
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        top_k_retrieval: int = 5,
        max_context_tokens: int = 3000
    ):
        """
        Initialize RAG pipeline.

        Args:
            embedding_model: HuggingFace embedding model name
            embedding_device: 'cpu' or 'cuda'
            vector_store_path:  Path to FAISS index
            ollama_base_url:  Ollama server URL
            ollama_model: Model name to use with Ollama
            chunk_size: Size of text chunks for diary entries
            chunk_overlap: Overlap between chunks
            top_k_retrieval: Number of therapy topics to retrieve
            max_context_tokens: Maximum context tokens for LLM
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k_retrieval = top_k_retrieval
        self.max_context_tokens = max_context_tokens

        # Initialize components
        logger.info("Initializing RAG pipeline...")
        self.embedder = SentenceTransformerEmbedder(
            model_name=embedding_model,
            device=embedding_device
        )

        self.vector_store = FAISSVectorStore(
            store_path=vector_store_path,
            dimension=self.embedder.get_dimension()
        )

        self.retriever = TherapyRetriever(self.embedder, self.vector_store)

        ollama_config = OllamaConfig(
            base_url=ollama_base_url,
            model=ollama_model
        )
        self.generator = OllamaGenerator(ollama_config)

        logger.info("✓ RAG pipeline initialized")

    def analyze_diary_entries(
        self,
        entries: List[Dict[str, str]]
    ) -> Dict: 
        """
        Analyze diary entries to extract context and themes.

        Args:
            entries: List of diary entries (expected keys: 'date', 'content')

        Returns:
            Dictionary with analysis results
        """
        if not entries:
            return {
                "entry_count": 0,
                "summary": "No diary entries found.",
                "themes": [],
                "combined_text": ""
            }

        # Combine entries
        combined_text = "\n".join([
            f"[{entry. get('date', 'Unknown date')}]\n{entry.get('content', '')}"
            for entry in entries
        ])

        # Summarize
        summary = summarize_diary_entries(combined_text)

        # Extract potential themes/keywords (simplified approach)
        themes = self._extract_themes(combined_text)

        return {
            "entry_count": len(entries),
            "date_range": self._get_date_range(entries),
            "summary": summary,
            "themes": themes,
            "combined_text": combined_text
        }

    def _extract_themes(self, text:  str) -> List[str]:
        """Extract themes from text (simplified keyword extraction)."""
        # This is a simple approach; for production, use more sophisticated NLP
        keywords = [
            "anxiety", "depression", "stress", "sleep", "relationships",
            "work", "identity", "grief", "trauma", "motivation", "conflict",
            "fear", "overwhelm", "lonely", "exhausted", "angry", "sad",
            "worried", "confused", "stuck", "progress"
        ]

        themes = [
            keyword for keyword in keywords
            if keyword. lower() in text.lower()
        ]

        return list(set(themes))  # Deduplicate

    def _get_date_range(self, entries: List[Dict]) -> str:
        """Extract date range from entries."""
        if not entries:
            return "N/A"

        dates = [entry.get('date') for entry in entries if entry.get('date')]
        if len(dates) < 2:
            return dates[0] if dates else "N/A"

        return f"{dates[0]} to {dates[-1]}"

    def retrieve_relevant_topics(
        self,
        analysis: Dict
    ) -> List[Dict]:
        """
        Retrieve relevant therapy topics based on diary analysis.

        Args:
            analysis: Output from analyze_diary_entries()

        Returns:
            List of relevant therapy topics
        """
        # Use summary and themes for retrieval
        summary = analysis. get("summary", "")
        themes = analysis.get("themes", [])

        if summary: 
            # Primary retrieval using summary
            results = self.retriever.retrieve(
                summary,
                k=self.top_k_retrieval
            )
        else:
            results = []

        # Augment with theme-based retrieval
        if themes:
            theme_results = self.retriever. retrieve_by_keywords(
                themes,
                k=self.top_k_retrieval // 2
            )
            # Merge and deduplicate
            result_ids = {r.get("id"): r for r in results}
            for r in theme_results:
                if r.get("id") not in result_ids:
                    results.append(r)

        logger.info(f"Retrieved {len(results)} relevant therapy topics")
        return results

    def generate_suggestions(
        self,
        diary_entries: List[Dict[str, str]],
        stream: bool = False
    ) -> Dict:
        """
        Generate therapy suggestions for a user.

        Args:
            diary_entries: Recent diary entries
            stream: Whether to stream LLM response

        Returns:
            Dictionary with suggestions and metadata
        """
        try:
            # Analyze diary
            logger.info("Analyzing diary entries...")
            analysis = self.analyze_diary_entries(diary_entries)

            # Retrieve relevant topics
            logger.info("Retrieving relevant therapy topics...")
            topics = self.retrieve_relevant_topics(analysis)

            # Prepare context for LLM
            diary_summary = analysis.get("summary", "")
            if not diary_summary and diary_entries:
                diary_summary = analysis.get("combined_text", "")[:500]

            # Generate suggestions
            logger.info("Generating suggestions with LLM...")
            suggestions = self.generator.generate_suggestions(
                diary_context=diary_summary,
                retrieved_topics=topics,
                stream=stream
            )

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "diary_analysis": {
                    "entry_count": analysis.get("entry_count"),
                    "date_range":  analysis.get("date_range"),
                    "themes": analysis.get("themes", [])
                },
                "retrieved_topics_count": len(topics),
                "suggestions": suggestions,
                "model":  self.generator.config.model
            }

        except Exception as e:
            logger. error(f"Suggestion generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def health_check(self) -> Dict:
        """Check system health."""
        return {
            "embedder":  {
                "model":  self.embedder.model_name,
                "dimension": self.embedder.dimension,
                "device": self.embedder.device
            },
            "vector_store": self.vector_store.get_stats(),
            "generator": self.generator.health_check(),
            "timestamp": datetime.now().isoformat()
        }