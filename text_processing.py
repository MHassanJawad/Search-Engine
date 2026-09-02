"""Shared, dependency-free text normalization for indexing and searching."""

from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)?|\d+", re.UNICODE)

IRREGULAR_NOUNS = {
    "children": "child",
    "feet": "foot",
    "geese": "goose",
    "men": "man",
    "mice": "mouse",
    "people": "person",
    "teeth": "tooth",
    "women": "woman",
}


def tokenize(text: object) -> list[str]:
    """Return lowercase searchable tokens without requiring NLTK data files."""
    return [token.replace("’", "'") for token in TOKEN_RE.findall(str(text).lower())]


def singular_candidate(word: str) -> str:
    """Approximate WordNet's default noun lemmatization for legacy indexes."""
    if word in IRREGULAR_NOUNS:
        return IRREGULAR_NOUNS[word]
    if len(word) <= 3 or word.endswith(("ss", "us", "is")) or word == "news":
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "xes", "zes")):
        return word[:-2]
    if word.endswith("s"):
        return word[:-1]
    return word


def token_candidates(word: str) -> tuple[str, ...]:
    """Return spellings that may occur in old WordNet-generated barrels."""
    singular = singular_candidate(word)
    return (word,) if singular == word else (word, singular)
