"""
Recommendation engine: feature vectors + cosine similarity + KNN.

LEARNING NOTES:
---------------
1. Each product becomes a numeric vector (features).
2. Cosine similarity = dot(a,b) / (||a|| * ||b||)  →  range [-1, 1], often [0, 1] for positive features.
3. KNN finds k products whose vectors are closest to a query vector (user profile or a product).
4. Feature engineering improves separability → better Precision@K (your "25%" story).
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

# Categories in seed data — keep in sync with seed_data.py
CATEGORIES = [
    "Electronics",
    "Books",
    "Home",
    "Sports",
    "Fashion",
    "Beauty",
]


def _safe_id(product: dict) -> str:
    return str(product.get("_id", product.get("id", "")))


class ProductRecommender:
    def __init__(self, use_engineered_features: bool = True):
        self.use_engineered_features = use_engineered_features
        self.products: list[dict] = []
        self.product_ids: list[str] = []
        self.feature_matrix: np.ndarray | None = None
        self._similarity_matrix: np.ndarray | None = None
        self._knn: NearestNeighbors | None = None
        self._tfidf: TfidfVectorizer | None = None
        self._category_index = {c: i for i, c in enumerate(CATEGORIES)}

    def fit(self, products: list[dict]) -> None:
        """Build feature matrix and fit KNN on product vectors."""
        self.products = products
        self.product_ids = [_safe_id(p) for p in products]
        self.feature_matrix = self._build_feature_matrix(products)
        self._similarity_matrix = cosine_similarity(self.feature_matrix)

        # KNN in cosine space: sklearn uses distance = 1 - cosine_similarity for metric='cosine'
        self._knn = NearestNeighbors(n_neighbors=min(10, len(products)), metric="cosine")
        self._knn.fit(self.feature_matrix)

    def _build_feature_matrix(self, products: list[dict]) -> np.ndarray:
        n = len(products)
        if n == 0:
            return np.zeros((0, 1))

        if not self.use_engineered_features:
            # Baseline: raw price + rating only (weak signal)
            return np.array(
                [[p.get("price", 0), p.get("rating", 0)] for p in products],
                dtype=float,
            )

        # --- Engineered features ---
        prices = np.array([p.get("price", 1) for p in products], dtype=float)
        ratings = np.array([p.get("rating", 3) for p in products], dtype=float)
        reviews = np.array([p.get("review_count", 0) for p in products], dtype=float)

        # Log price: reduces skew ($10 vs $1000)
        log_price = np.log1p(prices).reshape(-1, 1)
        # Normalize to 0-1 for fair weight vs other features
        log_price_norm = (log_price - log_price.min()) / (log_price.max() - log_price.min() + 1e-9)

        rating_norm = (ratings / 5.0).reshape(-1, 1)
        review_signal = (np.log1p(reviews) / (np.log1p(reviews).max() + 1e-9)).reshape(-1, 1)

        # One-hot category
        cat_matrix = np.zeros((n, len(CATEGORIES)))
        for i, p in enumerate(products):
            cat = p.get("category", "")
            if cat in self._category_index:
                cat_matrix[i, self._category_index[cat]] = 1.0

        # TF-IDF on name + description (captures "wireless headphones" vs "cookbook")
        texts = [
            f"{p.get('name', '')} {p.get('description', '')}".lower()
            for p in products
        ]
        self._tfidf = TfidfVectorizer(max_features=32, stop_words="english")
        tfidf_matrix = self._tfidf.fit_transform(texts).toarray()

        return np.hstack([log_price_norm, rating_norm, review_signal, cat_matrix, tfidf_matrix])

    def similar_products(self, product_id: str, k: int = 5) -> list[dict]:
        """Content-based: products most similar to given product (cosine)."""
        if not self.products or self._similarity_matrix is None:
            return []

        try:
            idx = self.product_ids.index(str(product_id))
        except ValueError:
            return []

        scores = self._similarity_matrix[idx]
        # Exclude self, take top k
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

    def recommend_for_user(
        self,
        liked_product_ids: list[str],
        k: int = 8,
        exclude_ids: set[str] | None = None,
    ) -> list[dict]:
        """
        Collaborative-ish profile: average feature vectors of liked products,
        then KNN to find nearest products user hasn't seen.
        """
        if not self.products or self._knn is None or self.feature_matrix is None:
            return []

        exclude_ids = exclude_ids or set()
        liked_indices = [
            i for i, pid in enumerate(self.product_ids) if pid in liked_product_ids
        ]

        if not liked_indices:
            # Cold start: popular items
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
                item["recommendation_reason"] = "Popular pick (new user)"
                out.append(item)
                if len(out) >= k:
                    break
            return out

        profile = self.feature_matrix[liked_indices].mean(axis=0).reshape(1, -1)
        distances, indices = self._knn.kneighbors(profile, n_neighbors=min(k + len(liked_indices) + 5, len(self.products)))

        results = []
        seen = set(liked_product_ids) | exclude_ids
        for dist, idx in zip(distances[0], indices[0]):
            pid = self.product_ids[idx]
            if pid in seen:
                continue
            p = dict(self.products[idx])
            p["id"] = pid
            # Convert cosine distance to similarity for UI
            p["similarity_score"] = round(float(1 - dist), 4)
            p["recommendation_reason"] = "Based on products you liked (KNN + cosine)"
            results.append(p)
            seen.add(pid)
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
        """Offline metric for evaluate_model.py — hide some likes, predict, measure hits."""
        rng = np.random.default_rng(seed)
        hits = 0
        total = 0

        for user_id, likes in user_likes.items():
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
