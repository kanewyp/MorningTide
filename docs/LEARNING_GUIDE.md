# MorningTide Learning Guide

Goal: after this guide you can explain every file, trace any request end to end, and say what is solid versus what is being rebuilt.

Setup for all exercises (repo root):

```bash
source .venv/bin/activate
```

Tags: **[OK]** works as written, **[FIX P2]/[FIX P3]** known problem scheduled for cleanup phase 2/3, **[MISSING]** not built yet.

---

## 1. The big picture

```
React UI (frontend/)  --HTTP+JWT-->  Flask API (app/api/)  -->  SQLite (morningtide.db)
                                        |
                                        +--> Emotion model (app/ml/inference.py)   "how do I feel?"
                                        +--> RAG pipeline  (app/ml/rag/)           "what should I discuss in therapy?"
```

Three independent pipelines share one app. Learn them in this order, easiest first:

1. **Auth + journal CRUD** (plain web app)
2. **Emotion analysis** (classic ML: train, load, predict)
3. **RAG suggestions** (retrieval + LLM)

## 2. Where does every file fit?

| Path | Role | Pipeline |
|---|---|---|
| `run_server.py` | Starts Flask on port 8000 | all |
| `app/__init__.py` | App factory: CORS, blueprints, DB init, lazy ML/RAG load, `get_rag_pipeline()` global | all |
| `app/config.py` | One `Config` class: paths, model hyperparameters, emotion list, Ollama/embedding/RAG settings (env-overridable) | all |
| `app/database.py` | SQLite path, `get_db()` (raw sqlite3) and SQLAlchemy engine, `init_db()` creates 3 tables | 1 |
| `app/api/auth.py` | `/auth/signup`, `/login`, `/verify`; password hash + JWT | 1 |
| `app/api/journal.py` | `/api/journal/entries` CRUD, `token_required` decorator, one entry per user per date | 1 |
| `app/api/analysis.py` | `/api/analysis/analyze` runs the model, converts to a 1-10 score, saves to `analysis_results` | 2 |
| `app/api/rag.py` | `/api/rag/generate-suggestions`, `/retrieve-topics`, `/health`, `/index-stats`, `/rebuild-index` | 3 |
| `app/schemas/*.py` | Pydantic request/response models. **Not used by routes yet**; P3 wires in `schemas/rag.py` | 3 |
| `app/ml/model.py` | DistilBERT + custom classification head (20 labels) | 2 |
| `app/ml/preprocess.py` | `prepare_sentiment_data()` (CSV split) and `preprocess_for_inference()` (lowercase, strip punctuation) | 2 |
| `app/ml/dataset.py` | PyTorch `Dataset` that tokenizes CSV rows | 2 |
| `app/ml/train.py` | Training loop (AdamW, early stopping), writes `checkpoints/best_model.pt` | 2 |
| `app/ml/inference.py` | Singleton `EmotionClassifier`, valence-to-intensity, `analyze_emotion()` | 2 |
| `app/ml/long_text_handler.py` | Splits long entries into sentences, weights them, aggregates | 2 |
| `app/ml/importance_scorer.py` | Keyword or ML sentence-importance scorers | 2 |
| `app/ml/utils.py` | `split_into_sentences`, `count_words` | 2 |
| `app/ml/rag/embedding.py` | Text to vector (Sentence Transformers `all-MiniLM-L6-v2`, 384 dims) | 3 |
| `app/ml/rag/vector_store.py` | FAISS index + parallel metadata list, saved to `data/vector_store/` | 3 |
| `app/ml/rag/indexer.py` | Reads corpus JSON, embeds, fills the store | 3 |
| `app/ml/rag/retriever.py` | Query to top-k documents; keyword fan-out merge | 3 |
| `app/ml/rag/generator.py` | Prompt building and the Ollama HTTP call | 3 |
| `app/ml/rag/runner.py` | `RAGPipeline`: orchestrates analyze, retrieve, generate | 3 |
| `app/ml/rag/utils.py` | Chunking, summarizing, keyword extraction (partly unused) | 3 |
| `data/raw`, `data/processed` | Emotion dataset and train/validation split | 2 |
| `data/therapy_corpus/seed_corpus.json` | The 49 hand-written topics that are actually indexed | 3 |
| `data/therapy_corpus/*.pdf` | ~289 source PDFs; **not ingested yet** [FIX P2] | 3 |
| `scripts/` | One-off tools: DB reset/fix, seed fake diary data, PDF extraction, smoke test, model eval | support |
| `tests/` | pytest suites for the RAG endpoints (mocked pipeline) | support |
| `frontend/src/services/api.js` | Axios instance, attaches JWT, journal/auth/analysis calls | UI |
| `frontend/src/context/AuthContext.jsx` | Login state in React context + localStorage | UI |
| `frontend/src/App.jsx` | Routes, `ProtectedRoute`, background music | UI |
| `frontend/src/pages/*` | Thin wrappers, one per route | UI |
| `frontend/src/components/*` | Auth forms, DiaryEditor/EmotionResult, Calendar, History, Chatbot, NavBar | UI |

## 3. Run it once, then read it

```bash
python run_server.py                  # terminal 1, http://localhost:8000
cd frontend && npm install && npm start   # terminal 2, http://localhost:3000
```

Open `http://localhost:8000/` and `/health`. They show whether RAG is initialized.

---

## 4. Pipeline 1: Auth and journal (read first)

Read in this order: `database.py` then `auth.py` then `journal.py` then `frontend/src/services/api.js`.

**Concepts**
- **Password hashing**: the DB stores `pbkdf2:sha256` hashes, never passwords.
- **JWT**: a signed token `{user_id, username, exp}`. The server stores no session; it re-verifies the signature on each request. The frontend keeps it in `localStorage` and the Axios interceptor adds `Authorization: Bearer <token>`.
- **Ownership checks**: every journal query filters on `user_id` from the token, so users cannot read each other's data.
- **Upsert by date**: saving twice on the same date updates the entry.

**Exercise 1.1: walk the auth flow with curl**

```bash
curl -s -X POST localhost:8000/auth/signup -H 'Content-Type: application/json' \
  -d '{"username":"learner","password":"secret123"}'
# copy the token, then:
TOKEN=...paste...
curl -s -X POST localhost:8000/api/journal/entries -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"content":"Stressed about work today.","date":"2026-10-10"}'
curl -s localhost:8000/api/journal/entries -H "Authorization: Bearer $TOKEN"
```

**Exercise 1.2: decode the token yourself**

```bash
python -c "import jwt,sys; print(jwt.decode(sys.argv[1], options={'verify_signature':False}))" "$TOKEN"
```

Note the payload is readable by anyone; the signature only prevents tampering.

**Check yourself**: why does `get_entry` filter on both `id` and `user_id`? What happens if `SECRET_KEY` changes? (All old tokens become invalid.) **[FIX P3]**: the secret has a hard-coded fallback and `token_required` is copy-pasted in two files.

---

## 5. Pipeline 2: Emotion analysis

Read: `config.py` (emotion map) then `model.py` then `preprocess.py` then `dataset.py` then `train.py` then `inference.py` then `long_text_handler.py` then `importance_scorer.py` then `api/analysis.py`.

**Training path (offline)**
`emotion_dataset.csv` -> `prepare_sentiment_data()` -> `train.csv`/`validation.csv` -> `EmotionDataset` (tokenizes to fixed 512 ids) -> `Trainer` -> `checkpoints/best_model.pt`.

**Inference path (online)**
`text` -> `preprocess_for_inference` -> tokenizer -> DistilBERT -> `softmax` over 20 emotions -> top 3 + **intensity**.

Intensity is not predicted by the model. It is a weighted average of per-emotion valence (e.g. anger -0.85, happiness +0.85) mapped to 1-10: `(valence + 1) * 4.5 + 1`. `analysis.py` then nudges the score +/-2 using the top emotion.

**Long entries**: DistilBERT sees at most 512 tokens, and one label for a long diary hides detail. `AdaptiveEmotionAnalyzer` splits sentences, scores each sentence's importance, classifies each, then averages probabilities weighted by importance.

**Exercise 2.1: sentence splitting and importance (no model needed)**

```bash
python - <<'EOF'
from app.ml.utils import split_into_sentences
from app.ml.importance_scorer import KeywordImportanceScorer
text = "I went to the shop. I am SO anxious about tomorrow! The bus was late. I feel completely alone."
s = [x for x in split_into_sentences(text) if x.strip(".!? ")]
for sent, score in zip(s, KeywordImportanceScorer().score(s)):
    print(f"{score:.2f}  {sent}")
EOF
```

Expected: "I am SO anxious about tomorrow" about 0.82 and "I feel completely alone." 1.00, while "The bus was late" is 0.00. Also print `split_into_sentences(text)` directly: it returns `['I went to the shop', '.', 'I am SO anxious ...', '!', ...]`, so the punctuation becomes separate list items (the regex capture group keeps them). That is a real bug worth spotting. **[FIX P3]**

**Exercise 2.2: the valence math**: open `_get_emotion_valence_scores` and compute by hand the intensity for 100% `sadness` (answer about 2.1) and 100% `happiness` (about 9.3).

**Exercise 2.3 (needs a checkpoint)**: `python -m scripts.eval_emotion_model`.

**Status**: the checkpoint is gitignored. Without it `app/ml/inference.py` raises at import. **[FIX P3]**: make emotion analysis optional so RAG and the rest of the app still run.

---

## 6. Pipeline 3: RAG, the core of the project

### 6.1 Concept in five lines

An LLM does not know your user or your trusted therapy material. RAG fixes that without training:
1. **Index (offline)**: split documents into chunks, turn each into a vector (embedding), store them.
2. **Retrieve (online)**: turn the query into a vector, find the nearest chunk vectors.
3. **Rerank (optional)**: re-score the candidates with a stronger or more specific signal.
4. **Augment**: put the best chunks plus the user context into the prompt.
5. **Generate**: the LLM answers using that context.

### 6.2 Request trace: `POST /api/rag/generate-suggestions`

```
Chatbot.jsx  generateTherapySuggestions()
 -> api/rag.py  validate_diary_entries, top_k check
   -> RAGPipeline.generate_suggestions()                (runner.py)
      1 analyze_diary_entries   join entries, summarize, keyword themes
      2 retrieve_relevant_topics  summary query + per-theme queries -> merge by id
         -> TherapyRetriever.retrieve -> embed_query -> FAISS search -> docs + score
      3 OllamaGenerator.generate_suggestions
         build_system_prompt + build_user_prompt -> POST ollama /api/generate
   <- {suggestions, diary_analysis, retrieved_topics_count, model}
```

### 6.3 Stage by stage with exercises

**A. Embeddings** (`embedding.py`). A sentence becomes 384 numbers; similar meaning gives nearby vectors.

```bash
python - <<'EOF'
import numpy as np
from app.ml.rag.embedding import SentenceTransformerEmbedder
e = SentenceTransformerEmbedder(device="cpu")   # downloads ~90 MB once
a,b,c = e.embed_batch(["I can't stop worrying about work","anxiety about my job","I baked bread"])
cos = lambda x,y: float(x@y/np.linalg.norm(x)/np.linalg.norm(y))
print(cos(a,b), cos(a,c))   # first should be clearly higher
EOF
```

Expected: about 0.60 (worry vs. job anxiety) against about 0.11 (worry vs. bread).

**B. Index and vector store** (`indexer.py`, `vector_store.py`). Each topic is embedded as `title + category + content` and added to a FAISS `IndexFlatL2` (exact nearest neighbor). Metadata lives in a Python list at the same position as the vector. That position link is the whole trick.

```bash
python - <<'EOF'
import tempfile
from app.ml.rag.embedding import SentenceTransformerEmbedder
from app.ml.rag.vector_store import FAISSVectorStore
from app.ml.rag.indexer import TherapyCorpusIndexer
from app.ml.rag.retriever import TherapyRetriever
e = SentenceTransformerEmbedder(device="cpu")
store = FAISSVectorStore(tempfile.mkdtemp(), e.get_dimension())
TherapyCorpusIndexer(e, store).build_index("data/therapy_corpus/seed_corpus.json")
for d in TherapyRetriever(e, store).retrieve("I can't sleep and my mind races", k=5):
    print(round(d["similarity_score"],3), d["id"], d["title"])
EOF
```

Observed: for "I can't sleep and my mind races" the top hit is `emotion_003` (Window of Tolerance), then `sleep_001`, `depression_001`, `mindfulness_001`, and `health_002` (Mind-Body Connection). Scores are all about 0.4-0.45, so they separate poorly. `sleep_001` arguably deserves rank 1, which is exactly what reranking is for. Does each hit make sense to you? Try other queries ("my boss criticized me", "I feel numb"). **[FIX P2]**: L2 on non-normalized vectors; switch to normalized cosine (`IndexFlatIP`), which gives scores you can reason about.

**C. Query building** (`runner.py`, `utils.py`). Today the "summary" is the first sentences up to 500 characters, and themes are substring matches from a fixed keyword list. Entries arrive newest-first, so truncation keeps the wrong end and `date_range` is reversed. **[FIX P2]**: sort by date, weight recent entries, keep each entry's key sentence.

**D. Reranking [MISSING]**. First-stage vector search is fast but coarse. Planned simple reranker (P2):
1. Retrieve 15-30 candidates instead of 5.
2. Score each: `0.7 * semantic + 0.2 * keyword/theme overlap + 0.1 * metadata fit` (category match, topic `keywords` field).
3. Penalize duplicate categories to diversify; keep the top 5-6.

You will implement this yourself with a test (see section 8).

**E. Prompt assembly** (`generator.py`). The system prompt sets role and limits; the user prompt injects the diary summary and numbered topics. Today each topic is cut to 200 characters, so the LLM barely sees the knowledge. **[FIX P2]**: include full chunks within a token budget, label them `[1]`, `[2]` and require the answer to cite them.

```bash
python - <<'EOF'
from app.ml.rag.generator import OllamaGenerator
g = OllamaGenerator.__new__(OllamaGenerator)   # skip the Ollama connection check
print(g.build_user_prompt("Anxious about work deadlines.", [{"title":"Cognitive Restructuring","category":"Anxiety","content":"Examine the evidence for worries. "*10}]))
EOF
```

**F. Calling Ollama** (`generator.py`). Test the raw API first so you know what the code must do:

```bash
curl -s localhost:11434/api/chat -d '{
  "model":"llama3.2:3b","stream":false,
  "options":{"temperature":0.4,"num_predict":400},
  "messages":[{"role":"system","content":"You are concise."},{"role":"user","content":"Name two CBT techniques."}]}'
```

Current code differences **[FIX P2]**: it uses `/api/generate`, concatenates system and user text, and puts `temperature`/`top_p`/`num_predict` at the top level where Ollama ignores them (they belong under `options`). The first call after idle can take a long time while the model loads.

**G. Orchestration and startup** (`app/__init__.py`, `runner.py`). The pipeline is created lazily on the first request, inside the same `try` as the emotion model import. If the checkpoint is missing or Ollama is down, RAG stays `None` forever and every call returns 503. This explains the broken UI. **[FIX P3]**: initialize RAG independently, retry, and report Ollama status in `/api/rag/health`.

**H. UI** (`Chatbot.jsx`). It loads all entries, picks "therapy" vs "retrieve topics" by checking for words like "help", and renders the response. It uses hard-coded `fetch` URLs rather than `api.js`, and the RAG routes have no auth. **[FIX P3]**

### 6.4 Vocabulary to own

| Term | Meaning here |
|---|---|
| Embedding | 384-number vector from `all-MiniLM-L6-v2` |
| Chunk | A piece of corpus text that is embedded as one unit |
| top-k | How many candidates to fetch |
| Recall vs precision | Retrieval is for recall (do not miss the right topic); reranking is for precision (order well) |
| Grounding | Making the LLM answer from supplied context, ideally with citations |
| Context window | Max tokens the model can read; the prompt must fit |
| Hallucination | Fluent text not supported by the context |

---

## 7. Frontend in one pass

`index.js` -> `App.jsx` (router + `AuthProvider`) -> `ProtectedRoute` checks `useAuth()` -> page -> component -> `api.js`.

- Diary: `DiaryEditor` saves (`POST entries`) then analyzes (`POST analyze`, `GET analysis`) and shows `EmotionResult`.
- Calendar and History: `getEntries(start, end)`, then colour by `emotion_score`.
- Chat: Section 6.

## 8. Suggested learning path (do in order)

1. Run the app and the Section 4 curl exercises.
2. Exercises 2.1 and 2.2, then read `long_text_handler.py` with the output beside you.
3. RAG exercises A, B, E with the seed corpus. Write down which queries retrieve badly.
4. Install Ollama, run exercise F, then call the real pipeline.
5. Implement the reranker (D) in a new `app/ml/rag/reranker.py` and compare ranked lists before and after for your bad queries.
6. Replace the 200-character truncation with a token budget and cite `[n]` sources.

## 9. Questions you should be able to answer for an interview

- Why RAG instead of fine-tuning? Why FAISS locally instead of a hosted vector DB?
- What does reranking add that nearest-neighbor search does not?
- Where would you add evaluation (query to expected topic, recall@k)?
- How does the system keep user data private, and what are the auth gaps?
- Why does long-text emotion analysis weight sentences, and what are its failure modes?
