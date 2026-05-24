"""Item–item collaborative filtering from like interactions."""

from __future__ import annotations

from collections import defaultdict

import numpy as np


class ItemCollaborativeFilter:
    """Users who liked A also liked B — co-like similarity between products."""

    def __init__(self):
        self._similar: dict[str, dict[str, float]] = {}

    def fit(self, interactions: list[dict]) -> None:
        user_likes: dict[str, set[str]] = defaultdict(set)
        for row in interactions:
            if row.get("type") != "like":
                continue
            uid = str(row.get("user_id", ""))
            pid = str(row.get("product_id", ""))
            if uid and pid:
                user_likes[uid].add(pid)

        co: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for liked in user_likes.values():
            items = list(liked)
            for i, a in enumerate(items):
                for b in items[i + 1 :]:
                    co[a][b] += 1.0
                    co[b][a] += 1.0

        self._similar = {}
        for a, neighbors in co.items():
            row_max = max(neighbors.values()) if neighbors else 1.0
            self._similar[a] = {
                b: count / row_max for b, count in neighbors.items()
            }

    def recommend(
        self,
        liked_product_ids: list[str],
        k: int = 20,
        exclude_ids: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        exclude_ids = exclude_ids or set()
        scores: dict[str, float] = defaultdict(float)

        for pid in liked_product_ids:
            for other_id, sim in self._similar.get(str(pid), {}).items():
                if other_id in exclude_ids or other_id in liked_product_ids:
                    continue
                scores[other_id] += sim

        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked[:k]
