"""
Offline RAG index build. Run from a terminal, not the debugger or a notebook:

    python -m scripts.build_index [--force] [--batch-size 32]

Streams the corpus (JSON topics and PDF pages) through bounded embedding
batches into a staging store, then swaps it in only on success.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import logging
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the therapy corpus vector index")
    parser.add_argument("--force", action="store_true", help="rebuild even if the index is current")
    parser.add_argument("--batch-size", type=int, default=32, help="documents embedded per batch")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from app.config import Config
    from app.ml.rag.embedding import SentenceTransformerEmbedder
    from app.ml.rag.indexer import TherapyCorpusIndexer
    from app.ml.rag.vector_store import FAISSVectorStore

    embedder = SentenceTransformerEmbedder(model_name=Config.EMBEDDING_MODEL, device="cpu")
    store = FAISSVectorStore(Config.VECTOR_STORE_PATH, dimension=embedder.get_dimension())
    indexer = TherapyCorpusIndexer(embedder, store)

    if not args.force and indexer.is_index_current(
        Config.RAG_CORPUS_PATH,
        chunk_size=Config.RAG_CHUNK_SIZE,
        chunk_overlap=Config.RAG_CHUNK_OVERLAP,
    ):
        print(f"Index is current ({store.index.ntotal} documents); use --force to rebuild.")
        return 0

    started = time.monotonic()
    indexer.build_index(
        Config.RAG_CORPUS_PATH,
        chunk_size=Config.RAG_CHUNK_SIZE,
        chunk_overlap=Config.RAG_CHUNK_OVERLAP,
        batch_size=args.batch_size,
    )
    print(f"Done: {store.index.ntotal} documents in {time.monotonic() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
