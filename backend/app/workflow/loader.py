"""Workflow loader — loads workflow definitions from files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.workflow.exceptions import LoaderError
from app.workflow.interfaces import WorkflowFormat
from app.workflow.parser import WorkflowParser
from app.workflow.serializer import WorkflowSerializer


class WorkflowLoader:
    """Loads workflow definitions from files or directories."""

    def __init__(self) -> None:
        self._parser = WorkflowParser()
        self._serializer = WorkflowSerializer()

    def load_file(self, path: str | Path) -> dict[str, Any]:
        path = Path(path)
        if not path.exists():
            raise LoaderError(f"File not found: {path}")
        if not path.is_file():
            raise LoaderError(f"Not a file: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            raise LoaderError(f"Failed to read file: {e}") from e

        fmt = self._detect_format(path)
        return self._parser.parse(content, fmt)

    def load_string(self, content: str, format: WorkflowFormat | None = None) -> dict[str, Any]:
        if format is None:
            format = self._parser.detect_format(content)
        return self._parser.parse(content, format)

    def load_directory(self, directory: str | Path) -> dict[str, dict[str, Any]]:
        directory = Path(directory)
        if not directory.is_dir():
            raise LoaderError(f"Not a directory: {directory}")

        workflows: dict[str, dict[str, Any]] = {}
        for entry in sorted(directory.iterdir()):
            if entry.is_file() and self._is_workflow_file(entry):
                try:
                    wf = self.load_file(entry)
                    wf_id = wf.get("workflow_id", entry.stem)
                    workflows[wf_id] = wf
                except Exception:
                    continue
        return workflows

    def save_file(self, definition: dict[str, Any], path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fmt = self._detect_format(path)
        content = self._serializer.serialize(definition, fmt)

        try:
            path.write_text(content, encoding="utf-8")
        except OSError as e:
            raise LoaderError(f"Failed to write file: {e}") from e

    def _detect_format(self, path: Path) -> WorkflowFormat:
        suffix = path.suffix.lower()
        if suffix == ".json":
            return WorkflowFormat.JSON
        elif suffix in (".yaml", ".yml"):
            return WorkflowFormat.YAML
        return WorkflowFormat.YAML

    def _is_workflow_file(self, path: Path) -> bool:
        return path.suffix.lower() in (".yaml", ".yml", ".json")
