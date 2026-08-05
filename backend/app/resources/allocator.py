"""ARKON Resource Manager - Allocator.

Resource allocation engine implementing multiple strategies.
"""

from __future__ import annotations

import random
from typing import Any

import structlog

from app.resources.interfaces import AllocationStrategy, ResourceHealth, ResourceType
from app.resources.resource import Resource
from app.resources.exceptions import AllocationError, NoResourceAvailableError

logger = structlog.get_logger(__name__)


class ResourceAllocator:
    """Implements allocation strategies for distributing resources.

    Each strategy selects the best resource for a given request.
    """

    def allocate(
        self,
        resources: list[Resource],
        amount: float,
        resource_type: ResourceType,
        strategy: AllocationStrategy,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Allocate `amount` from resources using the given strategy.

        Returns the selected Resource with `amount` deducted from available.
        Raises NoResourceAvailableError if no suitable resource found.
        """
        candidates = self._filter_candidates(resources, resource_type, amount, tags)
        if not candidates:
            raise NoResourceAvailableError(
                resource_type=resource_type.value,
                amount=amount,
            )

        selected = self._select(candidates, strategy)

        # Perform allocation
        selected.available -= amount
        selected.allocated += amount
        selected.update_status()

        logger.debug(
            "resource_allocated",
            resource_id=selected.resource_id,
            amount=amount,
            strategy=strategy.value,
            available=selected.available,
        )
        return selected

    def _filter_candidates(
        self,
        resources: list[Resource],
        resource_type: ResourceType,
        amount: float,
        tags: list[str] | None,
    ) -> list[Resource]:
        """Filter resources that can satisfy the allocation request."""
        candidates = []
        for r in resources:
            if r.resource_type != resource_type:
                continue
            if r.available < amount:
                continue
            if r.health in (ResourceHealth.UNAVAILABLE, ResourceHealth.MAINTENANCE):
                continue
            if tags and not all(t in r.tags for t in tags):
                continue
            candidates.append(r)
        return candidates

    def _select(
        self,
        candidates: list[Resource],
        strategy: AllocationStrategy,
    ) -> Resource:
        """Select a resource using the given strategy."""
        if strategy == AllocationStrategy.BEST_FIT:
            return self._best_fit(candidates)
        elif strategy == AllocationStrategy.FIRST_FIT:
            return self._first_fit(candidates)
        elif strategy == AllocationStrategy.BALANCED:
            return self._balanced(candidates)
        elif strategy == AllocationStrategy.PRIORITY:
            return self._priority(candidates)
        elif strategy == AllocationStrategy.LEAST_LOADED:
            return self._least_loaded(candidates)
        elif strategy == AllocationStrategy.WEIGHTED:
            return self._weighted(candidates)
        else:
            return candidates[0]

    def _best_fit(self, candidates: list[Resource]) -> Resource:
        """Select the resource with the smallest available capacity that fits.

        Minimizes wasted resources.
        """
        return min(candidates, key=lambda r: r.available)

    def _first_fit(self, candidates: list[Resource]) -> Resource:
        """Select the first resource that fits.

        Fastest strategy, may lead to fragmentation.
        """
        return candidates[0]

    def _balanced(self, candidates: list[Resource]) -> Resource:
        """Select the resource closest to 50% utilization.

        Distributes load evenly across all resources.
        """
        return min(candidates, key=lambda r: abs(r.utilization - 0.5))

    def _priority(self, candidates: list[Resource]) -> Resource:
        """Select the highest-priority resource.

        If tied, falls back to best-fit.
        """
        max_priority = max(r.priority for r in candidates)
        top = [r for r in candidates if r.priority == max_priority]
        if len(top) == 1:
            return top[0]
        return self._best_fit(top)

    def _least_loaded(self, candidates: list[Resource]) -> Resource:
        """Select the resource with the least allocated capacity."""
        return min(candidates, key=lambda r: r.allocated)

    def _weighted(self, candidates: list[Resource]) -> Resource:
        """Select a resource weighted by available capacity.

        Resources with more available capacity are more likely to be selected.
        """
        total = sum(r.available for r in candidates)
        if total <= 0:
            return candidates[0]

        r = random.random() * total
        cumulative = 0.0
        for resource in candidates:
            cumulative += resource.available
            if r <= cumulative:
                return resource
        return candidates[-1]

    def to_dict(self) -> dict[str, Any]:
        return {"strategy": "resource_allocator"}
