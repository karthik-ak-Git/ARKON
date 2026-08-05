"""ARKON Resource Manager - Main Orchestrator.

Central resource management system that owns resources, tracks usage,
enforces limits, and provides health monitoring.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import structlog

from app.resources.interfaces import (
    AllocationStrategy,
    IResourceManager,
    LimitScope,
    LimitType,
    ResourceHealth,
    ResourceType,
    ReservationStatus,
)
from app.resources.resource import Resource
from app.resources.reservation import Reservation
from app.resources.limits import ResourceLimit, ResourceQuota
from app.resources.allocator import ResourceAllocator
from app.resources.monitor import ResourceMonitor
from app.resources.health import ResourceHealthTracker
from app.resources.detector import ResourceDetector
from app.resources.quota import QuotaManager
from app.resources.providers import (
    GPUProvider,
    ModelProvider,
    APIProvider,
    WorkspaceProvider,
)
from app.resources.metrics import MetricsCollector
from app.resources.exceptions import (
    ResourceNotFoundError,
    ResourceExhaustedError,
    ResourceUnavailableError,
    ReservationNotFoundError,
    ReservationExpiredError,
    ReservationConflictError,
    AllocationError,
    QuotaExceededError,
)

logger = structlog.get_logger(__name__)


class ResourceManager:
    """Central resource management system.

    Responsibilities:
    - Resource discovery and registration
    - Resource allocation with multiple strategies
    - Reservation lifecycle management (Reserve → Commit → Release)
    - Limit enforcement (per-scope, hard/soft)
    - Health monitoring and tracking
    - Utilization reporting
    """

    def __init__(self) -> None:
        self._resources: dict[str, Resource] = {}
        self._reservations: dict[str, Reservation] = {}
        self._limits: dict[str, ResourceLimit] = {}
        self._allocator = ResourceAllocator()
        self._monitor = ResourceMonitor()
        self._health_tracker = ResourceHealthTracker()
        self._detector = ResourceDetector()
        self._quota_manager = QuotaManager()
        self._gpu_provider = GPUProvider()
        self._model_provider = ModelProvider()
        self._api_provider = APIProvider()
        self._workspace_provider = WorkspaceProvider()
        self._metrics = MetricsCollector()
        self._initialized = False

    # ── IResourceManager Interface ──

    def initialize(self) -> None:
        """Initialize the resource manager."""
        if self._initialized:
            return
        self._initialized = True
        logger.info("resource_manager_initialized")

    def shutdown(self) -> None:
        """Shutdown the resource manager."""
        self._resources.clear()
        self._reservations.clear()
        self._limits.clear()
        self._gpu_provider.clear()
        self._model_provider.clear()
        self._api_provider.clear()
        self._workspace_provider.clear()
        self._metrics.clear()
        self._initialized = False
        logger.info("resource_manager_shutdown")

    def get_id(self) -> str:
        return "resource_manager"

    # ── Resource Registration ──

    def register_resource(self, resource: Resource) -> None:
        """Register a new resource."""
        self._resources[resource.resource_id] = resource
        self._health_tracker.record_health(resource, resource.health)
        logger.debug("resource_registered", resource_id=resource.resource_id, name=resource.name)

    def unregister_resource(self, resource_id: str) -> bool:
        """Unregister a resource. Returns True if removed."""
        if resource_id in self._resources:
            del self._resources[resource_id]
            self._health_tracker.clear_history(resource_id)
            return True
        return False

    def get_resource(self, resource_id: str) -> Resource | None:
        """Get a resource by ID."""
        return self._resources.get(resource_id)

    def list_resources(self, resource_type: ResourceType | None = None) -> list[Resource]:
        """List all resources, optionally filtered by type."""
        if resource_type is None:
            return list(self._resources.values())
        return [r for r in self._resources.values() if r.resource_type == resource_type]

    def discover_resources(self) -> list[Resource]:
        """Auto-discover hardware resources."""
        detected = self._detector.detect_all()
        for resource in detected:
            self.register_resource(resource)
        return detected

    # ── Allocation ──

    def allocate(
        self,
        amount: float,
        resource_type: ResourceType,
        strategy: AllocationStrategy = AllocationStrategy.BEST_FIT,
        tags: list[str] | None = None,
        scope: LimitScope = LimitScope.GLOBAL,
        scope_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Allocate a resource.

        Selects a resource using the strategy, enforces limits,
        and returns the allocated resource.
        """
        # Check limits
        limit_key = f"{scope.value}:{scope_id}:{resource_type.value}"
        limit = self._limits.get(limit_key)
        if limit and not limit.can_allocate(amount):
            if limit.limit_type == LimitType.HARD:
                raise AllocationError(
                    resource_type=resource_type.value,
                    reason=f"Hard limit exceeded: {limit.used}/{limit.limit}",
                )
            # Soft limit: warn but allow
            logger.warning(
                "soft_limit_exceeded",
                limit_id=limit.limit_id,
                used=limit.used,
                limit=limit.limit,
            )

        resources = list(self._resources.values())
        start = time.time()

        try:
            selected = self._allocator.allocate(
                resources=resources,
                amount=amount,
                resource_type=resource_type,
                strategy=strategy,
                tags=tags,
                metadata=metadata,
            )
        except Exception as e:
            if resources:
                self._metrics.record_error(resources[0], str(e))
            raise

        duration_ms = (time.time() - start) * 1000

        # Record allocation
        self._metrics.record_allocation(selected, amount, duration_ms)
        self._monitor.check_resource(selected)

        # Update limit usage
        if limit:
            limit.allocate(amount)

        return selected

    def release(self, resource_id: str, amount: float) -> None:
        """Release allocated resources."""
        resource = self.get_resource(resource_id)
        if resource is None:
            raise ResourceNotFoundError(resource_id)

        resource.available += amount
        resource.allocated = max(0.0, resource.allocated - amount)
        resource.update_status()

        self._metrics.record_release(resource, amount)
        self._monitor.check_resource(resource)

        # Update limit usage
        for limit in self._limits.values():
            if limit.resource_type == resource.resource_type:
                limit.release(amount)
                break

    # ── Reservation Lifecycle ──

    def reserve(
        self,
        resource_id: str,
        amount: float,
        owner: str,
        ttl: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Reservation:
        """Reserve resources for later commit."""
        resource = self.get_resource(resource_id)
        if resource is None:
            raise ResourceNotFoundError(resource_id)

        if resource.available < amount:
            raise ResourceExhaustedError(
                resource_id=resource_id,
                available=resource.available,
                requested=amount,
            )

        expires_at = time.time() + ttl if ttl else None

        reservation = Reservation(
            resource_id=resource_id,
            amount=amount,
            owner=owner,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        resource.available -= amount
        resource.reserved += amount
        resource.update_status()

        self._reservations[reservation.reservation_id] = reservation
        self._metrics.record_reservation(resource, amount)

        logger.debug(
            "resource_reserved",
            reservation_id=reservation.reservation_id,
            resource_id=resource_id,
            amount=amount,
            owner=owner,
        )
        return reservation

    def commit_reservation(self, reservation_id: str) -> Reservation:
        """Commit a reservation (convert to allocation)."""
        reservation = self.get_reservation(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(reservation_id)

        if reservation.is_expired():
            reservation.expire()
            raise ReservationExpiredError(reservation_id)

        if reservation.status != ReservationStatus.PENDING:
            raise ReservationConflictError(
                resource_id=reservation.resource_id,
                requested=reservation.amount,
                available=0.0,
            )

        resource = self.get_resource(reservation.resource_id)
        if resource is None:
            raise ResourceNotFoundError(reservation.resource_id)

        # Convert reservation to allocation
        resource.reserved -= reservation.amount
        resource.allocated += reservation.amount
        resource.update_status()

        reservation.commit()
        return reservation

    def release_reservation(self, reservation_id: str) -> Reservation:
        """Release a reservation without committing."""
        reservation = self.get_reservation(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(reservation_id)

        resource = self.get_resource(reservation.resource_id)
        if resource:
            resource.reserved -= reservation.amount
            resource.available += reservation.amount
            resource.update_status()

        reservation.release()
        return reservation

    def get_reservation(self, reservation_id: str) -> Reservation | None:
        """Get a reservation by ID."""
        return self._reservations.get(reservation_id)

    def list_reservations(self, owner: str | None = None) -> list[Reservation]:
        """List reservations, optionally filtered by owner."""
        if owner is None:
            return list(self._reservations.values())
        return [r for r in self._reservations.values() if r.owner == owner]

    def cleanup_expired_reservations(self) -> list[Reservation]:
        """Clean up expired reservations. Returns list of expired reservations."""
        expired = []
        for res in list(self._reservations.values()):
            if res.is_expired() and res.status == ReservationStatus.PENDING:
                resource = self.get_resource(res.resource_id)
                if resource:
                    resource.reserved -= res.amount
                    resource.available += res.amount
                    resource.update_status()
                res.expire()
                expired.append(res)
        return expired

    # ── Limits ──

    def set_limit(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        limit: float,
        limit_type: LimitType = LimitType.HARD,
    ) -> ResourceLimit:
        """Set a resource limit."""
        key = f"{scope.value}:{scope_id}:{resource_type.value}"
        rl = ResourceLimit(
            scope=scope,
            scope_id=scope_id,
            resource_type=resource_type,
            limit=limit,
            limit_type=limit_type,
        )
        self._limits[key] = rl
        return rl

    def get_limit(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
    ) -> ResourceLimit | None:
        """Get a resource limit."""
        key = f"{scope.value}:{scope_id}:{resource_type.value}"
        return self._limits.get(key)

    # ── Health ──

    def check_health(self, resource_id: str) -> dict[str, Any] | None:
        """Check resource health."""
        resource = self.get_resource(resource_id)
        if resource is None:
            return None
        return self._monitor.check_resource(resource)

    def get_health_history(self, resource_id: str) -> list[dict[str, Any]]:
        """Get health history for a resource."""
        records = self._health_tracker.get_history(resource_id)
        return [{"health": r.health.value, "timestamp": r.timestamp, "details": r.details} for r in records]

    # ── Quotas ──

    def set_quota(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        quota: float,
        reset_interval: float | None = None,
    ) -> ResourceQuota:
        """Set a resource quota."""
        return self._quota_manager.register(scope, scope_id, resource_type, quota, reset_interval)

    def check_quota(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        amount: float,
    ) -> bool:
        """Check if consuming amount would exceed quota."""
        return self._quota_manager.check(scope, scope_id, resource_type, amount)

    def consume_quota(
        self,
        scope: LimitScope,
        scope_id: str,
        resource_type: ResourceType,
        amount: float,
    ) -> None:
        """Consume quota."""
        self._quota_manager.consume(scope, scope_id, resource_type, amount)

    # ── Metrics & Reporting ──

    def get_utilization_report(self) -> dict[str, Any]:
        """Get overall utilization report."""
        return self._monitor.get_utilization_report(list(self._resources.values()))

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics summary."""
        return {
            "resources": len(self._resources),
            "reservations": len(self._reservations),
            "limits": len(self._limits),
            "metrics": self._metrics.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "resource_count": len(self._resources),
            "reservation_count": len(self._reservations),
            "limit_count": len(self._limits),
            "resources": {rid: r.to_dict() for rid, r in self._resources.items()},
            "reservations": {rid: r.to_dict() for rid, r in self._reservations.items()},
        }
