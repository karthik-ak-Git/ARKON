"""Tests for Resource Manager - Allocator."""

import pytest
from app.resources.allocator import ResourceAllocator
from app.resources.resource import Resource
from app.resources.interfaces import (
    AllocationStrategy,
    ResourceHealth,
    ResourceType,
)
from app.resources.exceptions import NoResourceAvailableError


@pytest.fixture
def resources():
    return [
        Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=6.0, health=ResourceHealth.HEALTHY),
        Resource(name="cpu-2", resource_type=ResourceType.CPU, capacity=8.0, available=4.0, health=ResourceHealth.HEALTHY),
        Resource(name="cpu-3", resource_type=ResourceType.CPU, capacity=16.0, available=14.0, health=ResourceHealth.HEALTHY),
        Resource(name="gpu-1", resource_type=ResourceType.GPU, capacity=24.0, available=20.0, health=ResourceHealth.HEALTHY),
    ]


class TestResourceAllocator:
    def test_best_fit(self, resources):
        allocator = ResourceAllocator()
        selected = allocator.allocate(resources, 3.0, ResourceType.CPU, AllocationStrategy.BEST_FIT)
        assert selected.name == "cpu-2"  # 4.0 available (closest fit for 3.0)
        assert selected.available == pytest.approx(1.0)
        assert selected.allocated == pytest.approx(3.0)

    def test_first_fit(self, resources):
        allocator = ResourceAllocator()
        selected = allocator.allocate(resources, 3.0, ResourceType.CPU, AllocationStrategy.FIRST_FIT)
        assert selected.name == "cpu-1"  # First CPU with enough available

    def test_priority(self, resources):
        resources[1].priority = 10  # cpu-2 highest priority
        allocator = ResourceAllocator()
        selected = allocator.allocate(resources, 3.0, ResourceType.CPU, AllocationStrategy.PRIORITY)
        assert selected.name == "cpu-2"

    def test_least_loaded(self, resources):
        resources[0].allocated = 10.0
        resources[1].allocated = 5.0
        resources[2].allocated = 2.0
        allocator = ResourceAllocator()
        selected = allocator.allocate(resources, 3.0, ResourceType.CPU, AllocationStrategy.LEAST_LOADED)
        assert selected.name == "cpu-3"  # Lowest allocated

    def test_no_resource_available(self):
        allocator = ResourceAllocator()
        resources = [
            Resource(name="cpu-1", resource_type=ResourceType.CPU, capacity=8.0, available=2.0),
        ]
        with pytest.raises(NoResourceAvailableError):
            allocator.allocate(resources, 5.0, ResourceType.CPU, AllocationStrategy.BEST_FIT)

    def test_excludes_unavailable(self, resources):
        resources[0].health = ResourceHealth.UNAVAILABLE
        allocator = ResourceAllocator()
        selected = allocator.allocate(resources, 3.0, ResourceType.CPU, AllocationStrategy.BEST_FIT)
        assert selected.name == "cpu-2"

    def test_tag_filtering(self, resources):
        resources[0].tags = ["cuda"]
        resources[1].tags = ["compute"]
        allocator = ResourceAllocator()
        selected = allocator.allocate(
            resources, 3.0, ResourceType.CPU,
            AllocationStrategy.BEST_FIT,
            tags=["cuda"],
        )
        assert selected.name == "cpu-1"

    def test_no_matching_type(self, resources):
        allocator = ResourceAllocator()
        with pytest.raises(NoResourceAvailableError):
            allocator.allocate(resources, 3.0, ResourceType.DISK, AllocationStrategy.BEST_FIT)
