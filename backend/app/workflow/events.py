"""Workflow Runtime events."""

from __future__ import annotations

import time
from typing import Any

from app.events.interfaces import Event, EventMetadata


def _make_workflow_event(
    event_type: str,
    workflow_id: str,
    source: str = "workflow_runtime",
    **extra: Any,
) -> Event:
    metadata = EventMetadata(source=source, tags=[f"workflow:{workflow_id}"])
    payload: dict[str, Any] = {"workflow_id": workflow_id, **extra}
    return Event(
        event_type=event_type,
        metadata=metadata,
        payload=payload,
    )


def workflow_loaded_event(
    workflow_id: str,
    name: str = "",
    version: str = "",
    node_count: int = 0,
    edge_count: int = 0,
) -> Event:
    return _make_workflow_event(
        "workflow.loaded",
        workflow_id,
        name=name,
        version=version,
        node_count=node_count,
        edge_count=edge_count,
    )


def workflow_validated_event(
    workflow_id: str,
    is_valid: bool = True,
    error_count: int = 0,
    warning_count: int = 0,
) -> Event:
    return _make_workflow_event(
        "workflow.validated",
        workflow_id,
        is_valid=is_valid,
        error_count=error_count,
        warning_count=warning_count,
    )


def workflow_compiled_event(
    workflow_id: str,
    plan_id: str = "",
    task_count: int = 0,
) -> Event:
    return _make_workflow_event(
        "workflow.compiled",
        workflow_id,
        plan_id=plan_id,
        task_count=task_count,
    )


def workflow_failed_event(
    workflow_id: str,
    error: str = "",
    phase: str = "",
) -> Event:
    return _make_workflow_event(
        "workflow.failed",
        workflow_id,
        error=error,
        phase=phase,
    )
