"""ARKON Resource Manager - Detector.

Hardware resource discovery and detection.
"""

from __future__ import annotations

import os
import platform
from typing import Any

import structlog

from app.resources.interfaces import ResourceHealth, ResourceType
from app.resources.resource import Resource

logger = structlog.get_logger(__name__)


class ResourceDetector:
    """Detects available hardware resources on the system.

    Discovers CPU, RAM, GPU, Disk, and Network resources.
    """

    def detect_all(self) -> list[Resource]:
        """Detect all available resources on the system."""
        resources: list[Resource] = []
        resources.extend(self.detect_cpu())
        resources.extend(self.detect_ram())
        resources.extend(self.detect_gpu())
        resources.extend(self.detect_disk())
        resources.extend(self.detect_network())
        return resources

    def detect_cpu(self) -> list[Resource]:
        """Detect CPU resources."""
        try:
            cpu_count = os.cpu_count() or 1
            resource = Resource(
                name="cpu",
                resource_type=ResourceType.CPU,
                capacity=float(cpu_count),
                available=float(cpu_count),
                health=ResourceHealth.HEALTHY,
                metadata={
                    "core_count": cpu_count,
                    "architecture": platform.machine(),
                    "processor": platform.processor(),
                },
                tags=["cpu", "compute"],
            )
            return [resource]
        except Exception as e:
            logger.error("cpu_detection_failed", error=str(e))
            return []

    def detect_ram(self) -> list[Resource]:
        """Detect RAM resources."""
        try:
            # Try psutil first
            try:
                import psutil
                mem = psutil.virtual_memory()
                capacity_gb = mem.total / (1024**3)
                available_gb = mem.available / (1024**3)
            except ImportError:
                # Fallback: estimate from OS
                capacity_gb = 8.0  # Default estimate
                available_gb = capacity_gb * 0.5

            resource = Resource(
                name="ram",
                resource_type=ResourceType.RAM,
                capacity=capacity_gb,
                available=available_gb,
                health=ResourceHealth.HEALTHY,
                metadata={
                    "total_bytes": capacity_gb * (1024**3),
                    "platform": platform.system(),
                },
                tags=["memory", "ram"],
            )
            return [resource]
        except Exception as e:
            logger.error("ram_detection_failed", error=str(e))
            return []

    def detect_gpu(self) -> list[Resource]:
        """Detect GPU resources."""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.info("no_nvidia_gpu")
                return []

            resources = []
            for i, line in enumerate(result.stdout.strip().split("\n")):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    name = parts[0]
                    total_mb = float(parts[1])
                    free_mb = float(parts[2])
                    resources.append(Resource(
                        name=f"gpu_{i}",
                        resource_type=ResourceType.GPU,
                        capacity=total_mb,
                        available=free_mb,
                        health=ResourceHealth.HEALTHY,
                        metadata={
                            "gpu_name": name,
                            "total_vram_mb": total_mb,
                            "free_vram_mb": free_mb,
                            "device_index": i,
                        },
                        tags=["gpu", "cuda", "compute"],
                    ))
            return resources
        except FileNotFoundError:
            logger.info("nvidia_smi_not_found")
            return []
        except Exception as e:
            logger.error("gpu_detection_failed", error=str(e))
            return []

    def detect_disk(self) -> list[Resource]:
        """Detect disk resources."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            total_gb = total / (1024**3)
            free_gb = free / (1024**3)
            resource = Resource(
                name="disk",
                resource_type=ResourceType.DISK,
                capacity=total_gb,
                available=free_gb,
                health=ResourceHealth.HEALTHY,
                metadata={
                    "total_bytes": total,
                    "used_bytes": used,
                    "free_bytes": free,
                    "mount_point": "/",
                },
                tags=["disk", "storage"],
            )
            return [resource]
        except Exception as e:
            logger.error("disk_detection_failed", error=str(e))
            return []

    def detect_network(self) -> list[Resource]:
        """Detect network resources."""
        try:
            resource = Resource(
                name="network",
                resource_type=ResourceType.NETWORK,
                capacity=1000.0,  # Mbps estimate
                available=1000.0,
                health=ResourceHealth.HEALTHY,
                metadata={
                    "interface": "default",
                    "estimated_bandwidth_mbps": 1000,
                },
                tags=["network", "io"],
            )
            return [resource]
        except Exception as e:
            logger.error("network_detection_failed", error=str(e))
            return []

    def to_dict(self) -> dict[str, Any]:
        return {"detector": "resource_detector"}
