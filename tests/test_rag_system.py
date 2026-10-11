import numpy as np

from app.ml.rag.generator import OllamaConfig, OllamaGenerator
from app.ml.rag.reranker import TherapyReranker
from app.ml.rag.runner import RAGPipeline
from app.ml.rag.vector_store import FAISSVectorStore


def test_vector_store_uses_cosine_similarity_and_persists(tmp_path):
    store = FAISSVectorStore(str(tmp_path), dimension=2)
    store.add_documents(
        np.array([[4.0, 0.0], [0.0, 8.0]], dtype=np.float32),
        [{"id": "aligned"}, {"id": "orthogonal"}],
    )

    reloaded = FAISSVectorStore(str(tmp_path), dimension=2)
    results = reloaded.search(np.array([2.0, 0.0]), k=2)

    assert results[0][0]["id"] == "aligned"
    assert results[0][1] == 1.0
    assert results[1][1] == 0.5


def test_reranker_uses_keywords_and_themes():
    candidates = [
        {
            "id": "stress",
            "title": "Stress and Nervous System",
            "content": "Understanding stress responses",
            "keywords": ["stress"],
            "similarity_score": 0.9,
        },
        {
            "id": "sleep",
            "title": "Sleep Hygiene and Insomnia",
            "content": "Rest and a regular sleep schedule",
            "keywords": ["sleep", "insomnia"],
            "similarity_score": 0.82,
        },
    ]

    results = TherapyReranker().rerank(
        candidates, "I cannot sleep because of insomnia", ["sleep"], k=2
    )

    assert results[0]["id"] == "sleep"
    assert results[0]["rerank_score"] > results[1]["rerank_score"]


def test_generator_sends_ollama_chat_payload(mocker):
    response = mocker.Mock()
    response.json.return_value = {
        "message": {"content": "Bring sleep patterns up with your therapist."}
    }
    post = mocker.patch(
        "app.ml.rag.generator.requests.post", return_value=response
    )
    generator = OllamaGenerator(OllamaConfig(model="llama3.2:3b"))

    answer = generator.generate_suggestions(
        "Recent journal context",
        [{"title": "Sleep", "source": "guide.pdf", "page": 2, "content": "Sleep routines."}],
        user_question="Why am I waking up at night?",
    )

    payload = post.call_args.kwargs["json"]
    assert answer.startswith("Bring sleep")
    assert post.call_args.args[0].endswith("/api/chat")
    assert payload["messages"][0]["role"] == "system"
    assert "Why am I waking up at night?" in payload["messages"][1]["content"]
    assert "guide.pdf, page 2" in payload["messages"][1]["content"]
    assert payload["options"]["temperature"] == 0.7
    assert payload["options"]["num_ctx"] == 4096


def test_pipeline_prioritizes_recent_entries_and_isolates_top_k():
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.top_k_retrieval = 5

    class Reranker:
        def rerank(self, candidates, query, themes, k):
            assert k == 1
            return candidates[:k]

    class Retriever:
        reranker = Reranker()

        def retrieve_candidates(self, query, k):
            assert "newest" in query
            return [{"id": "sleep", "similarity_score": 0.8}]

        def retrieve_by_keywords(self, themes, k):
            return []

    pipeline.retriever = Retriever()
    analysis = pipeline.analyze_diary_entries(
        [
            {"date": "2026-10-10", "content": "newest sleep problem"},
            {"date": "2026-10-08", "content": "old work stress"},
        ]
    )

    assert analysis["date_range"] == "2026-10-08 to 2026-10-10"
    assert "newest" in analysis["summary"]
    assert pipeline.retrieve_relevant_topics(analysis, k=1, query="sleep")
    assert pipeline.top_k_retrieval == 5