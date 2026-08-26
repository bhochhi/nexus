"""Approved local knowledge retrieval adapter."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, List


@dataclass(frozen=True)
class KnowledgeResult:
    source_id: str
    title: str
    answer: str
    disclosure: str
    score: int


class LocalKnowledgeTool:
    name = "local_knowledge"
    actions = ("search",)
    _stop_words = {
        "a",
        "an",
        "and",
        "does",
        "how",
        "i",
        "is",
        "my",
        "the",
        "what",
        "work",
    }

    def __init__(self, path: Path):
        self.path = Path(path)

    def search(self, query: str, limit: int = 1) -> List[KnowledgeResult]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        query_terms = self._terms(query)
        results = []
        for article in payload.get("articles", []):
            searchable = " ".join(
                [article["title"], article["answer"], " ".join(article.get("keywords", []))]
            )
            score = len(query_terms.intersection(self._terms(searchable)))
            if score:
                results.append(
                    KnowledgeResult(
                        source_id=article["id"],
                        title=article["title"],
                        answer=article["answer"],
                        disclosure=article.get("disclosure", ""),
                        score=score,
                    )
                )
        return sorted(results, key=lambda result: result.score, reverse=True)[:limit]

    def _terms(self, text: str):
        return {
            term
            for term in re.findall(r"[a-z0-9]+", text.lower())
            if len(term) > 1 and term not in self._stop_words
        }

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action != "search":
            raise ValueError("Unsupported local knowledge action: {}".format(action))
        return [
            {
                "source_id": result.source_id,
                "title": result.title,
                "answer": result.answer,
                "disclosure": result.disclosure,
                "score": result.score,
            }
            for result in self.search(
                str(arguments["query"]), int(arguments.get("limit", 1))
            )
        ]
