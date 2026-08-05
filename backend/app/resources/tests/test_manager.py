"""Tests for Resource Manager - Main ResourceManager."""

import pytest
from app.resources.manager import ResourceManager
from app.resources.resource import Resource
from app.resources.interfaces import (
    AllocationStrategy,
    LimitScope,
    LimitType,
    ResourceHealth,
    ResourceType,
    ReservationStatus,
)
from app.resources.exceptions import (
    ResourceNotFoundError,
    ResourceExhaustedError,
    NoResourceAvailableError,
    ReservationNotFoundError,
    ReservationExpiredError,
    AllocationError,
    QuotaExceededError,
)


class TestResourceManagerInit:
    def test_initialize(self):
        rm = ResourceManager()
        rm.initialize()
        assert rm._initialized is True

    def test_shutdown(self):
        rm = ResourceManager()
        rm.initialize()
        rm.shutdown()
        assert rm._initialized is False


class TestResourceRegistration:
    def test_register_and_get(self):
        rm = ResourceManager()
        r = Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0)
        rm.register_resource(r)
        assert rm.get_resource(r.resource_id) is r

    def test_list_resources(self):
        rm = ResourceManager()
        rm.register_resource(Resource(name="cpu-1", resource_type=ResourceType.CPU))
        rm.register_resource(Resource(name="gpu-1", resource_type=ResourceType.GPU))
        assert len(rm.list_resources()) == 2
        assert len(rm.list_resources(ResourceType.CPU)) == 1

    def test_unregister(self):
        rm = ResourceManager()
        r = Resource(name="cpu-1", resource_type=ResourceType.CPU)
        rm.register_resource(r)
        assert rm.unregister_resource(r.resource_id) is True
        assert rm.get_resource(r.resource_id) is None


class TestAllocation:
    def test_allocate_best_fit(self):
        rm = ResourceManager()
        rm.register_resource(Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=6.0))
        rm.register_resource(Resource(name="cpu-2", resource_type=ResourceType.CPU, capacity=8.0, available=4.0))
        result = rm.allocate(3.0, ResourceType.CPU, AllocationStrategy.BEST_FIT)
        assert result.name == "cpu-2"

    def test_allocate_exhausted(self):
        rm = ResourceManager()
        rm.register_resource(Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=1.0))
        with pytest.raises(NoResourceAvailableError):
            rm.allocate(5.0, ResourceType.CPU)

    def test_release(self):
        rm = ResourceManager()
        r = Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=4.0, allocated=4.0)
        rm.register_resource(r)
        rm.release(r.resource_id, 2.0)
        assert r.available == 6.0
        assert r.allocated == 2.0


class TestReservationLifecycle:
    def test_reserve_commit_release(self):
        rm = ResourceManager()
        r = Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=24.0)
        rm.register_resource(r)

        # Reserve
        res = rm.reserve(r.resource_id, 8.0, "agent-1", ttl=60.0)
        assert res.status == ReservationStatus.PENDING
        assert r.available == 16.0
        assert r.reserved == 8.0

        # Commit
        committed = rm.commit_reservation(res.reservation_id)
        assert committed.status == ReservationStatus.COMMITTED
        assert r.reserved == 0.0
        assert r.allocated == 8.0

    def test_reserve_and_release(self):
        rm = ResourceManager()
        r = Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=24.0)
        rm.register_resource(r)

        res = rm.reserve(r.resource_id, 8.0, "agent-1")
        released = rm.release_reservation(res.reservation_id)
        assert released.status == ReservationStatus.RELEASED
        assert r.available == 24.0
        assert r.reserved == 0.0

    def test_reserve_expired(self):
        rm = ResourceManager()
        r = Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=24.0)
        rm.register_resource(r)

        res = rm.reserve(r.resource_id, 8.0, "agent-1", ttl=0.001)
        import time
        time.sleep(0.01)

        with pytest.raises(ReservationExpiredError):
            rm.commit_reservation(res.reservation_id)

    def test_reserve_insufficient(self):
        rm = ResourceManager()
        r = Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=2.0)
        rm.register_resource(r)

        with pytest.raises(ResourceExhaustedError):
            rm.reserve(r.resource_id, 8.0, "agent-1")

    def test_cleanup_expired(self):
        rm = ResourceManager()
        r = Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=24.0)
        rm.register_resource(r)

        rm.reserve(r.resource_id, 8.0, "agent-1", ttl=0.001)
        import time
        time.sleep(0.01)

        expired = rm.cleanup_expired_reservations()
        assert len(expired) == 1


class TestLimits:
    def test_set_and_get_limit(self):
        rm = ResourceManager()
        limit = rm.set_limit(LimitScope.WORKSPACE, "ws-1", ResourceType.GPU, 8.0, LimitType.HARD)
        assert limit.limit == 8.0

        retrieved = rm.get_limit(LimitScope.WORKSPACE, "ws-1", ResourceType.GPU)
        assert retrieved is not None


class TestQuotas:
    def test_set_and_check_quota(self):
        rm = ResourceManager()
        rm.set_quota(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        assert rm.check_quota(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 500.0) is True
        assert rm.check_quota(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1500.0) is False


class TestHealth:
    def test_check_health(self):
        rm = ResourceManager()
        r = Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=6.0)
        rm.register_resource(r)
        report = rm.check_health(r.resource_id)
        assert report is not None
        assert "status" in report


class TestReporting:
    def test_utilization_report(self):
        rm = ResourceManager()
        rm.register_resource(Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=6.0))
        rm.register_resource(Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=20.0))
        report = rm.get_utilization_report()
        assert report["resource_count"] == 2
