"""Plugin system — operating-system-level plugin runtime for ARKON."""

from app.plugins.interfaces import (
    PluginState,
    CapabilityType,
    PermissionType,
    DependencyType,
    IsolationLevel,
    PluginEventType,
    PluginPriority,
    PluginManifest,
    PluginInfo,
    PluginRegistration,
    PluginDependency,
    PluginCapability,
    PluginAgent,
    PluginCommand,
    PluginWorkflowNode,
    PluginUIExtension,
    PluginSetting,
    PluginPermission,
    PluginResource,
    PluginModel,
    PluginStorage,
)
from app.plugins.exceptions import (
    PluginError,
    ManifestError,
    ManifestNotFoundError,
    ManifestValidationError,
    ManifestParseError,
    PluginNotFoundError,
    PluginAlreadyInstalledError,
    PluginInstallError,
    PluginNotInstalledError,
    PluginNotLoadedError,
    PluginLoadError,
    PluginStartError,
    PluginStopError,
    PluginFailedError,
    DependencyError,
    DependencyNotFoundError,
    DependencyCycleError,
    DependencyConflictError,
    DependencyResolutionError,
    PermissionNotGrantedError,
    SandboxError,
    SandboxViolationError,
    IsolationError,
    VersionError,
    VersionMismatchError,
    CompatibilityError,
)
from app.plugins.runtime import PluginRuntime
from app.plugins.manager import PluginManager
from app.plugins.registry import PluginRegistry
from app.plugins.lifecycle import PluginStateMachine
from app.plugins.manifest import parse_manifest, validate_manifest
from app.plugins.versioning import SemanticVersion, satisfies, is_compatible
from app.plugins.dependency import DependencyGraph
from app.plugins.resolver import DependencyResolver
from app.plugins.permissions import PermissionManager
from app.plugins.isolation import IsolationManager
from app.plugins.sandbox import PluginSandbox, SandboxConfig
from app.plugins.loader import PluginLoader
from app.plugins.installer import PluginInstaller
from app.plugins.uninstaller import PluginUninstaller
from app.plugins.updater import PluginUpdater
from app.plugins.marketplace import PluginMarketplace
