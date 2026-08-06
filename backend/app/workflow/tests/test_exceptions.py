"""Tests for workflow exceptions."""

import pytest
from app.workflow.exceptions import (
    CyclicDependencyError,
    DAGError,
    InvalidEdgeError,
    LoaderError,
    MissingCapabilityError,
    MissingInputError,
    MissingNodeError,
    RegistryError,
    SchemaError,
    SerializerError,
    TemplateNotFoundError,
    WorkflowCompilationError,
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowParseError,
    WorkflowPlanningError,
    WorkflowValidationError,
    WorkflowVersionError,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        with pytest.raises(WorkflowError):
            raise WorkflowError("test")

    @pytest.mark.parametrize("exc_class", [
        WorkflowNotFoundError,
        WorkflowValidationError,
        WorkflowCompilationError,
        WorkflowPlanningError,
        WorkflowParseError,
        WorkflowVersionError,
        DAGError,
        TemplateNotFoundError,
        RegistryError,
        SerializerError,
        LoaderError,
    ])
    def test_inherits_from_base(self, exc_class):
        assert issubclass(exc_class, WorkflowError)

    @pytest.mark.parametrize("exc_class", [
        CyclicDependencyError,
        MissingNodeError,
        MissingCapabilityError,
        MissingInputError,
        InvalidEdgeError,
        SchemaError,
    ])
    def test_validation_subclasses(self, exc_class):
        assert issubclass(exc_class, WorkflowValidationError)
        assert issubclass(exc_class, WorkflowError)

    def test_workflow_not_found(self):
        with pytest.raises(WorkflowNotFoundError, match="not found"):
            raise WorkflowNotFoundError("not found")

    def test_cyclic_dependency(self):
        with pytest.raises(CyclicDependencyError, match="cycle"):
            raise CyclicDependencyError("cycle")

    def test_compilation_error(self):
        with pytest.raises(WorkflowCompilationError, match="compile"):
            raise WorkflowCompilationError("compile")
