"""Product search: multi-token matching with relevance scoring."""

from __future__ import annotations

import re
from typing import Any


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(query: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", _normalize(query)) if len(t) >= 2]


def _token_matches(token: str, *fields: str) -> bool:
    """Match whole field substring or word prefix (e.g. algo → algorithms)."""
    for raw in fields:
        text = _normalize(str(raw))
        if not text:
            continue
        if token in text:
            return True
        for word in text.split():
            if len(word) >= 2 and (token in word or word.startswith(token)):
                return True
    return False


# Common queries → category slugs when the synced feed has no literal match
QUERY_CATEGORY_HINTS: dict[str, list[str]] = {
    "iphone": ["smartphones", "mobile-accessories"],
    "phone": ["smartphones"],
    "laptop": ["laptops"],
    "electronics": ["laptops", "smartphones", "mobile-accessories", "tablets"],
}


def _searchable_text(doc: dict) -> str:
    parts = [
        doc.get("name", ""),
        doc.get("description", ""),
        doc.get("category", ""),
        doc.get("category_slug", ""),
        doc.get("brand", ""),
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

    if tokens:
        matched_tokens = 0
        for token in tokens:
            token_score = 0.0
            if _token_matches(token, doc.get("name", "")):
                token_score = 12
            elif _token_matches(
                token,
                doc.get("category", ""),
                doc.get("category_slug", ""),
                doc.get("brand", ""),
            ):
                token_score = 8
            elif _token_matches(token, doc.get("description", "")):
                token_score = 6
            elif _token_matches(token, blob):
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


def _rank(docs: list[dict], query: str, tokens: list[str], limit: int) -> list[dict[str, Any]]:
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


def _rank_any_token(docs: list[dict], query: str, tokens: list[str], limit: int) -> list[dict[str, Any]]:
    """Fallback: match if any token hits (broader, for typos / loose queries)."""
    if not tokens:
        return []
    ranked: list[tuple[float, dict]] = []
    for doc in docs:
        blob = _searchable_text(doc)
        hits = sum(
            1
            for t in tokens
            if _token_matches(
                t,
                doc.get("name", ""),
                doc.get("category", ""),
                doc.get("description", ""),
                blob,
            )
        )
        if hits == 0:
            continue
        score = hits * 10 + float(doc.get("rating") or 0)
        ranked.append((score, doc))
    ranked.sort(key=lambda x: (-x[0], -x[1].get("rating", 0)))
    out = []
    for s, doc in ranked[:limit]:
        item = dict(doc)
        item["relevance_score"] = round(s, 2)
        out.append(item)
    return out


def _rank_category_hints(docs: list[dict], query: str, limit: int) -> list[dict[str, Any]]:
    slugs = QUERY_CATEGORY_HINTS.get(_normalize(query), [])
    if not slugs:
        return []
    ranked: list[tuple[float, dict]] = []
    for doc in docs:
        slug = _normalize(str(doc.get("category_slug", "")))
        if slug not in slugs:
            continue
        score = 15 + float(doc.get("rating") or 0) + min(float(doc.get("review_count") or 0) / 500, 5)
        ranked.append((score, doc))
    ranked.sort(key=lambda x: (-x[0], -x[1].get("rating", 0)))
    out = []
    for s, doc in ranked[:limit]:
        item = dict(doc)
        item["relevance_score"] = round(s, 2)
        out.append(item)
    return out


def search_products(docs: list[dict], query: str, limit: int = 48) -> list[dict[str, Any]]:
    q = _normalize(query)
    if not q:
        return []

    tokens = _tokens(query)
    # Strict: all tokens must match (e.g. micro + oven → microwave)
    results = _rank(docs, query, tokens, limit)
    if results:
        return results
    # Fallback: any token matches (e.g. "running" or partial terms)
    if tokens:
        results = _rank_any_token(docs, query, tokens, limit)
        if results:
            return results
    # Category hints (e.g. "iphone" → smartphones when titles use "iPhone 13 Pro")
    return _rank_category_hints(docs, query, limit)


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
