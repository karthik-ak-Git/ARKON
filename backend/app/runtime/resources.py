"""ARKON Runtime - Resource Management.

Every agent declares resource requirements.
The runtime tracks real usage.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ResourceProfile:
    """Resource requirements for an agent."""
    cpu: float = 0.5  # CPU cores
    ram: float = 256.0  # MB
    vram: float = 0.0  # MB (GPU memory)
    gpu_required: bool = False
    network: bool = False
    disk: float = 100.0  # MB
    estimated_runtime: float = 60.0  # seconds
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu": self.cpu,
            "ram": self.ram,
            "vram": self.vram,
            "gpu_required": self.gpu_required,
            "network": self.network,
            "disk": self.disk,
            "estimated_runtime": self.estimated_runtime,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceProfile:
        return cls(
            cpu=data.get("cpu", 0.5),
            ram=data.get("ram", 256.0),
            vram=data.get("vram", 0.0),
            gpu_required=data.get("gpu_required", False),
            network=data.get("network", False),
            disk=data.get("disk", 100.0),
            estimated_runtime=data.get("estimated_runtime", 60.0),
            priority=data.get("priority", 0),
        )


@dataclass
class ResourceUsage:
    """Actual resource usage by an agent."""
    agent_id: str
    cpu: float = 0.0
    ram: float = 0.0
    vram: float = 0.0
    disk: float = 0.0
    network_bytes_in: int = 0
    network_bytes_out: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "cpu": self.cpu,
            "ram": self.ram,
            "vram": self.vram,
            "disk": self.disk,
            "network_bytes_in": self.network_bytes_in,
            "network_bytes_out": self.network_bytes_out,
            "timestamp": self.timestamp,
        }


class ResourceTracker:
    """Tracks resource usage across all agents."""

    def __init__(
        self,
        total_cpu: float = 8.0,
        total_ram: float = 16384.0,
        total_vram: float = 8192.0,
    ) -> None:
        self._total_cpu = total_cpu
        self._total_ram = total_ram
        self._total_vram = total_vram
        self._usage: dict[str, ResourceUsage] = {}
        self._profiles: dict[str, ResourceProfile] = {}

    def register_profile(
        self, agent_id: str, profile: ResourceProfile
    ) -> None:
        """Register resource profile for an agent."""
        self._profiles[agent_id] = profile

    def unregister_profile(self, agent_id: str) -> None:
        """Unregister resource profile."""
        self._profiles.pop(agent_id, None)

    def update_usage(self, usage: ResourceUsage) -> None:
        """Update resource usage for an agent."""
        self._usage[usage.agent_id] = usage

    def remove_usage(self, agent_id: str) -> None:
        """Remove usage tracking for an agent."""
        self._usage.pop(agent_id, None)

    def get_usage(self, agent_id: str) -> ResourceUsage | None:
        """Get current usage for an agent."""
        return self._usage.get(agent_id)

    def get_total_usage(self) -> ResourceUsage:
        """Get total resource usage across all agents."""
        total = ResourceUsage(agent_id="__total__")
        for usage in self._usage.values():
            total.cpu += usage.cpu
            total.ram += usage.ram
            total.vram += usage.vram
            total.disk += usage.disk
            total.network_bytes_in += usage.network_bytes_in
            total.network_bytes_out += usage.network_bytes_out
        return total

    def can_allocate(self, profile: ResourceProfile) -> bool:
        """Check if resources can be allocated."""
        total = self.get_total_usage()
        return (
            total.cpu + profile.cpu <= self._total_cpu
            and total.ram + profile.ram <= self._total_ram
            and (not profile.gpu_required or total.vram + profile.vram <= self._total_vram)
        )

    def get_available(self) -> dict[str, float]:
        """Get available resources."""
        total = self.get_total_usage()
        return {
            "cpu": max(0, self._total_cpu - total.cpu),
            "ram": max(0, self._total_ram - total.ram),
            "vram": max(0, self._total_vram - total.vram),
        }

    def get_allocated(self) -> dict[str, float]:
        """Get allocated resources."""
        total = self.get_total_usage()
        return {
            "cpu": total.cpu,
            "ram": total.ram,
            "vram": total.vram,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": {
                "cpu": self._total_cpu,
                "ram": self._total_ram,
                "vram": self._total_vram,
            },
            "available": self.get_available(),
            "allocated": self.get_allocated(),
            "agents": {
                aid: usage.to_dict()
                for aid, usage in self._usage.items()
            },
        }
