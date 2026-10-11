"""
Embedding Provider using Sentence Transformers

Generates embeddings for documents and queries for semantic search.
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    """Generates embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """
        Initialize embedder with specified model.

        Args:
            model_name: HuggingFace model identifier
            device: 'cpu', 'xpu' and 'cuda'
        """
        self.model_name = model_name
        self.device = device

        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(
                f"✓ Loaded embedding model:  {model_name} "
                f"(dimension={self.dimension}, device={device})"
            )
        except Exception as e: 
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Cannot load embedding model {model_name}:  {e}")

    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Embed text(s).

        Args:
            text:  Single string or list of strings

        Returns: 
            Embeddings as numpy array (n_texts, dimension)
        """
        try:
            embeddings = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query text.

        Args:
            query: Query text

        Returns:
            Query embedding (1, dimension)
        """
        return self.embed_text(query)

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """
        Embed a batch of texts in bounded model-sized sub-batches.

        Args:
            texts: List of strings
            batch_size: Texts encoded per model forward pass
            show_progress_bar: Display tqdm progress while encoding

        Returns:
            Normalized embeddings (n_texts, dimension)
        """
        try:
            return self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=show_progress_bar,
            )
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension