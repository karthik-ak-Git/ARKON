"""Tests for Resource Manager - Limits and Quotas."""

import pytest
from app.resources.limits import ResourceLimit, ResourceQuota
from app.resources.interfaces import LimitScope, LimitType, ResourceType


class TestResourceLimit:
    def test_hard_limit(self):
        limit = ResourceLimit(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.GPU,
            limit=8.0,
            limit_type=LimitType.HARD,
        )
        assert limit.can_allocate(8.0) is True
        assert limit.can_allocate(9.0) is False

    def test_soft_limit(self):
        limit = ResourceLimit(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.GPU,
            limit=8.0,
            limit_type=LimitType.SOFT,
        )
        assert limit.can_allocate(10.0) is True  # Soft limits always allow
        assert limit.is_soft_exceeded is False

    def test_allocate_and_release(self):
        limit = ResourceLimit(
            scope=LimitScope.AGENT,
            scope_id="agent-1",
            resource_type=ResourceType.RAM,
            limit=16.0,
        )
        limit.allocate(5.0)
        assert limit.used == 5.0
        assert limit.available == pytest.approx(11.0)

        limit.release(3.0)
        assert limit.used == 2.0

    def test_utilization(self):
        limit = ResourceLimit(
            scope=LimitScope.GLOBAL,
            scope_id="",
            resource_type=ResourceType.CPU,
            limit=100.0,
            used=75.0,
        )
        assert limit.utilization == pytest.approx(0.75)

    def test_reset(self):
        limit = ResourceLimit(
            scope=LimitScope.GLOBAL,
            scope_id="",
            resource_type=ResourceType.CPU,
            limit=100.0,
            used=50.0,
        )
        limit.reset()
        assert limit.used == 0.0

    def test_to_dict(self):
        limit = ResourceLimit(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.GPU,
            limit=8.0,
        )
        d = limit.to_dict()
        assert d["scope"] == "workspace"
        assert d["limit"] == 8.0


class TestResourceQuota:
    def test_quota_tracking(self):
        quota = ResourceQuota(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.API_TOKEN,
            quota=1000.0,
        )
        assert quota.available == 1000.0
        quota.consume(300.0)
        assert quota.used == 300.0
        assert quota.available == pytest.approx(700.0)

    def test_quota_exceeded(self):
        quota = ResourceQuota(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.API_TOKEN,
            quota=100.0,
        )
        quota.consume(150.0)
        assert quota.is_exceeded is True

    def test_quota_reset(self):
        quota = ResourceQuota(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.API_TOKEN,
            quota=1000.0,
            used=500.0,
        )
        quota.reset()
        assert quota.used == 0.0

    def test_quota_utilization(self):
        quota = ResourceQuota(
            scope=LimitScope.WORKSPACE,
            scope_id="ws-1",
            resource_type=ResourceType.API_TOKEN,
            quota=1000.0,
            used=250.0,
        )
        assert quota.utilization == pytest.approx(0.25)

    def test_to_dict(self):
        quota = ResourceQuota(
            scope=LimitScope.GLOBAL,
            scope_id="",
            resource_type=ResourceType.CPU,
            quota=100.0,
        )
        d = quota.to_dict()
        assert d["quota"] == 100.0
        assert d["is_exceeded"] is False
