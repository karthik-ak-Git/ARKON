"""ARKON Resource Manager - Exceptions.

All resource-manager-specific exceptions.
"""

from __future__ import annotations


class ResourceError(Exception):
    """Base resource error."""
    pass


# Resource errors


class ResourceNotFoundError(ResourceError):
    """Resource not found."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource not found: '{resource_id}'")


class ResourceAlreadyExistsError(ResourceError):
    """Resource already registered."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource already registered: '{resource_id}'")


class ResourceExhaustedError(ResourceError):
    """Resource has no available capacity."""
    def __init__(self, resource_id: str, requested: float, available: float):
        self.resource_id = resource_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Resource '{resource_id}' exhausted: "
            f"requested {requested}, available {available}"
        )


class ResourceUnavailableError(ResourceError):
    """Resource is unavailable (unhealthy/offline)."""
    def __init__(self, resource_id: str, health: str = ""):
        self.resource_id = resource_id
        self.health = health
        super().__init__(
            f"Resource '{resource_id}' unavailable"
            + (f" (health: {health})" if health else "")
        )


# Reservation errors


class ReservationError(ResourceError):
    """Base reservation error."""
    pass


class ReservationNotFoundError(ReservationError):
    """Reservation not found."""
    def __init__(self, reservation_id: str):
        self.reservation_id = reservation_id
        super().__init__(f"Reservation not found: '{reservation_id}'")


class ReservationExpiredError(ReservationError):
    """Reservation has expired."""
    def __init__(self, reservation_id: str):
        self.reservation_id = reservation_id
        super().__init__(f"Reservation expired: '{reservation_id}'")


class ReservationConflictError(ReservationError):
    """Reservation conflicts with existing reservation."""
    def __init__(self, resource_id: str, requested: float, available: float):
        self.resource_id = resource_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Reservation conflict on '{resource_id}': "
            f"requested {requested}, available {available}"
        )


class ReservationAlreadyCommittedError(ReservationError):
    """Reservation already committed."""
    def __init__(self, reservation_id: str):
        self.reservation_id = reservation_id
        super().__init__(f"Reservation already committed: '{reservation_id}'")


# Allocation errors


class AllocationError(ResourceError):
    """Base allocation error."""
    pass


class NoResourceAvailableError(AllocationError):
    """No resource available for the request."""
    def __init__(
        self,
        resource_type: str,
        amount: float,
        filters: dict | None = None,
    ):
        self.resource_type = resource_type
        self.amount = amount
        self.filters = filters or {}
        filter_str = ", ".join(f"{k}={v}" for k, v in self.filters.items())
        super().__init__(
            f"No resource available for type '{resource_type}' "
            f"(amount: {amount})"
            + (f" with filters: {filter_str}" if filter_str else "")
        )


class AllocationFailedError(AllocationError):
    """Allocation failed."""
    def __init__(self, resource_id: str, reason: str = ""):
        self.resource_id = resource_id
        self.reason = reason
        super().__init__(
            f"Allocation failed for '{resource_id}'"
            + (f": {reason}" if reason else "")
        )


class OverAllocationError(AllocationError):
    """Attempted to allocate more than available."""
    def __init__(self, resource_id: str, requested: float, available: float):
        self.resource_id = resource_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Over-allocation on '{resource_id}': "
            f"requested {requested}, available {available}"
        )


# Limit errors


class LimitError(ResourceError):
    """Base limit error."""
    pass


class QuotaExceededError(LimitError):
    """Quota exceeded."""
    def __init__(
        self,
        scope: str,
        resource_type: str,
        used: float,
        limit: float,
    ):
        self.scope = scope
        self.resource_type = resource_type
        self.used = used
        self.limit = limit
        super().__init__(
            f"Quota exceeded for '{scope}' on '{resource_type}': "
            f"used {used}, limit {limit}"
        )


class LimitExceededError(LimitError):
    """Resource limit exceeded."""
    def __init__(
        self,
        scope: str,
        resource_type: str,
        requested: float,
        limit: float,
    ):
        self.scope = scope
        self.resource_type = resource_type
        self.requested = requested
        self.limit = limit
        super().__init__(
            f"Limit exceeded for '{scope}' on '{resource_type}': "
            f"requested {requested}, limit {limit}"
        )


# Health errors


class HealthCheckError(ResourceError):
    """Health check failed."""
    def __init__(self, resource_id: str, reason: str = ""):
        self.resource_id = resource_id
        self.reason = reason
        super().__init__(
            f"Health check failed for '{resource_id}'"
            + (f": {reason}" if reason else "")
        )


# Monitor errors


class MonitorError(ResourceError):
    """Monitoring error."""
    pass


class DiscoveryError(MonitorError):
    """Resource discovery failed."""
    def __init__(self, source: str, reason: str = ""):
        self.source = source
        self.reason = reason
        super().__init__(
            f"Discovery failed from '{source}'"
            + (f": {reason}" if reason else "")
        )
