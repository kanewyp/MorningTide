"""
Retriever Module for Semantic Search

Combines embeddings and vector store to retrieve relevant therapy topics.
"""

import logging
from typing import List, Dict, Tuple
from . embedding import SentenceTransformerEmbedder
from .vector_store import FAISSVectorStore
from .reranker import TherapyReranker


logger = logging.getLogger(__name__)


class TherapyRetriever:
    """Retrieves relevant therapy topics using semantic search."""

    def __init__(
        self,
        embedder: SentenceTransformerEmbedder,
        vector_store: FAISSVectorStore
    ):
        """
        Initialize retriever.

        Args:
            embedder: Embedding provider instance
            vector_store: Vector store instance
        """
        self. embedder = embedder
        self.vector_store = vector_store
        self.reranker = TherapyReranker()

    def retrieve_candidates(self, query: str, k: int = 20) -> List[Dict]:
        """Fetch a broad semantic candidate set for later ranking."""
        if not query.strip() or self.vector_store.index.ntotal == 0:
            return []

        query_embedding = self.embedder.embed_query(query)
        results = self.vector_store.search(query_embedding, k=k)
        return [
            {**document, "similarity_score": float(score)}
            for document, score in results
        ]

    def retrieve(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Retrieve top-k relevant therapy topics for a query.

        Args:
            query: Query text (e.g., user context or diary summary)
            k: Number of results to return

        Returns:
            List of relevant therapy topic documents
        """
        try:
            candidates = self.retrieve_candidates(query, k=max(k * 4, k))
            documents = self.reranker.rerank(candidates, query, [], k)
            logger.debug(
                f"Retrieved {len(documents)} documents for query: {query[:50]}..."
            )
            return documents

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise RuntimeError(f"Failed to retrieve documents: {e}")

    def retrieve_by_keywords(
        self,
        keywords: List[str],
        k: int = 5
    ) -> List[Dict]:
        """
        Retrieve documents by combining multiple keyword queries.

        Args:
            keywords: List of keywords to search
            k: Number of results to return

        Returns:
            Combined and deduplicated list of relevant documents
        """
        all_results = {}

        for keyword in keywords:
            results = self.retrieve_candidates(keyword, k=k)
            for doc in results:
                doc_id = doc. get("id", "")
                if doc_id not in all_results: 
                    all_results[doc_id] = doc
                else:
                    # Update similarity if higher
                    all_results[doc_id]["similarity_score"] = max(
                        all_results[doc_id]["similarity_score"],
                        doc. get("similarity_score", 0)
                    )

        return self.reranker.rerank(
            list(all_results.values()),
            " ".join(keywords),
            keywords,
            k,
        )