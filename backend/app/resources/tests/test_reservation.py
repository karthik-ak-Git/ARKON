"""Tests for Resource Manager - Reservation model."""

import pytest
from app.resources.reservation import Reservation
from app.resources.interfaces import ReservationStatus


class TestReservation:
    def test_create_reservation(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        assert res.resource_id == "res-1"
        assert res.amount == 5.0
        assert res.owner == "agent-1"
        assert res.status == ReservationStatus.PENDING

    def test_commit(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        res.commit()
        assert res.status == ReservationStatus.COMMITTED
        assert res.committed_at is not None

    def test_release(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        res.release()
        assert res.status == ReservationStatus.RELEASED
        assert res.released_at is not None

    def test_cancel(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        res.cancel()
        assert res.status == ReservationStatus.CANCELLED

    def test_expire(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        res.expire()
        assert res.status == ReservationStatus.EXPIRED

    def test_timeout(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        res.timeout()
        assert res.status == ReservationStatus.TIMED_OUT

    def test_is_expired_with_ttl(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1", expires_at=0.0)
        assert res.is_expired() is True

    def test_is_expired_no_ttl(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        assert res.is_expired() is False

    def test_to_dict(self):
        res = Reservation(resource_id="res-1", amount=5.0, owner="agent-1")
        d = res.to_dict()
        assert d["resource_id"] == "res-1"
        assert d["amount"] == 5.0
        assert d["status"] == "pending"

    def test_from_dict(self):
        data = {"resource_id": "res-1", "amount": 10.0, "owner": "agent-2", "status": "committed"}
        res = Reservation.from_dict(data)
        assert res.resource_id == "res-1"
        assert res.amount == 10.0
        assert res.status == ReservationStatus.COMMITTED
