"""Fair share scheduling - ensures equitable resource distribution."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ShareRecord:
    """Tracks share allocation for a group."""

    group_id: str
    allocated: float = 0.0
    consumed: float = 0.0
    weight: float = 1.0
    last_updated: float = field(default_factory=time.time)

    @property
    def available(self) -> float:
        return max(0.0, self.allocated - self.consumed)

    @property
    def utilization(self) -> float:
        return self.consumed / self.allocated if self.allocated > 0 else 0.0


class FairShareManager:
    """Manages fair share allocation across groups."""

    def __init__(self) -> None:
        self._records: dict[str, ShareRecord] = {}
        self._total_weight: float = 0.0

    def register_group(self, group_id: str, weight: float = 1.0) -> None:
        self._records[group_id] = ShareRecord(group_id=group_id, weight=weight)
        self._recalculate_total()

    def unregister_group(self, group_id: str) -> None:
        self._records.pop(group_id, None)
        self._recalculate_total()

    def set_weight(self, group_id: str, weight: float) -> None:
        if group_id in self._records:
            self._records[group_id].weight = weight
            self._recalculate_total()

    def allocate(self, group_id: str, amount: float) -> bool:
        """Allocate resources to a group. Returns False if insufficient share."""
        record = self._records.get(group_id)
        if not record:
            return False
        share = self._get_share(group_id)
        if record.consumed + amount > share:
            return False
        record.consumed += amount
        record.last_updated = time.time()
        return True

    def release(self, group_id: str, amount: float) -> None:
        record = self._records.get(group_id)
        if record:
            record.consumed = max(0.0, record.consumed - amount)
            record.last_updated = time.time()

    def get_share(self, group_id: str) -> float:
        return self._get_share(group_id)

    def get_deficit(self, group_id: str) -> float:
        """How much more this group could use."""
        record = self._records.get(group_id)
        if not record:
            return 0.0
        share = self._get_share(group_id)
        return max(0.0, share - record.consumed)

    def get_most_deficit_group(self) -> str | None:
        """Group with highest deficit (most under-served)."""
        if not self._records:
            return None
        return max(self._records.keys(), key=lambda g: self.get_deficit(g))

    def get_records(self) -> dict[str, ShareRecord]:
        return dict(self._records)

    def to_dict(self) -> dict:
        return {
            "groups": {
                gid: {
                    "weight": r.weight,
                    "consumed": r.consumed,
                    "share": self._get_share(gid),
                    "deficit": self.get_deficit(gid),
                }
                for gid, r in self._records.items()
            },
            "total_weight": self._total_weight,
        }

    def _get_share(self, group_id: str) -> float:
        record = self._records.get(group_id)
        if not record or self._total_weight <= 0:
            return 0.0
        return record.weight / self._total_weight

    def _recalculate_total(self) -> None:
        self._total_weight = sum(r.weight for r in self._records.values())
