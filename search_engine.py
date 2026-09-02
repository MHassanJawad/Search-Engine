"""BM25 retrieval over the project's on-disk barrel indexes."""

from __future__ import annotations

import json
import math
from collections import OrderedDict, defaultdict
from pathlib import Path
from threading import RLock
from typing import Any

from text_processing import token_candidates, tokenize


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "datasets"


class IndexDataError(RuntimeError):
    """Raised when generated search-index files are missing or malformed."""


class SearchEngine:
    def __init__(self, data_dir: Path | str = DEFAULT_DATA_DIR, barrel_cache_size: int = 4):
        self.data_dir = Path(data_dir)
        self.barrel_cache_size = max(1, barrel_cache_size)
        self._cache: OrderedDict[str, dict[str, dict[str, Any]]] = OrderedDict()
        self._cache_lock = RLock()
        self.doc_metadata = self._load_object("doc_metadata.json")
        raw_lengths = self._load_object("doc_lengths.json")
        try:
            self.doc_lengths = {str(key): float(value) for key, value in raw_lengths.items()}
        except (TypeError, ValueError) as exc:
            raise IndexDataError("doc_lengths.json contains a non-numeric length") from exc
        self.total_docs = len(self.doc_lengths)
        self.avg_doc_len = (
            sum(self.doc_lengths.values()) / self.total_docs if self.total_docs else 0.0
        )

    def _load_object(self, filename: str) -> dict[str, Any]:
        path = self.data_dir / filename
        try:
            with path.open("r", encoding="utf-8") as file:
                value = json.load(file)
        except FileNotFoundError as exc:
            raise IndexDataError(
                f"Missing {path}. Generate the indexes with: python make_json.py"
            ) from exc
        except json.JSONDecodeError as exc:
            raise IndexDataError(f"Invalid JSON in {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise IndexDataError(f"{path} must contain a JSON object")
        return value

    @staticmethod
    def _barrel_name(token: str) -> str:
        first = token[0] if token else ""
        return first if "a" <= first <= "z" else "other"

    def _load_barrel(self, name: str) -> dict[str, dict[str, Any]]:
        with self._cache_lock:
            cached = self._cache.get(name)
            if cached is not None:
                self._cache.move_to_end(name)
                return cached

            path = self.data_dir / f"barrel_{name}.json"
            if not path.exists():
                # Older generated datasets contain only a-z barrels.
                if name == "other":
                    return {}
                raise IndexDataError(
                    f"Missing {path}. Generate the indexes with: python make_json.py"
                )
            try:
                with path.open("r", encoding="utf-8") as file:
                    barrel = json.load(file)
            except json.JSONDecodeError as exc:
                raise IndexDataError(f"Invalid JSON in {path}: {exc}") from exc
            if not isinstance(barrel, dict):
                raise IndexDataError(f"{path} must contain a JSON object")

            self._cache[name] = barrel
            self._cache.move_to_end(name)
            while len(self._cache) > self.barrel_cache_size:
                self._cache.popitem(last=False)
            return barrel

    def _resolve_terms(self, query: str) -> list[tuple[str, dict[str, Any]]]:
        resolved: list[tuple[str, dict[str, Any]]] = []
        seen: set[str] = set()
        for raw_token in tokenize(query):
            for candidate in token_candidates(raw_token):
                if candidate in seen:
                    continue
                barrel = self._load_barrel(self._barrel_name(candidate))
                postings = barrel.get(candidate)
                if isinstance(postings, dict):
                    resolved.append((candidate, postings))
                    seen.add(candidate)
                    break
        return resolved

    def search(self, query: str) -> list[dict[str, Any]]:
        """Return documents matching any query term, ranked with BM25."""
        if not query.strip() or not self.total_docs or not self.avg_doc_len:
            return []

        scores: defaultdict[str, float] = defaultdict(float)
        matched_terms: defaultdict[str, int] = defaultdict(int)

        for term, postings in self._resolve_terms(query):
            document_frequency = len(postings)
            if not document_frequency:
                continue
            idf = math.log(
                1 + (self.total_docs - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            for raw_doc_id, raw_frequency in postings.items():
                doc_id = str(raw_doc_id)
                try:
                    frequency = float(raw_frequency)
                except (TypeError, ValueError):
                    continue
                if frequency <= 0:
                    continue
                length = self.doc_lengths.get(doc_id, self.avg_doc_len)
                denominator = frequency + 1.5 * (
                    1 - 0.75 + 0.75 * length / self.avg_doc_len
                )
                scores[doc_id] += idf * (frequency * 2.5 / denominator)
                matched_terms[doc_id] += 1

                title = str(self.doc_metadata.get(doc_id, {}).get("title") or "").lower()
                if term in tokenize(title):
                    scores[doc_id] += 0.35 * idf

        ranked_ids = sorted(
            scores,
            key=lambda doc_id: (matched_terms[doc_id], scores[doc_id], doc_id),
            reverse=True,
        )
        results: list[dict[str, Any]] = []
        for doc_id in ranked_ids:
            metadata = self.doc_metadata.get(doc_id, {})
            results.append(
                {
                    "doc_id": doc_id,
                    "title": metadata.get("title") or "No title available",
                    "description": metadata.get("description") or "No description available",
                    "url": metadata.get("url") or "",
                    "url_to_image": metadata.get("url_to_image") or "",
                    "score": round(scores[doc_id], 6),
                    "matched_terms": matched_terms[doc_id],
                }
            )
        return results


_default_engine: SearchEngine | None = None
_default_engine_lock = RLock()


def get_default_engine() -> SearchEngine:
    global _default_engine
    with _default_engine_lock:
        if _default_engine is None:
            _default_engine = SearchEngine()
        return _default_engine


def search_query(query: str) -> dict[str, Any]:
    results = get_default_engine().search(query)
    return {"total_results": len(results), "results": results}
