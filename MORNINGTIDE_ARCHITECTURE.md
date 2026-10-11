# MorningTide Journal: Architecture Brief

## One-sentence description

MorningTide is a private, full-stack reflective journaling application: users write dated diary entries, receive ML-based emotion analysis and history/calendar views, and can generate personalized, therapist-facing discussion topics using retrieval-augmented generation (RAG).

## Product intent

The product is a journaling companion, not a diagnostic or replacement therapist. Its highest-value workflow is: capture a user's own words, make emotional patterns easier to notice, and help the user prepare concrete topics for a real therapy session. The RAG output should therefore be supportive, bounded, explainable, and grounded in the user's entries plus a curated therapy-topic corpus.

## System shape

- **Frontend:** React single-page application with protected routes for chatbot/session preparation, diary editing, calendar, and history. Axios calls the backend and attaches a JWT from local storage.
- **Backend:** Flask application factory in `app/__init__.py`; CORS, route blueprints, database initialization, lazy ML/RAG initialization, health routes, and global error handling.
- **Persistence:** SQLite database (`users`, `journal_entries`, `analysis_results`). Journal entries are user-scoped; an entry is unique per user/date in the application workflow and is updated when the same date is saved again.
- **Authentication:** Signup/login hash passwords with Werkzeug and issue 30-day HS256 JWTs. Journal and analysis routes validate the bearer token and enforce ownership before reading or mutating data.
- **Emotion ML:** A fine-tuned DistilBERT sequence classifier with 20 emotion classes. Inference returns top emotions, probabilities, and a valence-derived 1-10 emotional score.
- **RAG:** Local Sentence Transformers embeddings (`all-MiniLM-L6-v2`, 384 dimensions), normalized-cosine FAISS search, deterministic lexical/theme reranking, a curated JSON therapy corpus, and Ollama chat generation (default `llama3.2:3b`).

## Main user flows

### Journal and emotion analysis

1. The user authenticates and receives a JWT.
2. The user creates or updates a dated entry through `/api/journal/entries`.
3. `/api/analysis/analyze` accepts an entry ID or raw text, verifies ownership when an ID is supplied, runs adaptive emotion inference, and persists the result for an entry.
4. The frontend retrieves entries with their saved analysis and renders diary, calendar, and history views.

For short text, the classifier runs once. For long text, `AdaptiveEmotionAnalyzer` splits the entry into sentences, drops trivial fragments, scores sentence importance, classifies each sentence, and computes an importance-weighted aggregate. Importance can be keyword/pattern based or locally ML-based, with keyword fallback. This avoids letting a long entry exceed the classifier's token window or letting unimportant sentences dominate the result.

### RAG therapy-session preparation

1. The authenticated client sends one or more `{date, content}` diary entries, the user's `question`, and `top_k` to `/api/rag/generate-suggestions`.
2. The pipeline sorts entries by date, builds a recent-first extractive summary, extracts lightweight themes, and calculates a chronological date range.
3. The combined question and summary are embedded and searched against FAISS. Theme queries add candidates; records are deduplicated and reranked.
4. The top topics and journal summary are passed to Ollama's `/api/chat` endpoint with source labels, citations, and a context-window budget.
5. Ollama answers the user's actual question. For session preparation, it suggests practical discussion topics and reflection questions without diagnosing or prescribing.
6. The API returns status, timestamp, diary metadata, retrieved-topic count, generated suggestions, and model name.

## RAG architecture

### Offline/indexing path

The default source corpus is `data/therapy_corpus/`, containing the curated JSON topics and PDF resources. PDFs are extracted one page at a time and split into overlapping word-count chunks; each chunk retains its PDF source and one-based page number. `TherapyCorpusIndexer` streams documents into configurable embedding batches (`RAG_EMBED_BATCH_SIZE`, default 16), then stores normalized vectors in FAISS and records in a parallel metadata pickle. The persisted index is loaded on the first RAG request; an empty or incompatible index is rebuilt. `/api/rag/rebuild-index` performs a synchronous rebuild.

### Online/query path

`RAGPipeline` owns the embedder, `FAISSVectorStore`, `TherapyRetriever`, and `OllamaGenerator`. The retriever normalizes document and query vectors and uses FAISS `IndexFlatIP`, making inner product equivalent to cosine similarity. Scores are mapped to `[0, 1]`. The pipeline combines two signals:

- **Semantic query:** the diary summary captures meaning and paraphrase.
- **Theme queries:** extracted keywords provide interpretable lexical anchors and increase recall for obvious topics.

The retriever fetches up to four times the requested `top_k` (at most 50) as candidates. Results from summary and theme queries are deduplicated by topic ID and reranked. Each score is `0.70 * semantic + 0.20 * query-term overlap + 0.10 * theme overlap`. The generator receives the question, a bounded recent summary, and selected corpus text, not an unbounded dump of journal history.

### Reranking stage

`app/ml/rag/reranker.py` implements a deterministic lexical reranker over candidate titles, categories, content, and keywords. It combines normalized semantic, query-term, and extracted-theme scores. This separates **recall** (wide FAISS candidate generation) from **precision/context ordering** (reranking). It is intentionally a simple baseline: it does not yet cross-encode query/document pairs or enforce category diversity. A later evaluation can compare it to a cross-encoder using labeled query-to-topic examples.

### Generation and safety boundary

The system prompt tells the LLM to answer the user's actual question, be empathetic and practical, cite supplied references as `[n]`, and not diagnose or prescribe. Full retrieved text is included within an approximate character budget derived from the model context and output budgets. The UI uses `stream: false`; true token-by-token browser streaming is not implemented. Retrieved material helps ground responses but cannot guarantee factuality.

## API surface

- `POST /auth/signup`, `POST /auth/login`, `GET /auth/verify`: account and token lifecycle.
- `POST/GET/DELETE /api/journal/entries` and `GET /api/journal/entries/<id>`: user-scoped diary CRUD and date-range history.
- `POST /api/analysis/analyze`, `GET /api/analysis/<entry_id>`: emotion inference and persisted analysis.
- `POST /api/rag/generate-suggestions`: authenticated, end-to-end question + diary + retrieval + generation workflow.
- `POST /api/rag/retrieve-topics`: authenticated direct retrieval/debugging surface.
- `GET /api/rag/health`, `GET /api/rag/index-stats`: operational visibility.
- `POST /api/rag/rebuild-index`: corpus reindexing.

## Startup and dependencies

The Flask app creates the SQLite schema and registers blueprints. The first `/api/rag/*` request lazily loads the embedder and index independently of the optional emotion checkpoint. Ollama is not required for retrieval startup; if it is unavailable or the configured model is missing, health reports a degraded state and generation returns an actionable 503. Configuration is centralized in `app/config.py` and can be overridden with environment variables such as `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `VECTOR_STORE_PATH`, `RAG_TOP_K_RETRIEVAL`, and `RAG_CORPUS_PATH`.

## Interview-level design decisions

- **Why RAG instead of fine-tuning the generator?** The therapy corpus can be revised or expanded without retraining the LLM; retrieval provides source control and lets the model personalize stable guidance with current diary context.
- **Why dense embeddings plus themes?** Embeddings handle semantic similarity and paraphrase; themes provide a cheap interpretable signal and improve recall for known concerns.
- **Why FAISS?** It is fast, local, dependency-light for a small curated corpus, and avoids sending private diary data to a hosted vector service.
- **Why local Ollama?** It supports offline/local inference and keeps sensitive journal context inside the user's environment, at the cost of model availability and latency management.
- **Why adaptive emotion analysis?** DistilBERT has a finite input length; sentence-level importance weighting preserves salient emotional signals in long entries while retaining a fast direct path for short entries.
- **Why persist analysis separately?** Journal text and derived results have different lifecycles, and a cached analysis avoids recomputing the model for every history view.

## Assumed working behavior and known improvement points

For architectural discussion, local embedding, retrieval, reranking, authenticated UI/API wiring, and mocked end-to-end generation have been exercised. Real Ollama generation remains unverified until Ollama and `llama3.2:3b` are installed. Remaining quality work includes indexing the PDFs with page-level citations, adding a labeled retrieval evaluation set, improving diary summarization, securing the development secret, validating dates, adding index versioning/atomic pair persistence, and testing answer grounding. The heuristic reranker is a baseline, not a guarantee of relevance.

## Compact mental model

`React client(question + latest 10 diary entries) -> JWT-protected Flask API -> recent-first summary + themes -> normalized cosine candidates -> lexical/theme rerank -> bounded cited prompt -> Ollama /api/chat -> answer`
