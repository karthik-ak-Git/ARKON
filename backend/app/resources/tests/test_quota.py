"""Tests for Resource Manager - QuotaManager."""

import pytest
from app.resources.quota import QuotaManager
from app.resources.interfaces import LimitScope, ResourceType
from app.resources.exceptions import QuotaExceededError


class TestQuotaManager:
    def test_register_and_get(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        q = qm.get(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN)
        assert q is not None
        assert q.quota == 1000.0

    def test_check_within_quota(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        assert qm.check(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 500.0) is True

    def test_check_exceeds_quota(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 100.0)
        assert qm.check(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 150.0) is False

    def test_consume_within_quota(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        qm.consume(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 300.0)
        q = qm.get(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN)
        assert q.used == 300.0

    def test_consume_exceeds_quota(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 100.0)
        with pytest.raises(QuotaExceededError):
            qm.consume(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 150.0)

    def test_release_quota(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        qm.consume(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 500.0)
        qm.release(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 200.0)
        q = qm.get(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN)
        assert q.used == 300.0

    def test_reset(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        qm.consume(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 500.0)
        qm.reset(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN)
        q = qm.get(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN)
        assert q.used == 0.0

    def test_list_all(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        qm.register(LimitScope.WORKSPACE, "ws-2", ResourceType.API_TOKEN, 500.0)
        assert len(qm.list_all()) == 2

    def test_remove(self):
        qm = QuotaManager()
        qm.register(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 1000.0)
        assert qm.remove(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN) is True
        assert qm.get(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN) is None

    def test_check_no_quota_unlimited(self):
        qm = QuotaManager()
        assert qm.check(LimitScope.WORKSPACE, "ws-1", ResourceType.API_TOKEN, 999999.0) is True
