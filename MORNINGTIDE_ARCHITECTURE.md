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
- **RAG:** Local Sentence Transformers embeddings (`all-MiniLM-L6-v2`, 384 dimensions), FAISS vector search, a curated JSON therapy corpus, and a local Ollama model (default `mistral`) for final generation.

## Main user flows

### Journal and emotion analysis

1. The user authenticates and receives a JWT.
2. The user creates or updates a dated entry through `/api/journal/entries`.
3. `/api/analysis/analyze` accepts an entry ID or raw text, verifies ownership when an ID is supplied, runs adaptive emotion inference, and persists the result for an entry.
4. The frontend retrieves entries with their saved analysis and renders diary, calendar, and history views.

For short text, the classifier runs once. For long text, `AdaptiveEmotionAnalyzer` splits the entry into sentences, drops trivial fragments, scores sentence importance, classifies each sentence, and computes an importance-weighted aggregate. Importance can be keyword/pattern based or locally ML-based, with keyword fallback. This avoids letting a long entry exceed the classifier's token window or letting unimportant sentences dominate the result.

### RAG therapy-session preparation

1. The client sends one or more `{date, content}` diary entries to `/api/rag/generate-suggestions` with `top_k` and optional streaming.
2. The pipeline combines entries with date markers, creates a compact summary, extracts lightweight themes such as anxiety, sleep, work, grief, or relationships, and calculates the date range.
3. The summary is embedded and searched against the FAISS index. Theme keywords are also searched and merged by document ID.
4. Retrieved topic records are ranked and passed as bounded context to Ollama with the diary summary.
5. Ollama returns 3-5 structured discussion topics. Each should contain a title, why it relates to the entries, a therapy connection, a specific reflection/discussion prompt, and a suggested session focus.
6. The API returns status, timestamp, diary metadata, retrieved-topic count, generated suggestions, and model name.

## RAG architecture

### Offline/indexing path

The source corpus is `data/therapy_corpus/seed_corpus.json`. Each topic contains an ID, category, title, explanatory content, keywords, difficulty, and related-topic IDs. `TherapyCorpusIndexer` embeds the concatenation of title, category, and content, then stores vectors in FAISS and the original records in a parallel metadata pickle. The persisted index is loaded at startup; an empty index is rebuilt automatically. `/api/rag/rebuild-index` supports explicit rebuilds.

### Online/query path

`RAGPipeline` owns the embedder, `FAISSVectorStore`, `TherapyRetriever`, and `OllamaGenerator`. The retriever performs dense semantic search using L2 distance converted to a bounded similarity score `1 / (1 + distance)`. The pipeline combines two signals:

- **Semantic query:** the diary summary captures meaning and paraphrase.
- **Theme queries:** extracted keywords provide interpretable lexical anchors and increase recall for obvious topics.

Results are deduplicated by topic ID and truncated to the configured top-k/context budget. The generator receives only the summary and selected corpus snippets, not an unbounded dump of the user's history.

### Simple reranking stage

The repository's current retrieval path is effectively first-stage dense retrieval plus theme-result merging; it has no independent cross-encoder reranker. The intended production-quality/simple completion is:

1. Retrieve a wider candidate set, for example 15-30 topics, using FAISS and keyword/theme search.
2. Normalize each candidate's semantic score and compute a lexical/theme overlap score from the candidate title, category, content, and keywords.
3. Optionally add small metadata bonuses for matching category, difficulty, or related themes; apply a diversity penalty when several candidates have the same category.
4. Rank with a transparent weighted score such as `0.70 * semantic + 0.20 * theme_overlap + 0.10 * metadata_fit`, then keep the final 5-8 topics.

This is a useful interview explanation because it separates **recall** (FAISS candidate generation) from **precision/context quality** (reranking). A stronger later version could replace the heuristic with a cross-encoder that scores `(diary summary, candidate topic)` pairs, but the simple scorer is deterministic, cheap, local, and easy to test.

### Generation and safety boundary

The system prompt tells the LLM to be empathetic, non-judgmental, practical, evidence-aware, and explicit that it does not replace therapy. The model is asked to suggest conversation topics and reflection prompts, not diagnose, prescribe, or claim certainty. Retrieved corpus content grounds the language and reduces purely free-form hallucination; the user's journal remains the personalization source.

## API surface

- `POST /auth/signup`, `POST /auth/login`, `GET /auth/verify`: account and token lifecycle.
- `POST/GET/DELETE /api/journal/entries` and `GET /api/journal/entries/<id>`: user-scoped diary CRUD and date-range history.
- `POST /api/analysis/analyze`, `GET /api/analysis/<entry_id>`: emotion inference and persisted analysis.
- `POST /api/rag/generate-suggestions`: end-to-end diary-to-suggestions workflow.
- `POST /api/rag/retrieve-topics`: direct retrieval/debugging surface.
- `GET /api/rag/health`, `GET /api/rag/index-stats`: operational visibility.
- `POST /api/rag/rebuild-index`: corpus reindexing.

## Startup and dependencies

The Flask app creates the SQLite schema and registers blueprints. On the first request it loads the emotion model and initializes the RAG pipeline. RAG startup requires the embedding model, FAISS, a readable corpus/index location, and an accessible Ollama server with the configured model. Configuration is centralized in `app/config.py` and can be overridden with environment variables such as `OLLAMA_MODEL`, `EMBEDDING_MODEL`, `VECTOR_STORE_PATH`, `RAG_TOP_K_RETRIEVAL`, and `RAG_CORPUS_PATH`.

## Interview-level design decisions

- **Why RAG instead of fine-tuning the generator?** The therapy corpus can be revised or expanded without retraining the LLM; retrieval provides source control and lets the model personalize stable guidance with current diary context.
- **Why dense embeddings plus themes?** Embeddings handle semantic similarity and paraphrase; themes provide a cheap interpretable signal and improve recall for known concerns.
- **Why FAISS?** It is fast, local, dependency-light for a small curated corpus, and avoids sending private diary data to a hosted vector service.
- **Why local Ollama?** It supports offline/local inference and keeps sensitive journal context inside the user's environment, at the cost of model availability and latency management.
- **Why adaptive emotion analysis?** DistilBERT has a finite input length; sentence-level importance weighting preserves salient emotional signals in long entries while retaining a fast direct path for short entries.
- **Why persist analysis separately?** Journal text and derived results have different lifecycles, and a cached analysis avoids recomputing the model for every history view.

## Assumed working behavior and known improvement points

For architectural discussion, treat initialization, retrieval, and generation as operational. In a real maintenance pass, the most important hardening areas are explicit reranking, per-request pipeline configuration instead of mutating shared `top_k`, stronger date validation, secret/configuration management, stricter prompt/context token budgeting, index versioning and atomic rebuilds, and tests that validate ranking quality and grounding rather than only response shape. Streaming would also need a true streaming HTTP response contract instead of collecting the stream into one string.

## Compact mental model

`React client -> JWT-protected Flask API -> SQLite journal + cached emotion analysis -> RAGPipeline(summary/themes -> embed -> FAISS candidates -> rerank -> bounded prompt -> Ollama) -> structured therapy-session preparation`
