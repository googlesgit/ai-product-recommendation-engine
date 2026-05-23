"""Product search: multi-token matching with relevance scoring."""

from __future__ import annotations

import re
from typing import Any


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(query: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", _normalize(query)) if len(t) >= 2]


def _searchable_text(doc: dict) -> str:
    parts = [
        doc.get("name", ""),
        doc.get("description", ""),
        doc.get("category", ""),
    ]
    tags = doc.get("tags") or []
    if isinstance(tags, list):
        parts.extend(tags)
    return _normalize(" ".join(str(p) for p in parts))


def score_product(doc: dict, query: str, tokens: list[str]) -> float:
    """Higher score = better match. 0 means no match."""
    name = _normalize(doc.get("name", ""))
    desc = _normalize(doc.get("description", ""))
    cat = _normalize(doc.get("category", ""))
    blob = _searchable_text(doc)
    q = _normalize(query)

    if not q:
        return 0.0

    score = 0.0

    # Full phrase in name is a strong signal (e.g. "micro oven" -> microwave product text)
    if q in name:
        score += 50
    elif q in blob:
        score += 25

    # Each token contributes; all tokens must match somewhere for a result
    if tokens:
        matched_tokens = 0
        for token in tokens:
            token_score = 0.0
            if token in name:
                token_score = 12
            elif token in cat:
                token_score = 8
            elif token in desc:
                token_score = 6
            elif token in blob:
                token_score = 4
            if token_score > 0:
                matched_tokens += 1
                score += token_score
        if matched_tokens < len(tokens):
            return 0.0
    elif q not in blob:
        return 0.0

    # Popularity tie-breaker (mild)
    rating = float(doc.get("rating") or 0)
    reviews = float(doc.get("review_count") or 0)
    score += rating * 0.5 + min(reviews / 1000.0, 5.0)

    return score


def search_products(docs: list[dict], query: str, limit: int = 48) -> list[dict[str, Any]]:
    q = _normalize(query)
    if not q:
        return []

    tokens = _tokens(query)
    ranked: list[tuple[float, dict]] = []

    for doc in docs:
        s = score_product(doc, query, tokens)
        if s > 0:
            ranked.append((s, doc))

    ranked.sort(key=lambda x: (-x[0], -x[1].get("rating", 0), -x[1].get("review_count", 0)))

    out = []
    for s, doc in ranked[:limit]:
        item = dict(doc)
        item["relevance_score"] = round(s, 2)
        out.append(item)
    return out


def suggest_queries(docs: list[dict], partial: str, limit: int = 6) -> list[str]:
    """Return example searches when query is empty or for autocomplete hints."""
    partial = _normalize(partial)
    names = [d.get("name", "") for d in docs if d.get("name")]
    categories = sorted({d.get("category", "") for d in docs if d.get("category")})

    seeds = categories + names[:12]
    if not partial:
        return seeds[:limit]

    matches = []
    for s in seeds:
        if partial in _normalize(s) and s not in matches:
            matches.append(s)
    return matches[:limit]
