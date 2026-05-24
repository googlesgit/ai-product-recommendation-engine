"""
Recommendation engine: content-based (KNN + cosine) + item–item collaborative filtering.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

from models.collaborative import ItemCollaborativeFilter

CONTENT_WEIGHT = 0.55
CF_WEIGHT = 0.45


def _safe_id(product: dict) -> str:
    return str(product.get("_id", product.get("id", "")))


def _discover_categories(products: list[dict]) -> list[str]:
    cats = sorted({str(p.get("category") or "General") for p in products})
    return cats or ["General"]


class ProductRecommender:
    def __init__(self, use_engineered_features: bool = True):
        self.use_engineered_features = use_engineered_features
        self.products: list[dict] = []
        self.product_ids: list[str] = []
        self.feature_matrix: np.ndarray | None = None
        self._similarity_matrix: np.ndarray | None = None
        self._knn: NearestNeighbors | None = None
        self._tfidf: TfidfVectorizer | None = None
        self._category_index: dict[str, int] = {}
        self._cf = ItemCollaborativeFilter()
        self._id_to_index: dict[str, int] = {}

    def fit(self, products: list[dict]) -> None:
        self.products = products
        self.product_ids = [_safe_id(p) for p in products]
        self._id_to_index = {pid: i for i, pid in enumerate(self.product_ids)}
        self._category_index = {c: i for i, c in enumerate(_discover_categories(products))}
        self.feature_matrix = self._build_feature_matrix(products)
        if len(products) == 0:
            self._similarity_matrix = None
            self._knn = None
            return
        self._similarity_matrix = cosine_similarity(self.feature_matrix)
        n_neighbors = min(max(3, len(products)), 15)
        self._knn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
        self._knn.fit(self.feature_matrix)

    def fit_collaborative(self, interactions: list[dict]) -> None:
        self._cf.fit(interactions)

    def _build_feature_matrix(self, products: list[dict]) -> np.ndarray:
        n = len(products)
        if n == 0:
            return np.zeros((0, 1))

        if not self.use_engineered_features:
            return np.array(
                [[p.get("price", 0), p.get("rating", 0)] for p in products],
                dtype=float,
            )

        prices = np.array([p.get("price", 1) for p in products], dtype=float)
        ratings = np.array([p.get("rating", 3) for p in products], dtype=float)
        reviews = np.array([p.get("review_count", 0) for p in products], dtype=float)

        log_price = np.log1p(prices).reshape(-1, 1)
        log_price_norm = (log_price - log_price.min()) / (log_price.max() - log_price.min() + 1e-9)
        rating_norm = (ratings / 5.0).reshape(-1, 1)
        review_signal = (np.log1p(reviews) / (np.log1p(reviews).max() + 1e-9)).reshape(-1, 1)

        n_cats = max(len(self._category_index), 1)
        cat_matrix = np.zeros((n, n_cats))
        for i, p in enumerate(products):
            cat = p.get("category", "")
            if cat in self._category_index:
                cat_matrix[i, self._category_index[cat]] = 1.0

        texts = [
            f"{p.get('name', '')} {p.get('description', '')} {p.get('brand', '')}".lower()
            for p in products
        ]
        self._tfidf = TfidfVectorizer(max_features=48, stop_words="english")
        tfidf_matrix = self._tfidf.fit_transform(texts).toarray()

        return np.hstack([log_price_norm, rating_norm, review_signal, cat_matrix, tfidf_matrix])

    def similar_products(self, product_id: str, k: int = 5) -> list[dict]:
        if not self.products or self._similarity_matrix is None:
            return []
        try:
            idx = self.product_ids.index(str(product_id))
        except ValueError:
            return []

        scores = self._similarity_matrix[idx]
        ranked = np.argsort(-scores)
        results = []
        for j in ranked:
            if j == idx:
                continue
            if len(results) >= k:
                break
            p = dict(self.products[j])
            p["similarity_score"] = round(float(scores[j]), 4)
            p["id"] = self.product_ids[j]
            results.append(p)
        return results

    def _content_recommendations(
        self,
        liked_product_ids: list[str],
        k: int,
        exclude_ids: set[str],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        if not liked_product_ids or self._knn is None or self.feature_matrix is None:
            return scores

        liked_indices = [
            self._id_to_index[pid] for pid in liked_product_ids if pid in self._id_to_index
        ]
        if not liked_indices:
            return scores

        profile = self.feature_matrix[liked_indices].mean(axis=0).reshape(1, -1)
        n_req = min(k + len(liked_indices) + 10, len(self.products))
        distances, indices = self._knn.kneighbors(profile, n_neighbors=n_req)

        for dist, idx in zip(distances[0], indices[0]):
            pid = self.product_ids[idx]
            if pid in exclude_ids:
                continue
            scores[pid] = max(scores.get(pid, 0.0), float(1 - dist))
        return scores

    def _cf_recommendations(
        self,
        liked_product_ids: list[str],
        k: int,
        exclude_ids: set[str],
    ) -> dict[str, float]:
        ranked = self._cf.recommend(liked_product_ids, k=k * 3, exclude_ids=exclude_ids)
        if not ranked:
            return {}
        max_s = max(s for _, s in ranked) or 1.0
        return {pid: score / max_s for pid, score in ranked}

    def _popular_fallback(self, k: int, exclude_ids: set[str]) -> list[dict]:
        sorted_products = sorted(
            self.products,
            key=lambda p: (p.get("rating", 0), p.get("review_count", 0)),
            reverse=True,
        )
        out = []
        for p in sorted_products:
            pid = _safe_id(p)
            if pid in exclude_ids:
                continue
            item = dict(p)
            item["id"] = pid
            item["similarity_score"] = round(float(p.get("rating", 0) / 5.0), 4)
            item["recommendation_reason"] = "Trending in our catalog (new visitor)"
            item["algorithm"] = "popular"
            out.append(item)
            if len(out) >= k:
                break
        return out

    def recommend_for_user(
        self,
        liked_product_ids: list[str],
        k: int = 8,
        exclude_ids: set[str] | None = None,
    ) -> list[dict]:
        if not self.products:
            return []

        exclude_ids = exclude_ids or set()
        liked_set = set(liked_product_ids)

        if not liked_set:
            return self._popular_fallback(k, exclude_ids | liked_set)

        content_scores = self._content_recommendations(liked_product_ids, k, exclude_ids | liked_set)
        cf_scores = self._cf_recommendations(liked_product_ids, k, exclude_ids | liked_set)

        all_ids = set(content_scores) | set(cf_scores)
        hybrid: list[tuple[str, float, str]] = []

        for pid in all_ids:
            c = content_scores.get(pid, 0.0)
            f = cf_scores.get(pid, 0.0)
            if c == 0 and f == 0:
                continue
            total = CONTENT_WEIGHT * c + CF_WEIGHT * f
            if f > 0.15 and c > 0.15:
                reason = "Hybrid: your taste + shoppers with similar likes"
                algo = "hybrid"
            elif f > c:
                reason = "People who liked similar items also liked this"
                algo = "collaborative"
            else:
                reason = "Matches your liked products (content similarity)"
                algo = "content"
            hybrid.append((pid, total, reason, algo, c, f))

        hybrid.sort(key=lambda x: (-x[1], -x[4], -x[5]))
        results = []
        category_count: dict[str, int] = {}

        for pid, total, reason, algo, c, f in hybrid:
            if pid in exclude_ids or pid in liked_set:
                continue
            idx = self._id_to_index.get(pid)
            if idx is None:
                continue
            cat = self.products[idx].get("category", "Other")
            if category_count.get(cat, 0) >= 3:
                continue

            p = dict(self.products[idx])
            p["id"] = pid
            p["similarity_score"] = round(total, 4)
            p["content_score"] = round(c, 4)
            p["cf_score"] = round(f, 4)
            p["recommendation_reason"] = reason
            p["algorithm"] = algo
            results.append(p)
            category_count[cat] = category_count.get(cat, 0) + 1
            if len(results) >= k:
                break

        return results

    def precision_at_k(
        self,
        user_likes: dict[str, list[str]],
        test_fraction: float = 0.2,
        k: int = 5,
        seed: int = 42,
    ) -> float:
        rng = np.random.default_rng(seed)
        hits = 0
        total = 0

        for _user_id, likes in user_likes.items():
            if len(likes) < 3:
                continue
            likes = list(likes)
            rng.shuffle(likes)
            n_test = max(1, int(len(likes) * test_fraction))
            test_set = set(likes[:n_test])
            train_set = likes[n_test:]

            recs = self.recommend_for_user(train_set, k=k, exclude_ids=set())
            rec_ids = {_safe_id(r) for r in recs}
            hits += len(rec_ids & test_set)
            total += min(k, len(test_set))

        return hits / total if total else 0.0
