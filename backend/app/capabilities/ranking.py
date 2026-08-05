"""ARKON Capability Registry - Ranking.

Provides multiple ranking strategies for providers.
Strategy is configurable per resolution request.
"""

from __future__ import annotations

from typing import Any

from app.capabilities.interfaces import IProvider, ProviderHealth, RankingStrategy


class ProviderRanker:
    """Ranks providers using configurable strategies."""

    def rank(
        self,
        providers: list[IProvider],
        strategy: RankingStrategy = RankingStrategy.WEIGHTED_COMPOSITE,
        weights: dict[str, float] | None = None,
    ) -> list[IProvider]:
        """Rank providers using the specified strategy.

        Args:
            providers: Providers to rank.
            strategy: Ranking strategy to use.
            weights: Custom weights for WEIGHTED_COMPOSITE strategy.
                Keys: priority, cost, latency, health.
                Defaults: priority=0.3, cost=0.3, latency=0.2, health=0.2.

        Returns:
            Providers sorted by rank (best first).
        """
        if not providers:
            return []

        if strategy == RankingStrategy.HIGHEST_PRIORITY:
            return self._rank_by_priority(providers)
        elif strategy == RankingStrategy.LOWEST_COST:
            return self._rank_by_cost(providers)
        elif strategy == RankingStrategy.FASTEST:
            return self._rank_by_latency(providers)
        elif strategy == RankingStrategy.LOCAL_FIRST:
            return self._rank_by_local_first(providers)
        elif strategy == RankingStrategy.HEALTHY_FIRST:
            return self._rank_by_health(providers)
        elif strategy == RankingStrategy.WEIGHTED_COMPOSITE:
            return self._rank_composite(providers, weights)
        else:
            return list(providers)

    def _rank_by_priority(self, providers: list[IProvider]) -> list[IProvider]:
        """Sort by priority (lower value = higher priority)."""
        return sorted(providers, key=lambda p: p.get_priority())

    def _rank_by_cost(self, providers: list[IProvider]) -> list[IProvider]:
        """Sort by cost (lower cost first)."""
        return sorted(providers, key=lambda p: p.get_cost())

    def _rank_by_latency(self, providers: list[IProvider]) -> list[IProvider]:
        """Sort by latency (lower latency first)."""
        return sorted(providers, key=lambda p: p.get_latency())

    def _rank_by_local_first(self, providers: list[IProvider]) -> list[IProvider]:
        """Sort by workspace scope (local before global)."""
        def sort_key(p: IProvider) -> tuple[int, int]:
            is_local = 0 if p.get_workspace_scope() is not None else 1
            return (is_local, p.get_priority())
        return sorted(providers, key=sort_key)

    def _rank_by_health(self, providers: list[IProvider]) -> list[IProvider]:
        """Sort by health (healthy first, then degraded, then unknown)."""
        health_order = {
            ProviderHealth.HEALTHY: 0,
            ProviderHealth.DEGRADED: 1,
            ProviderHealth.UNKNOWN: 2,
            ProviderHealth.UNHEALTHY: 3,
            ProviderHealth.UNAVAILABLE: 4,
        }
        return sorted(
            providers,
            key=lambda p: (health_order.get(p.get_health(), 5), p.get_priority()),
        )

    def _rank_composite(
        self,
        providers: list[IProvider],
        weights: dict[str, float] | None = None,
    ) -> list[IProvider]:
        """Rank using weighted composite score.

        Lower score = better provider.
        """
        w = weights or {}
        w_priority = w.get("priority", 0.3)
        w_cost = w.get("cost", 0.3)
        w_latency = w.get("latency", 0.2)
        w_health = w.get("health", 0.2)

        health_scores = {
            ProviderHealth.HEALTHY: 0.0,
            ProviderHealth.DEGRADED: 0.3,
            ProviderHealth.UNKNOWN: 0.5,
            ProviderHealth.UNHEALTHY: 0.8,
            ProviderHealth.UNAVAILABLE: 1.0,
        }

        # Normalize values to 0-1 range
        max_priority = max((p.get_priority() for p in providers), default=1) or 1
        max_cost = max((p.get_cost() for p in providers), default=1) or 1
        max_latency = max((p.get_latency() for p in providers), default=1) or 1

        def score(p: IProvider) -> float:
            norm_priority = p.get_priority() / max_priority
            norm_cost = p.get_cost() / max_cost
            norm_latency = p.get_latency() / max_latency
            norm_health = health_scores.get(p.get_health(), 0.5)

            return (
                w_priority * norm_priority
                + w_cost * norm_cost
                + w_latency * norm_latency
                + w_health * norm_health
            )

        return sorted(providers, key=score)
