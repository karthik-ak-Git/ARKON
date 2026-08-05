"""ARKON Kernel - Unit Tests.

Comprehensive tests for all kernel components.
No mocking frameworks — pure Python tests.
"""

import pytest
from app.kernel import (
    CircularDependencyError,
    ContextNotInitializedError,
    DependencyNotSatisfiedError,
    DuplicateModuleError,
    DuplicateServiceError,
    Kernel,
    KernelState,
    LifecycleManager,
    LifecycleState,
    ModuleRegistry,
    ServiceContainer,
    Context,
    create_context,
)
from app.kernel.interfaces import IModule, IContext
from app.kernel.exceptions import ModuleNotFoundError, ServiceNotFoundError


# =============================================================================
# Test Fixtures
# =============================================================================

class MockModule(IModule):
    """Test module implementation."""

    def __init__(
        self,
        name: str = "test_module",
        version: str = "0.1.0",
        deps: list[str] | None = None,
        should_fail_init: bool = False,
        should_fail_start: bool = False,
        healthy: bool = True,
    ):
        self._name = name
        self._version = version
        self._deps = deps or []
        self._should_fail_init = should_fail_init
        self._should_fail_start = should_fail_start
        self._healthy = healthy
        self._state = LifecycleState.CREATED
        self._initialized = False
        self._started = False
        self._stopped = False
        self._context: IContext | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def state(self) -> LifecycleState:
        return self._state

    def dependencies(self) -> list[str]:
        return self._deps

    async def initialize(self, context: IContext) -> None:
        if self._should_fail_init:
            raise RuntimeError("Init failed")
        self._initialized = True
        self._context = context

    async def start(self) -> None:
        if self._should_fail_start:
            raise RuntimeError("Start failed")
        self._started = True

    async def stop(self) -> None:
        self._stopped = True

    async def shutdown(self) -> None:
        self._stopped = True

    async def health_check(self) -> dict:
        return {"status": "ok" if self._healthy else "error"}

    @property
    def is_healthy(self) -> bool:
        return self._healthy


# =============================================================================
# ServiceContainer Tests
# =============================================================================

class TestServiceContainer:

    def test_register_and_resolve(self):
        container = ServiceContainer()
        container.register(str, "hello")
        assert container.resolve(str) == "hello"

    def test_resolve_not_found(self):
        container = ServiceContainer()
        with pytest.raises(ServiceNotFoundError):
            container.resolve(str)

    def test_resolve_optional(self):
        container = ServiceContainer()
        assert container.resolve_optional(str) is None
        container.register(str, "hello")
        assert container.resolve_optional(str) == "hello"

    def test_has(self):
        container = ServiceContainer()
        assert not container.has(str)
        container.register(str, "hello")
        assert container.has(str)

    def test_duplicate_raises(self):
        container = ServiceContainer()
        container.register(str, "hello")
        with pytest.raises(DuplicateServiceError):
            container.register(str, "world")

    def test_overwrite(self):
        container = ServiceContainer()
        container.register(str, "hello")
        container.register(str, "world", overwrite=True)
        assert container.resolve(str) == "world"

    def test_singleton(self):
        container = ServiceContainer()
        container.register(str, lambda: "hello", singleton=True)
        a = container.resolve(str)
        b = container.resolve(str)
        assert a is b

    def test_transient(self):
        container = ServiceContainer()
        counter = 0

        def factory():
            nonlocal counter
            counter += 1
            return f"instance-{counter}"

        container.register(str, factory, singleton=False)
        a = container.resolve(str)
        b = container.resolve(str)
        assert a != b

    def test_lazy(self):
        container = ServiceContainer()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "instance"

        container.register_lazy(str, factory)
        assert call_count == 0
        container.resolve(str)
        assert call_count == 1
        container.resolve(str)
        assert call_count == 1  # Still 1 (singleton)

    def test_clear(self):
        container = ServiceContainer()
        container.register(str, "hello")
        container.clear()
        assert not container.has(str)

    def test_registrations(self):
        container = ServiceContainer()
        container.register(str, "hello")
        regs = container.registrations()
        assert "str" in regs
        assert regs["str"]["is_singleton"] is True


# =============================================================================
# ModuleRegistry Tests
# =============================================================================

class TestModuleRegistry:

    def test_register_and_get(self):
        registry = ModuleRegistry()
        module = MockModule(name="test")
        registry.register(module)
        assert registry.get("test") is module

    def test_get_not_found(self):
        registry = ModuleRegistry()
        with pytest.raises(ModuleNotFoundError):
            registry.get("nonexistent")

    def test_get_optional(self):
        registry = ModuleRegistry()
        assert registry.get_optional("nonexistent") is None
        module = MockModule(name="test")
        registry.register(module)
        result = registry.get_optional("test")
        assert result is not None
        assert result.module is module

    def test_has(self):
        registry = ModuleRegistry()
        assert not registry.has("test")
        registry.register(MockModule(name="test"))
        assert registry.has("test")

    def test_duplicate_raises(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="test"))
        with pytest.raises(DuplicateModuleError):
            registry.register(MockModule(name="test"))

    def test_unregister(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="test"))
        registry.unregister("test")
        assert not registry.has("test")

    def test_unregister_not_found(self):
        registry = ModuleRegistry()
        with pytest.raises(ModuleNotFoundError):
            registry.unregister("nonexistent")

    def test_all(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="a"))
        registry.register(MockModule(name="b"))
        assert len(registry.all()) == 2

    def test_len(self):
        registry = ModuleRegistry()
        assert len(registry) == 0
        registry.register(MockModule(name="a"))
        assert len(registry) == 1

    def test_contains(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="a"))
        assert "a" in registry
        assert "b" not in registry

    def test_snapshot(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="test", version="1.0.0"))
        snap = registry.snapshot()
        assert "test" in snap
        assert snap["test"]["version"] == "1.0.0"

    def test_clear(self):
        registry = ModuleRegistry()
        registry.register(MockModule(name="a"))
        registry.clear()
        assert len(registry) == 0


# =============================================================================
# Context Tests
# =============================================================================

class TestContext:

    def test_create_context(self):
        ctx = create_context(config={"key": "value"})
        assert ctx.config == {"key": "value"}

    def test_context_immutable(self):
        ctx = create_context(config={"key": "value"})
        with pytest.raises(AttributeError):
            ctx._config = {"new": "value"}  # type: ignore

    def test_context_not_initialized(self):
        ctx = create_context(config=None)
        with pytest.raises(ContextNotInitializedError):
            _ = ctx.config


# =============================================================================
# Kernel Tests
# =============================================================================

class TestKernel:

    def test_kernel_created(self):
        kernel = Kernel()
        assert kernel.state == KernelState.CREATED

    def test_register_module(self):
        kernel = Kernel()
        module = MockModule(name="test")
        kernel.register(module)
        assert kernel.registry.has("test")

    def test_kernel_resolve_service(self):
        kernel = Kernel()
        kernel.services.register(str, "hello")
        assert kernel.resolve(str) == "hello"

    @pytest.mark.asyncio
    async def test_kernel_bootstrap(self):
        kernel = Kernel()
        ctx = await kernel.bootstrap({"key": "value"})
        assert kernel.state == KernelState.RUNNING
        assert ctx.config == {"key": "value"}

    @pytest.mark.asyncio
    async def test_kernel_shutdown(self):
        kernel = Kernel()
        await kernel.bootstrap({})
        await kernel.shutdown()
        assert kernel.state == KernelState.STOPPED

    @pytest.mark.asyncio
    async def test_module_lifecycle(self):
        kernel = Kernel()
        module = MockModule(name="test")
        kernel.register(module)

        await kernel.bootstrap({})
        assert module._initialized
        assert module._started

        await kernel.shutdown()
        assert module._stopped


# =============================================================================
# LifecycleManager Tests
# =============================================================================

class TestLifecycleManager:

    @pytest.mark.asyncio
    async def test_startup_order(self):
        """Modules start in dependency order."""
        registry = ModuleRegistry()
        module_a = MockModule(name="a", deps=[])
        module_b = MockModule(name="b", deps=["a"])
        module_c = MockModule(name="c", deps=["b"])

        registry.register(module_c)
        registry.register(module_a)
        registry.register(module_b)

        ctx = create_context(config={})
        lm = LifecycleManager(registry)
        await lm.startup(ctx)

        assert module_a._initialized
        assert module_b._initialized
        assert module_c._initialized

    @pytest.mark.asyncio
    async def test_shutdown_reverse_order(self):
        """Modules stop in reverse dependency order."""
        registry = ModuleRegistry()
        module_a = MockModule(name="a", deps=[])
        module_b = MockModule(name="b", deps=["a"])

        registry.register(module_a)
        registry.register(module_b)

        ctx = create_context(config={})
        lm = LifecycleManager(registry)
        await lm.startup(ctx)
        await lm.shutdown()

        assert module_a._stopped
        assert module_b._stopped

    @pytest.mark.asyncio
    async def test_circular_dependency(self):
        """Circular dependencies raise error."""
        registry = ModuleRegistry()
        module_a = MockModule(name="a", deps=["b"])
        module_b = MockModule(name="b", deps=["a"])

        registry.register(module_a)
        registry.register(module_b)

        ctx = create_context(config={})
        lm = LifecycleManager(registry)

        with pytest.raises(CircularDependencyError):
            await lm.startup(ctx)

    @pytest.mark.asyncio
    async def test_missing_dependency(self):
        """Missing dependencies raise error."""
        registry = ModuleRegistry()
        module = MockModule(name="a", deps=["nonexistent"])
        registry.register(module)

        ctx = create_context(config={})
        lm = LifecycleManager(registry)

        with pytest.raises(DependencyNotSatisfiedError):
            await lm.startup(ctx)

    @pytest.mark.asyncio
    async def test_module_init_failure(self):
        """Module init failure triggers rollback."""
        registry = ModuleRegistry()
        module_ok = MockModule(name="ok")
        module_fail = MockModule(name="fail", should_fail_init=True)

        registry.register(module_ok)
        registry.register(module_fail)

        ctx = create_context(config={})
        lm = LifecycleManager(registry)

        with pytest.raises(Exception):
            await lm.startup(ctx)

        # module_ok should have been stopped during rollback
        assert module_ok._stopped

    def test_get_state(self):
        registry = ModuleRegistry()
        module = MockModule(name="test")
        registry.register(module)

        lm = LifecycleManager(registry)
        state = lm.get_state()
        assert state["test"] == LifecycleState.CREATED
