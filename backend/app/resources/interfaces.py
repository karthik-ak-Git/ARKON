"""ARKON Resource Manager - Interfaces.

Defines the contracts for all resource manager components.
The Resource Manager is the operating system's resource allocation subsystem.
It owns resources. It never executes work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


# =============================================================================
# Resource Types
# =============================================================================


class ResourceType(str, Enum):
    """Types of computational resources."""

    CPU = "cpu"
    RAM = "ram"
    GPU = "gpu"
    VRAM = "vram"
    DISK = "disk"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    API_TOKEN = "api_token"
    MODEL_SLOT = "model_slot"
    WORKER_SLOT = "worker_slot"
    PLUGIN_RESOURCE = "plugin_resource"
    WORKSPACE_RESOURCE = "workspace_resource"


# =============================================================================
# Resource Health
# =============================================================================


class ResourceHealth(str, Enum):
    """Resource health states."""

    HEALTHY = "healthy"
    BUSY = "busy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


# =============================================================================
# Resource Status
# =============================================================================


class ResourceStatus(str, Enum):
    """Resource allocation status."""

    FREE = "free"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    EXHAUSTED = "exhausted"
    OFFLINE = "offline"


# =============================================================================
# Reservation Status
# =============================================================================


class ReservationStatus(str, Enum):
    """Reservation lifecycle states."""

    PENDING = "pending"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


# =============================================================================
# Allocation Strategy
# =============================================================================


class AllocationStrategy(str, Enum):
    """Resource allocation strategies."""

    BEST_FIT = "best_fit"
    FIRST_FIT = "first_fit"
    BALANCED = "balanced"
    PRIORITY = "priority"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"


# =============================================================================
# Limit Scope
# =============================================================================


class LimitScope(str, Enum):
    """Scope for resource limits."""

    WORKSPACE = "workspace"
    AGENT = "agent"
    PLUGIN = "plugin"
    TASK = "task"
    USER = "user"
    MODEL = "model"
    GLOBAL = "global"


# =============================================================================
# Limit Type
# =============================================================================


class LimitType(str, Enum):
    """Type of resource limit."""

    HARD = "hard"
    SOFT = "soft"


# =============================================================================
# IResource
# =============================================================================


class IResource(ABC):
    """Interface for a resource."""

    @abstractmethod
    def get_id(self) -> str:
        """Get resource ID."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get resource name."""
        ...

    @abstractmethod
    def get_type(self) -> ResourceType:
        """Get resource type."""
        ...

    @abstractmethod
    def get_capacity(self) -> float:
        """Get total capacity."""
        ...

    @abstractmethod
    def get_available(self) -> float:
        """Get currently available amount."""
        ...

    @abstractmethod
    def get_reserved(self) -> float:
        """Get reserved amount."""
        ...

    @abstractmethod
    def get_allocated(self) -> float:
        """Get allocated amount."""
        ...

    @abstractmethod
    def get_health(self) -> ResourceHealth:
        """Get health status."""
        ...

    @abstractmethod
    def get_status(self) -> ResourceStatus:
        """Get allocation status."""
        ...

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Get resource metadata."""
        ...

    @abstractmethod
    def get_tags(self) -> list[str]:
        """Get resource tags."""
        ...

    @abstractmethod
    def get_priority(self) -> int:
        """Get resource priority."""
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# IReservation
# =============================================================================


class IReservation(ABC):
    """Interface for a resource reservation."""

    @abstractmethod
    def get_id(self) -> str:
        """Get reservation ID."""
        ...

    @abstractmethod
    def get_resource_id(self) -> str:
        """Get resource ID."""
        ...

    @abstractmethod
    def get_amount(self) -> float:
        """Get reserved amount."""
        ...

    @abstractmethod
    def get_status(self) -> ReservationStatus:
        """Get reservation status."""
        ...

    @abstractmethod
    def get_owner(self) -> str:
        """Get reservation owner (workspace/agent/task ID)."""
        ...

    @abstractmethod
    def get_expires_at(self) -> float | None:
        """Get expiration timestamp."""
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# IAllocator
# =============================================================================


class IAllocator(ABC):
    """Interface for resource allocation strategies."""

    @abstractmethod
    def allocate(
        self,
        resources: list[IResource],
        amount: float,
        strategy: AllocationStrategy = AllocationStrategy.BEST_FIT,
        **kwargs: Any,
    ) -> IResource | None:
        """Find and allocate a resource.

        Args:
            resources: Available resources.
            amount: Amount needed.
            strategy: Allocation strategy.
            **kwargs: Additional constraints.

        Returns:
            Allocated resource or None.
        """
        ...

    @abstractmethod
    def can_allocate(
        self,
        resource: IResource,
        amount: float,
    ) -> bool:
        """Check if a resource can satisfy the request.

        Args:
            resource: Resource to check.
            amount: Amount needed.

        Returns:
            True if allocation is possible.
        """
        ...


# =============================================================================
# IResourceManager
# =============================================================================


class IResourceManager(ABC):
    """Interface for the resource manager.

    The resource manager discovers, monitors, reserves, allocates,
    and releases computational resources.
    """

    @abstractmethod
    async def discover_resources(self) -> list[IResource]:
        """Discover all available resources."""
        ...

    @abstractmethod
    async def register_resource(self, resource: IResource) -> None:
        """Register a resource."""
        ...

    @abstractmethod
    async def unregister_resource(self, resource_id: str) -> None:
        """Unregister a resource."""
        ...

    @abstractmethod
    async def get_resource(self, resource_id: str) -> IResource | None:
        """Get a resource by ID."""
        ...

    @abstractmethod
    async def list_resources(
        self,
        resource_type: ResourceType | None = None,
        tags: list[str] | None = None,
    ) -> list[IResource]:
        """List resources, optionally filtered."""
        ...

    @abstractmethod
    async def reserve(
        self,
        resource_id: str,
        amount: float,
        owner: str,
        ttl: float | None = None,
    ) -> IReservation:
        """Reserve resources."""
        ...

    @abstractmethod
    async def commit_reservation(self, reservation_id: str) -> None:
        """Commit a reservation (convert to allocation)."""
        ...

    @abstractmethod
    async def release_reservation(self, reservation_id: str) -> None:
        """Release a reservation."""
        ...

    @abstractmethod
    async def allocate(
        self,
        resource_type: ResourceType,
        amount: float,
        owner: str,
        strategy: AllocationStrategy = AllocationStrategy.BEST_FIT,
        **kwargs: Any,
    ) -> IReservation:
        """Allocate resources using a strategy."""
        ...

    @abstractmethod
    async def release(self, reservation_id: str) -> None:
        """Release allocated resources."""
        ...

    @abstractmethod
    async def get_utilization(self, resource_id: str | None = None) -> dict[str, Any]:
        """Get resource utilization metrics."""
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check health of all resources."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the resource manager."""
        ...
