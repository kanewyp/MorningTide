"""
Indexer Module for Building Vector Index

Loads therapy corpus, generates embeddings, and builds FAISS index.
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from .embedding import SentenceTransformerEmbedder
from .vector_store import FAISSVectorStore


logger = logging.getLogger(__name__)


class TherapyCorpusIndexer: 
    """Indexes therapy corpus documents for semantic search."""

    def __init__(
        self,
        embedder: SentenceTransformerEmbedder,
        vector_store: FAISSVectorStore
    ):
        """
        Initialize indexer.

        Args:
            embedder: Embedding provider instance
            vector_store: Vector store instance
        """
        self. embedder = embedder
        self.vector_store = vector_store

    def load_corpus(self, corpus_path: str) -> List[Dict]:
        """
        Load therapy corpus from JSON file. 

        Args:
            corpus_path: Path to corpus JSON file

        Returns:
            List of topic documents
        """
        try: 
            with open(corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            topics = data.get("topics", [])
            logger.info(f"✓ Loaded {len(topics)} therapy topics from {corpus_path}")
            return topics

        except FileNotFoundError:
            logger.error(f"Corpus file not found: {corpus_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse corpus JSON: {e}")
            raise

    def build_index(self, corpus_path: str) -> None:
        """
        Build index from corpus file.

        Args:
            corpus_path: Path to corpus JSON file
        """
        # Load corpus
        topics = self. load_corpus(corpus_path)

        if not topics:
            logger.warning("No topics to index")
            return

        # Clear existing index
        self.vector_store.clear()

        # Extract texts for embedding
        texts = [
            f"{topic. get('title', '')} {topic.get('category', '')} {topic.get('content', '')}"
            for topic in topics
        ]

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedder.embed_batch(texts)

        # Add to vector store
        self.vector_store.add_documents(embeddings, topics)

        logger.info(
            f"✓ Indexed {len(topics)} therapy topics "
            f"(store:  {self.vector_store.get_stats()['total_documents']})"
        )

    def update_index(self, new_topics: List[Dict]) -> None:
        """
        Add new topics to existing index.

        Args:
            new_topics:  List of new topic documents
        """
        if not new_topics:
            logger.warning("No topics to add")
            return

        # Generate embeddings
        texts = [
            f"{topic. get('title', '')} {topic.get('category', '')} {topic.get('content', '')}"
            for topic in new_topics
        ]

        embeddings = self.embedder.embed_batch(texts)

        # Add to store
        self.vector_store. add_documents(embeddings, new_topics)
        logger.info(
            f"✓ Added {len(new_topics)} new topics to index"
        )