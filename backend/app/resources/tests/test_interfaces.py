"""Tests for Resource Manager - Interfaces and Exceptions."""

import pytest
from app.resources.interfaces import (
    AllocationStrategy,
    IAllocator,
    IReservation,
    IResource,
    IResourceManager,
    LimitScope,
    LimitType,
    ReservationStatus,
    ResourceHealth,
    ResourceStatus,
    ResourceType,
)
from app.resources.exceptions import (
    ResourceError,
    ResourceNotFoundError,
    ResourceExhaustedError,
    ResourceUnavailableError,
    AllocationError,
    NoResourceAvailableError,
    ReservationNotFoundError,
    ReservationExpiredError,
    ReservationConflictError,
    QuotaExceededError,
    LimitExceededError,
)


class TestResourceTypes:
    def test_resource_type_values(self):
        assert ResourceType.CPU.value == "cpu"
        assert ResourceType.RAM.value == "ram"
        assert ResourceType.GPU.value == "gpu"
        assert ResourceType.VRAM.value == "vram"
        assert ResourceType.DISK.value == "disk"
        assert ResourceType.NETWORK.value == "network"
        assert ResourceType.FILESYSTEM.value == "filesystem"
        assert ResourceType.API_TOKEN.value == "api_token"
        assert ResourceType.MODEL_SLOT.value == "model_slot"
        assert ResourceType.WORKER_SLOT.value == "worker_slot"
        assert ResourceType.PLUGIN_RESOURCE.value == "plugin_resource"
        assert ResourceType.WORKSPACE_RESOURCE.value == "workspace_resource"

    def test_resource_type_count(self):
        assert len(ResourceType) == 12


class TestResourceHealth:
    def test_health_states(self):
        assert ResourceHealth.HEALTHY.value == "healthy"
        assert ResourceHealth.BUSY.value == "busy"
        assert ResourceHealth.DEGRADED.value == "degraded"
        assert ResourceHealth.UNAVAILABLE.value == "unavailable"
        assert ResourceHealth.MAINTENANCE.value == "maintenance"
        assert ResourceHealth.UNKNOWN.value == "unknown"


class TestAllocationStrategy:
    def test_strategies(self):
        assert AllocationStrategy.BEST_FIT.value == "best_fit"
        assert AllocationStrategy.FIRST_FIT.value == "first_fit"
        assert AllocationStrategy.BALANCED.value == "balanced"
        assert AllocationStrategy.PRIORITY.value == "priority"
        assert AllocationStrategy.LEAST_LOADED.value == "least_loaded"
        assert AllocationStrategy.WEIGHTED.value == "weighted"


class TestExceptions:
    def test_resource_not_found(self):
        e = ResourceNotFoundError("res-123")
        assert e.resource_id == "res-123"
        assert issubclass(ResourceNotFoundError, ResourceError)

    def test_resource_exhausted(self):
        e = ResourceExhaustedError("res-123", requested=5.0, available=2.0)
        assert e.available == 2.0
        assert e.requested == 5.0

    def test_reservation_expired(self):
        e = ReservationExpiredError("res-456")
        assert e.reservation_id == "res-456"
        assert issubclass(ReservationExpiredError, ResourceError)

    def test_quota_exceeded(self):
        e = QuotaExceededError("workspace:ws1", "gpu", 100.0, 80.0)
        assert e.used == 100.0
        assert e.limit == 80.0
        assert issubclass(QuotaExceededError, ResourceError)

    def test_allocation_error(self):
        e = AllocationError()
        assert issubclass(AllocationError, ResourceError)

    def test_limit_exceeded(self):
        e = LimitExceededError("workspace:ws1", "gpu", 100.0, 80.0)
        assert e.requested == 100.0
        assert e.limit == 80.0
        assert issubclass(LimitExceededError, ResourceError)
