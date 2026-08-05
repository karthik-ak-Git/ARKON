"""ARKON Resource Manager - Reservation Model.

Defines the Reservation data structure.
Reservations track pending, committed, and released resource allocations.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.resources.interfaces import IReservation, ReservationStatus


@dataclass
class Reservation(IReservation):
    """A resource reservation.

    Reservations have a lifecycle: PENDING → COMMITTED → RELEASED.
    They can also EXPIRE, be CANCELLED, or TIMED_OUT.
    """

    resource_id: str
    amount: float
    owner: str
    status: ReservationStatus = ReservationStatus.PENDING
    reservation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    committed_at: float | None = None
    released_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_id(self) -> str:
        return self.reservation_id

    def get_resource_id(self) -> str:
        return self.resource_id

    def get_amount(self) -> float:
        return self.amount

    def get_status(self) -> ReservationStatus:
        return self.status

    def get_owner(self) -> str:
        return self.owner

    def get_expires_at(self) -> float | None:
        return self.expires_at

    def is_expired(self) -> bool:
        """Check if reservation has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def commit(self) -> None:
        """Commit the reservation."""
        self.status = ReservationStatus.COMMITTED
        self.committed_at = time.time()

    def release(self) -> None:
        """Release the reservation."""
        self.status = ReservationStatus.RELEASED
        self.released_at = time.time()

    def cancel(self) -> None:
        """Cancel the reservation."""
        self.status = ReservationStatus.CANCELLED

    def expire(self) -> None:
        """Mark reservation as expired."""
        self.status = ReservationStatus.EXPIRED

    def timeout(self) -> None:
        """Mark reservation as timed out."""
        self.status = ReservationStatus.TIMED_OUT

    def to_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "resource_id": self.resource_id,
            "amount": self.amount,
            "owner": self.owner,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "committed_at": self.committed_at,
            "released_at": self.released_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Reservation:
        return cls(
            reservation_id=data.get("reservation_id", uuid.uuid4().hex[:16]),
            resource_id=data["resource_id"],
            amount=data.get("amount", 0.0),
            owner=data.get("owner", ""),
            status=ReservationStatus(data.get("status", "pending")),
            created_at=data.get("created_at", time.time()),
            expires_at=data.get("expires_at"),
            committed_at=data.get("committed_at"),
            released_at=data.get("released_at"),
            metadata=data.get("metadata", {}),
        )
