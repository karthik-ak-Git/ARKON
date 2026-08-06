"""Workflow Runtime exceptions."""


class WorkflowError(Exception):
    """Base workflow error."""


class WorkflowNotFoundError(WorkflowError):
    """Workflow not found."""


class WorkflowValidationError(WorkflowError):
    """Workflow validation failed."""


class WorkflowCompilationError(WorkflowError):
    """Workflow compilation failed."""


class WorkflowPlanningError(WorkflowError):
    """Workflow planning failed."""


class WorkflowParseError(WorkflowError):
    """Failed to parse workflow definition."""


class WorkflowVersionError(WorkflowError):
    """Workflow version incompatibility."""


class CyclicDependencyError(WorkflowValidationError):
    """Workflow contains a cycle."""


class MissingNodeError(WorkflowValidationError):
    """A referenced node is missing."""


class MissingCapabilityError(WorkflowValidationError):
    """A node references a missing capability."""


class MissingInputError(WorkflowValidationError):
    """A required input is not connected."""


class InvalidEdgeError(WorkflowValidationError):
    """An edge references invalid nodes."""


class SchemaError(WorkflowValidationError):
    """Workflow definition does not match schema."""


class DAGError(WorkflowError):
    """DAG operation error."""


class TemplateNotFoundError(WorkflowError):
    """Workflow template not found."""


class RegistryError(WorkflowError):
    """Registry operation error."""


class SerializerError(WorkflowError):
    """Serialization/deserialization error."""


class LoaderError(WorkflowError):
    """Workflow loader error."""
