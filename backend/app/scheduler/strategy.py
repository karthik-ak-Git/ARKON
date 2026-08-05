"""Load balancing strategies - determines WHERE to dispatch."""

from __future__ import annotations

import abc
import random
from dataclasses import dataclass, field

from app.scheduler.interfaces import LoadBalancingStrategy


@dataclass
class Target:
    """An execution target (worker, node, etc.)."""

    target_id: str
    load: float = 0.0
    capacity: float = 1.0
    weight: float = 1.0
    active_tasks: int = 0
    capabilities: set[str] = field(default_factory=set)
    healthy: bool = True

    @property
    def available_capacity(self) -> float:
        return max(0.0, self.capacity - self.load)

    @property
    def utilization(self) -> float:
        return self.load / self.capacity if self.capacity > 0 else 0.0


class LoadBalancer(abc.ABC):
    """Base load balancer."""

    @property
    @abc.abstractmethod
    def strategy_type(self) -> LoadBalancingStrategy:
        ...

    @abc.abstractmethod
    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        ...


class LeastLoadedBalancer(LoadBalancer):
    """Select target with least load."""

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.LEAST_LOADED

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = self._filter(targets, required_capabilities)
        if not candidates:
            return None
        return min(candidates, key=lambda t: t.load)

    def _filter(self, targets: list[Target], required: set[str] | None) -> list[Target]:
        result = [t for t in targets if t.healthy]
        if required:
            result = [t for t in result if required.issubset(t.capabilities)]
        return result


class LeastBusyBalancer(LoadBalancer):
    """Select target with fewest active tasks."""

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.LEAST_BUSY

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = [t for t in targets if t.healthy]
        if required_capabilities:
            candidates = [t for t in candidates if required_capabilities.issubset(t.capabilities)]
        if not candidates:
            return None
        return min(candidates, key=lambda t: t.active_tasks)


class RandomBalancer(LoadBalancer):
    """Select a random healthy target."""

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.RANDOM

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = [t for t in targets if t.healthy]
        if required_capabilities:
            candidates = [t for t in candidates if required_capabilities.issubset(t.capabilities)]
        if not candidates:
            return None
        return random.choice(candidates)


class RoundRobinBalancer(LoadBalancer):
    """Round-robin target selection."""

    def __init__(self) -> None:
        self._index = 0

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.ROUND_ROBIN

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = [t for t in targets if t.healthy]
        if required_capabilities:
            candidates = [t for t in candidates if required_capabilities.issubset(t.capabilities)]
        if not candidates:
            return None
        idx = self._index % len(candidates)
        self._index += 1
        return candidates[idx]


class WeightedBalancer(LoadBalancer):
    """Weighted random selection based on available capacity."""

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.WEIGHTED

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = [t for t in targets if t.healthy]
        if required_capabilities:
            candidates = [t for t in candidates if required_capabilities.issubset(t.capabilities)]
        if not candidates:
            return None
        weights = [t.weight * t.available_capacity for t in candidates]
        total = sum(weights)
        if total <= 0:
            return candidates[0]
        r = random.uniform(0, total)
        cumulative = 0.0
        for t, w in zip(candidates, weights):
            cumulative += w
            if r <= cumulative:
                return t
        return candidates[-1]


class CapabilityScoreBalancer(LoadBalancer):
    """Select based on capability match score."""

    @property
    def strategy_type(self) -> LoadBalancingStrategy:
        return LoadBalancingStrategy.CAPABILITY_SCORE

    def select(self, targets: list[Target], required_capabilities: set[str] | None = None) -> Target | None:
        candidates = [t for t in targets if t.healthy]
        if not candidates:
            return None

        def score(t: Target) -> float:
            if required_capabilities:
                overlap = len(required_capabilities & t.capabilities)
                total = len(required)
                match_score = overlap / total if total > 0 else 0.0
            else:
                match_score = 1.0
            return match_score * t.available_capacity * t.weight

        return max(candidates, key=score)


BALANCER_MAP: dict[LoadBalancingStrategy, type[LoadBalancer]] = {
    LoadBalancingStrategy.LEAST_LOADED: LeastLoadedBalancer,
    LoadBalancingStrategy.LEAST_BUSY: LeastBusyBalancer,
    LoadBalancingStrategy.RANDOM: RandomBalancer,
    LoadBalancingStrategy.ROUND_ROBIN: RoundRobinBalancer,
    LoadBalancingStrategy.WEIGHTED: WeightedBalancer,
    LoadBalancingStrategy.CAPABILITY_SCORE: CapabilityScoreBalancer,
}


def create_balancer(strategy: LoadBalancingStrategy) -> LoadBalancer:
    cls = BALANCER_MAP.get(strategy)
    if cls is None:
        raise ValueError(f"Unknown strategy: {strategy}")
    return cls()
