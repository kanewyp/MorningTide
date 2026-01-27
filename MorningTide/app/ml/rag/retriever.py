"""
Retriever Module for Semantic Search

Combines embeddings and vector store to retrieve relevant therapy topics.
"""

import logging
from typing import List, Dict, Tuple
from . embedding import SentenceTransformerEmbedder
from .vector_store import FAISSVectorStore


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
        if self.vector_store.index. ntotal == 0:
            logger.warning("Vector store is empty, returning empty results")
            return []

        try:
            # Embed query
            query_embedding = self. embedder.embed_query(query)

            # Search
            results = self.vector_store.search(query_embedding, k=k)

            # Format results
            documents = [
                {
                    **doc,
                    "similarity_score": float(similarity)
                }
                for doc, similarity in results
            ]

            logger.debug(
                f"Retrieved {len(documents)} documents for query:  {query[: 50]}..."
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
            results = self.retrieve(keyword, k=k)
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

        # Sort by similarity and return top k
        sorted_results = sorted(
            all_results.values(),
            key=lambda x:  x.get("similarity_score", 0),
            reverse=True
        )
        return sorted_results[:k]