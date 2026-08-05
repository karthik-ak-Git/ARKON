"""ARKON Resource Manager - Specialized Providers.

Domain-specific resource providers for GPU, Model, API, and Workspace resources.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.resources.interfaces import ResourceHealth, ResourceType
from app.resources.resource import Resource

logger = structlog.get_logger(__name__)


class GPUProvider:
    """Manages GPU and VRAM resources."""

    def __init__(self) -> None:
        self._gpus: list[Resource] = []

    def register_gpu(
        self,
        name: str,
        total_vram_mb: float,
        free_vram_mb: float | None = None,
        device_index: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Register a GPU resource."""
        resource = Resource(
            name=name,
            resource_type=ResourceType.GPU,
            capacity=total_vram_mb,
            available=free_vram_mb or total_vram_mb,
            health=ResourceHealth.HEALTHY,
            metadata={
                "gpu_name": name,
                "total_vram_mb": total_vram_mb,
                "device_index": device_index,
                **(metadata or {}),
            },
            tags=["gpu", "cuda", "compute"],
        )
        self._gpus.append(resource)
        return resource

    def get_vram_usage(self) -> dict[str, Any]:
        """Get VRAM usage across all GPUs."""
        total = sum(g.capacity for g in self._gpus)
        available = sum(g.available for g in self._gpus)
        return {
            "total_vram_mb": total,
            "available_vram_mb": available,
            "used_vram_mb": total - available,
            "gpu_count": len(self._gpus),
        }

    def get_all(self) -> list[Resource]:
        return list(self._gpus)

    def clear(self) -> None:
        self._gpus.clear()


class ModelProvider:
    """Manages AI model resources (concurrency, rate limits, slots)."""

    def __init__(self) -> None:
        self._models: dict[str, Resource] = {}

    def register_model(
        self,
        model_id: str,
        max_concurrent: int = 1,
        rate_limit: float = 0.0,  # requests per second
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Register a model resource."""
        resource = Resource(
            name=model_id,
            resource_type=ResourceType.MODEL_SLOT,
            capacity=float(max_concurrent),
            available=float(max_concurrent),
            health=ResourceHealth.HEALTHY,
            metadata={
                "model_id": model_id,
                "max_concurrent": max_concurrent,
                "rate_limit_rps": rate_limit,
                **(metadata or {}),
            },
            tags=["model", "ai"],
        )
        self._models[model_id] = resource
        return resource

    def get_model(self, model_id: str) -> Resource | None:
        return self._models.get(model_id)

    def get_all(self) -> list[Resource]:
        return list(self._models.values())

    def clear(self) -> None:
        self._models.clear()


class APIProvider:
    """Manages API resource limits (rate limits, token budgets, quotas)."""

    def __init__(self) -> None:
        self._apis: dict[str, Resource] = {}

    def register_api(
        self,
        api_id: str,
        rate_limit: float = 100.0,  # requests per minute
        token_budget: float = 1_000_000.0,
        max_concurrent: int = 10,
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Register an API resource."""
        resource = Resource(
            name=api_id,
            resource_type=ResourceType.API_TOKEN,
            capacity=rate_limit,
            available=rate_limit,
            health=ResourceHealth.HEALTHY,
            metadata={
                "api_id": api_id,
                "rate_limit_rpm": rate_limit,
                "token_budget": token_budget,
                "max_concurrent": max_concurrent,
                **(metadata or {}),
            },
            tags=["api", "rate-limit"],
        )
        self._apis[api_id] = resource
        return resource

    def get_api(self, api_id: str) -> Resource | None:
        return self._apis.get(api_id)

    def get_all(self) -> list[Resource]:
        return list(self._apis.values())

    def clear(self) -> None:
        self._apis.clear()


class WorkspaceProvider:
    """Manages workspace-level resources."""

    def __init__(self) -> None:
        self._workspaces: dict[str, Resource] = {}

    def register_workspace(
        self,
        workspace_id: str,
        max_agents: int = 10,
        max_tasks: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Register a workspace resource."""
        resource = Resource(
            name=workspace_id,
            resource_type=ResourceType.WORKSPACE_RESOURCE,
            capacity=float(max_agents),
            available=float(max_agents),
            health=ResourceHealth.HEALTHY,
            metadata={
                "workspace_id": workspace_id,
                "max_agents": max_agents,
                "max_tasks": max_tasks,
                **(metadata or {}),
            },
            tags=["workspace"],
        )
        self._workspaces[workspace_id] = resource
        return resource

    def get_workspace(self, workspace_id: str) -> Resource | None:
        return self._workspaces.get(workspace_id)

    def get_all(self) -> list[Resource]:
        return list(self._workspaces.values())

    def clear(self) -> None:
        self._workspaces.clear()
