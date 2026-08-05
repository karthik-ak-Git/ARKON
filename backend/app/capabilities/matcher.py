"""ARKON Capability Registry - Matcher.

Matches providers against filter criteria.
Supports matching by capability, tags, workspace, hardware, priority, cost, latency, availability.
"""

from __future__ import annotations

from typing import Any

from app.capabilities.interfaces import IProvider, ProviderHealth


class ProviderMatcher:
    """Matches providers against filter criteria."""

    def match(
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
        **extra_filters: Any,
    ) -> list[IProvider]:
        """Filter providers by criteria.

        Args:
            providers: List of providers to filter.
            capability: Required capability name.
            tags: Required tags (provider must have ALL).
            workspace_id: Workspace scope filter.
            required_resources: Required resources (provider must have ALL).
            max_priority: Maximum priority value (inclusive).
            max_cost: Maximum cost per invocation (inclusive).
            max_latency: Maximum latency in ms (inclusive).
            require_healthy: Only return healthy/degraded providers.
            **extra_filters: Reserved for future use.

        Returns:
            Filtered list of providers.
        """
        result = list(providers)

        if capability is not None:
            result = [p for p in result if capability in p.get_capabilities()]

        if tags is not None:
            result = [
                p for p in result
                if all(t in p.get_tags() for t in tags)
            ]

        if workspace_id is not None:
            result = [
                p for p in result
                if p.get_workspace_scope() is None
                or p.get_workspace_scope() == workspace_id
            ]

        if required_resources is not None:
            result = [
                p for p in result
                if all(
                    p.get_required_resources().get(k) == v
                    for k, v in required_resources.items()
                )
            ]

        if max_priority is not None:
            result = [p for p in result if p.get_priority() <= max_priority]

        if max_cost is not None:
            result = [p for p in result if p.get_cost() <= max_cost]

        if max_latency is not None:
            result = [p for p in result if p.get_latency() <= max_latency]

        if require_healthy:
            result = [
                p for p in result
                if p.get_health() in {ProviderHealth.HEALTHY, ProviderHealth.DEGRADED}
            ]

        return result

    def match_any_capability(
        self,
        providers: list[IProvider],
        capabilities: list[str],
    ) -> list[IProvider]:
        """Match providers that have ANY of the given capabilities.

        Args:
            providers: List of providers to filter.
            capabilities: List of capability names (OR logic).

        Returns:
            Matching providers.
        """
        result = []
        seen_ids: set[str] = set()

        for provider in providers:
            pid = provider.get_id()
            if pid in seen_ids:
                continue
            provider_caps = set(provider.get_capabilities())
            if provider_caps & set(capabilities):
                result.append(provider)
                seen_ids.add(pid)

        return result

    def has_required_resources(
        self,
        provider: IProvider,
        required: dict[str, Any],
    ) -> bool:
        """Check if provider has all required resources.

        Args:
            provider: Provider to check.
            required: Required resource key-value pairs.

        Returns:
            True if provider has all required resources.
        """
        provider_resources = provider.get_required_resources()
        return all(
            provider_resources.get(k) == v
            for k, v in required.items()
        )
