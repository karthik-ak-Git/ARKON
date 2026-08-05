"""ARKON Capability Registry - Resolver.

Resolves capabilities to ranked providers.
Combines matching and ranking into a single resolution pipeline.
"""

from __future__ import annotations

from typing import Any

from app.capabilities.interfaces import IProvider, RankingStrategy
from app.capabilities.matcher import ProviderMatcher
from app.capabilities.ranking import ProviderRanker


class CapabilityResolver:
    """Resolves capabilities to ranked providers.

    Pipeline: match → rank → return.
    """

    def __init__(self) -> None:
        self._matcher = ProviderMatcher()
        self._ranker = ProviderRanker()

    def resolve(
        self,
        providers: list[IProvider],
        capability: str | None = None,
        tags: list[str] | None = None,
        workspace_id: str | None = None,
        required_resources: dict[str, Any] | None = None,
        max_priority: int | None = None,
        max_cost: float | None = None,
        max_latency: float | None = None,
        require_healthy: bool = True,
        ranking_strategy: RankingStrategy = RankingStrategy.WEIGHTED_COMPOSITE,
        ranking_weights: dict[str, float] | None = None,
    ) -> list[IProvider]:
        """Resolve providers for a capability.

        Args:
            providers: All available providers.
            capability: Required capability name.
            tags: Required tags.
            workspace_id: Workspace scope filter.
            required_resources: Required resources.
            max_priority: Maximum priority.
            max_cost: Maximum cost.
            max_latency: Maximum latency.
            require_healthy: Only return healthy providers.
            ranking_strategy: Ranking strategy.
            ranking_weights: Custom weights for weighted composite.

        Returns:
            Ranked list of matching providers.
        """
        # Step 1: Match
        matched = self._matcher.match(
            providers=providers,
            capability=capability,
            tags=tags,
            workspace_id=workspace_id,
            required_resources=required_resources,
            max_priority=max_priority,
            max_cost=max_cost,
            max_latency=max_latency,
            require_healthy=require_healthy,
        )

        # Step 2: Rank
        ranked = self._ranker.rank(
            providers=matched,
            strategy=ranking_strategy,
            weights=ranking_weights,
        )

        return ranked

    def resolve_any(
        self,
        providers: list[IProvider],
        capabilities: list[str],
        **kwargs: Any,
    ) -> list[IProvider]:
        """Resolve providers that have ANY of the given capabilities.

        Args:
            providers: All available providers.
            capabilities: List of capability names (OR logic).
            **kwargs: Additional filter/rank options.

        Returns:
            Ranked list of matching providers.
        """
        # Step 1: Match any capability
        matched = self._matcher.match_any_capability(providers, capabilities)

        # Step 2: Apply additional filters
        if kwargs.get("tags"):
            matched = [
                p for p in matched
                if all(t in p.get_tags() for t in kwargs["tags"])
            ]

        if kwargs.get("require_healthy", True):
            from app.capabilities.interfaces import ProviderHealth
            matched = [
                p for p in matched
                if p.get_health() in {ProviderHealth.HEALTHY, ProviderHealth.DEGRADED}
            ]

        # Step 3: Rank
        strategy = kwargs.get("ranking_strategy", RankingStrategy.WEIGHTED_COMPOSITE)
        weights = kwargs.get("ranking_weights")

        return self._ranker.rank(matched, strategy, weights)
