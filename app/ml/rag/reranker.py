"""Deterministic second-stage ranking for a small therapy-topic corpus."""

import re
from typing import Dict, List, Set


_TOKEN_PATTERN = re.compile(r"[a-z0-9']+")
_STOP_WORDS = {
    "a", "about", "after", "again", "all", "am", "an", "and", "are",
    "as", "at", "be", "because", "been", "being", "but", "by", "can",
    "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "me", "my", "of", "on", "or", "our", "ours",
    "she", "so", "that", "the", "their", "them", "there", "they", "this",
    "to", "too", "up", "us", "was", "we", "were", "what", "when", "which",
    "who", "will", "with", "would", "you", "your",
}


def _terms(text: str) -> Set[str]:
    return {
        token for token in _TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in _STOP_WORDS
    }


class TherapyReranker:
    """Combine cosine relevance with query-word and extracted-theme overlap."""

    def rerank(
        self,
        candidates: List[Dict],
        query: str,
        themes: List[str],
        k: int,
    ) -> List[Dict]:
        query_terms = _terms(query)
        theme_terms = _terms(" ".join(themes))
        ranked = []

        for candidate in candidates:
            keywords = candidate.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]
            document_text = " ".join(
                [
                    candidate.get("title", ""),
                    candidate.get("category", ""),
                    candidate.get("content", ""),
                    " ".join(str(keyword) for keyword in keywords),
                ]
            )
            document_terms = _terms(document_text)
            semantic = float(candidate.get("similarity_score", 0.0))
            keyword = (
                len(query_terms & document_terms) / len(query_terms)
                if query_terms else 0.0
            )
            theme = (
                len(theme_terms & document_terms) / len(theme_terms)
                if theme_terms else 0.0
            )
            score = 0.70 * semantic + 0.20 * keyword + 0.10 * theme
            ranked.append(
                {
                    **candidate,
                    "semantic_score": semantic,
                    "keyword_score": keyword,
                    "theme_score": theme,
                    "rerank_score": score,
                }
            )

        ranked.sort(
            key=lambda item: (item["rerank_score"], item.get("id", "")),
            reverse=True,
        )
        return ranked[:max(0, k)]