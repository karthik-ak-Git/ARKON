"""ARKON Resource Manager - Resource Allocation Subsystem.

The resource manager is the OS-level resource allocation subsystem.
It owns resources, tracks usage, enforces limits, and provides health monitoring.
It does NOT execute work, schedule tasks, or know about domain-specific operations.
"""

from app.resources.interfaces import (
    AllocationStrategy,
    IAllocator,
    IResourceManager,
    IReservation,
    IResource,
    LimitScope,
    LimitType,
    ReservationStatus,
    ResourceHealth,
    ResourceStatus,
    ResourceType,
)
from app.resources.resource import Resource
from app.resources.reservation import Reservation
from app.resources.limits import ResourceLimit, ResourceQuota
from app.resources.allocator import ResourceAllocator
from app.resources.monitor import ResourceMonitor
from app.resources.health import ResourceHealthTracker
from app.resources.detector import ResourceDetector
from app.resources.quota import QuotaManager
from app.resources.providers import GPUProvider, ModelProvider, APIProvider, WorkspaceProvider
from app.resources.metrics import MetricsCollector
from app.resources.manager import ResourceManager

__all__ = [
    "AllocationStrategy",
    "IAllocator",
    "IResourceManager",
    "IReservation",
    "IResource",
    "LimitScope",
    "LimitType",
    "ReservationStatus",
    "ResourceHealth",
    "ResourceStatus",
    "ResourceType",
    "Resource",
    "Reservation",
    "ResourceLimit",
    "ResourceQuota",
    "ResourceAllocator",
    "ResourceMonitor",
    "ResourceHealthTracker",
    "ResourceDetector",
    "QuotaManager",
    "GPUProvider",
    "ModelProvider",
    "APIProvider",
    "WorkspaceProvider",
    "MetricsCollector",
    "ResourceManager",
]
