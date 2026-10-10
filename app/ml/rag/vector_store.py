"""
Vector Store Management using FAISS

Handles embedding storage, indexing, and semantic similarity search
for therapy corpus documents.
"""

import os
import logging
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import faiss


logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for semantic search over therapy corpus."""

    def __init__(
        self,
        store_path: str = "./data/vector_store",
        dimension: int = 384
    ):
        """
        Initialize FAISS vector store. 

        Args:
            store_path: Path to store FAISS index files
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.dimension = dimension
        self. index_file = self.store_path / "therapy_index.faiss"
        self.metadata_file = self.store_path / "metadata.pkl"

        self. index:  Optional[faiss.IndexFlatL2] = None
        self. metadata: List[Dict] = []

        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        if self.index_file. exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(
                    f"✓ Loaded FAISS index with {self.index.ntotal} documents"
                )
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        logger.info(f"✓ Created new FAISS index (dimension={self.dimension})")

    def add_documents(
        self,
        embeddings: np.ndarray,
        documents: List[Dict]
    ) -> None:
        """
        Add documents with their embeddings to the index. 

        Args:
            embeddings:  Array of shape (n_docs, dimension)
            documents: List of document metadata dictionaries
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings.shape[1]} "
                f"does not match index dimension {self.dimension}"
            )

        # Convert to float32 (required by FAISS)
        embeddings = embeddings.astype(np. float32)

        # Add to index
        self.index.add(embeddings)
        self.metadata.extend(documents)

        logger.info(
            f"✓ Added {len(documents)} documents "
            f"(total: {self.index.ntotal})"
        )

        # Save to disk
        self. save()

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector (1, dimension)
            k: Number of results to return

        Returns:
            List of (document, distance) tuples sorted by relevance
        """
        if self.index. ntotal == 0:
            logger.warning("Vector store is empty")
            return []

        # Ensure proper shape and type
        query_embedding = query_embedding.astype(np. float32)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        # Convert distances to similarity scores (L2 distance -> similarity)
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= 0:  # Valid index
                doc = self.metadata[idx]
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                similarity = 1.0 / (1.0 + distance)
                results.append((doc, similarity))

        return results

    def clear(self) -> None:
        """Clear the index and metadata."""
        self._create_new_index()
        self.save()
        logger.info("✓ Vector store cleared")

    def save(self) -> None:
        """Save index and metadata to disk."""
        if self.index is None:
            return

        faiss.write_index(self. index, str(self.index_file))
        with open(self.metadata_file, "wb") as f:
            pickle.dump(self.metadata, f)

        logger.debug(f"✓ Saved vector store to {self.store_path}")

    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            "total_documents": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "store_path": str(self.store_path),
            "index_file_exists": self.index_file.exists(),
            "metadata_file_exists": self.metadata_file. exists(),
        }