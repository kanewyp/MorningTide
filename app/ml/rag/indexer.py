"""
Indexer Module for Building Vector Index

Loads therapy corpus, generates embeddings, and builds FAISS index.
"""

import json
import hashlib
import logging
import os
import re
import tempfile
from typing import List, Dict
from pathlib import Path
import pymupdf
from .embedding import SentenceTransformerEmbedder
from .vector_store import FAISSVectorStore
from .utils import chunk_text


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
        self.manifest_path = self.vector_store.store_path / "corpus_manifest.json"

    def load_corpus(
        self,
        corpus_path: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> List[Dict]:
        """
        Load therapy corpus from JSON file. 

        Args:
            corpus_path: Path to corpus JSON file

        Returns:
            List of topic documents
        """
        return list(self.iter_corpus(corpus_path, chunk_size, chunk_overlap))

    def iter_corpus(
        self,
        corpus_path: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        """Yield normalized corpus documents without retaining all PDF chunks."""
        source = Path(corpus_path)
        if not source.exists():
            raise FileNotFoundError(f"Corpus path not found: {source}")

        json_paths = sorted(source.glob("*.json")) if source.is_dir() else [source]
        for json_path in json_paths:
            if json_path.suffix.lower() != ".json":
                continue
            with json_path.open("r", encoding="utf-8") as corpus_file:
                data = json.load(corpus_file)
            records = data.get("topics", []) if isinstance(data, dict) else data
            for record in records:
                content = record.get("content") or record.get("text", "")
                if not content.strip():
                    continue
                topic = dict(record)
                topic["content"] = content.strip()
                topic.setdefault("source", record.get("source_file", json_path.name))
                topic.setdefault("title", record.get("title", record.get("doc_id", "Therapy topic")))
                topic.setdefault("category", "Curated therapy topic")
                topic.setdefault("keywords", record.get("tags", []))
                yield topic

        if source.is_dir():
            for pdf_path in sorted(source.glob("*.pdf")):
                try:
                    with pymupdf.open(pdf_path) as document:
                        for page_number, page in enumerate(document, start=1):
                            page_text = page.get_text("text").strip()
                            for chunk_number, text_chunk in enumerate(
                                chunk_text(
                                    page_text,
                                    chunk_size=chunk_size,
                                    overlap=chunk_overlap,
                                )
                            ):
                                slug = re.sub(r"[^a-z0-9]+", "_", pdf_path.stem.lower()).strip("_")
                                yield {
                                    "id": f"pdf_{slug}_p{page_number}_c{chunk_number}",
                                    "title": pdf_path.stem,
                                    "category": "Therapy resource",
                                    "content": text_chunk,
                                    "keywords": [],
                                    "source": pdf_path.name,
                                    "page": page_number,
                                }
                except Exception:
                    logger.exception("Could not extract text from %s", pdf_path)

        logger.info("Finished reading therapy corpus from %s", source)

    def _source_fingerprint(
        self,
        corpus_path: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> str:
        source = Path(corpus_path)
        files = sorted(
            path for path in (source.rglob("*") if source.is_dir() else [source])
            if path.is_file() and path.suffix.lower() in {".json", ".pdf"}
        )
        state = [
            (str(path.relative_to(source)) if source.is_dir() else path.name,
             path.stat().st_size, path.stat().st_mtime_ns)
            for path in files
        ]
        payload = {
            "files": state,
            "embedding_model": self.embedder.model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def is_index_current(
        self,
        corpus_path: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> bool:
        if self.vector_store.index.ntotal == 0 or not self.manifest_path.exists():
            return False
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return manifest.get("fingerprint") == self._source_fingerprint(
                corpus_path, chunk_size, chunk_overlap
            )
        except (OSError, ValueError):
            return False

    def build_index(
        self,
        corpus_path: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        batch_size: int = 16,
    ) -> None:
        """
        Build index from corpus file.

        Args:
            corpus_path: Path to corpus JSON file
        """
        if chunk_size < 1 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_size must be positive and overlap in [0, chunk_size)")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")

        topic_iterator = iter(self.iter_corpus(corpus_path, chunk_size, chunk_overlap))
        first_topic = next(topic_iterator, None)
        if first_topic is None:
            logger.warning("No topics to index")
            return

        topics = [first_topic]
        while len(topics) < batch_size:
            topic = next(topic_iterator, None)
            if topic is None:
                break
            topics.append(topic)

        first_embeddings = self.embedder.embed_batch(
            [self._document_text(topic) for topic in topics]
        )
        staging_directory = tempfile.TemporaryDirectory(
            prefix=".rag-index-build-",
            dir=self.vector_store.store_path.parent,
        )
        staged_store = FAISSVectorStore(
            staging_directory.name,
            dimension=self.vector_store.dimension,
        )
        indexed_count = 0

        def index_batch(batch: List[Dict]) -> None:
            nonlocal indexed_count
            texts = [self._document_text(topic) for topic in batch]
            embeddings = self.embedder.embed_batch(texts)
            staged_store.add_documents(embeddings, batch, save=False)
            indexed_count += len(batch)
            if indexed_count % (batch_size * 16) == 0:
                logger.info("Indexed %s corpus documents", indexed_count)

        staged_store.add_documents(first_embeddings, topics, save=False)
        indexed_count = len(topics)
        topics = []
        for topic in topic_iterator:
            topics.append(topic)
            if len(topics) >= batch_size:
                index_batch(topics)
                topics = []
        if topics:
            index_batch(topics)

        staged_store.save()
        self.manifest_path.unlink(missing_ok=True)
        os.replace(staged_store.index_file, self.vector_store.index_file)
        os.replace(staged_store.metadata_file, self.vector_store.metadata_file)
        self.vector_store.index = staged_store.index
        self.vector_store.metadata = staged_store.metadata
        manifest = {
            "fingerprint": self._source_fingerprint(
                corpus_path, chunk_size, chunk_overlap
            ),
            "document_count": indexed_count,
        }
        temporary_manifest = self.manifest_path.with_suffix(".tmp")
        temporary_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        temporary_manifest.replace(self.manifest_path)
        staging_directory.cleanup()

        logger.info(
            f"✓ Indexed {indexed_count} therapy topics "
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
        texts = [self._document_text(topic) for topic in new_topics]

        embeddings = self.embedder.embed_batch(texts)

        # Add to store
        self.vector_store. add_documents(embeddings, new_topics)
        logger.info(
            f"✓ Added {len(new_topics)} new topics to index"
        )

    @staticmethod
    def _document_text(topic: Dict) -> str:
        keywords = topic.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        return " ".join(
            [
                topic.get("title", ""),
                topic.get("category", ""),
                " ".join(str(keyword) for keyword in keywords),
                topic.get("content", ""),
            ]
        )