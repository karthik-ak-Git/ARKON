"""Tests for DAG."""

import pytest
from app.workflow.dag import WorkflowDAG
from app.workflow.node import WorkflowNode
from app.workflow.edge import WorkflowEdge
from app.workflow.exceptions import CyclicDependencyError, DAGError


def _n(nid):
    return WorkflowNode(node_id=nid, name=nid, capability="test.cap")


class TestDAGConstruction:
    def test_empty_dag(self):
        g = WorkflowDAG()
        assert g.node_count == 0
        assert g.edge_count == 0

    def test_add_node(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        assert g.node_count == 1
        assert g.get_node("a") is not None

    def test_add_edge(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        e = WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b")
        g.add_edge(e)
        assert g.edge_count == 1

    def test_add_edge_missing_source(self):
        g = WorkflowDAG()
        g.add_node(_n("b"))
        e = WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b")
        with pytest.raises(DAGError):
            g.add_edge(e)

    def test_add_edge_missing_target(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        e = WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b")
        with pytest.raises(DAGError):
            g.add_edge(e)


class TestDAGQueries:
    def _linear_dag(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_node(_n("c"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        return g

    def test_get_node(self):
        g = self._linear_dag()
        assert g.get_node("a").name == "a"
        assert g.get_node("x") is None

    def test_get_children(self):
        g = self._linear_dag()
        assert g.get_children("a") == ["b"]
        assert g.get_children("c") == []

    def test_get_parents(self):
        g = self._linear_dag()
        assert g.get_parents("b") == ["a"]
        assert g.get_parents("a") == []

    def test_get_roots(self):
        g = self._linear_dag()
        assert g.get_roots() == ["a"]

    def test_get_leaves(self):
        g = self._linear_dag()
        assert g.get_leaves() == ["c"]

    def test_remove_node(self):
        g = self._linear_dag()
        g.remove_node("b")
        assert g.node_count == 2
        assert g.get_node("b") is None
        assert g.edge_count == 0

    def test_remove_node_cascades_edges(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_node(_n("c"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        g.remove_node("b")
        assert g.edge_count == 0

    def test_get_nodes(self):
        g = self._linear_dag()
        assert len(g.get_nodes()) == 3

    def test_get_edges(self):
        g = self._linear_dag()
        assert len(g.get_edges()) == 2


class TestTopologicalSort:
    def test_linear_chain(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_node(_n("c"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        order = g.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_diamond(self):
        g = WorkflowDAG()
        for nid in ["a", "b", "c", "d"]:
            g.add_node(_n(nid))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="a", target_node_id="c"))
        g.add_edge(WorkflowEdge(edge_id="e3", source_node_id="b", target_node_id="d"))
        g.add_edge(WorkflowEdge(edge_id="e4", source_node_id="c", target_node_id="d"))
        order = g.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_cycle_detection(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="a"))
        with pytest.raises(CyclicDependencyError):
            g.topological_sort()

    def test_has_cycle(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="a"))
        assert g.has_cycle() is True

    def test_no_cycle(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        assert g.has_cycle() is False


class TestDAGValidation:
    def test_empty_dag_valid(self):
        g = WorkflowDAG()
        errors = g.validate_dag()
        assert errors == []

    def test_single_node_valid(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        errors = g.validate_dag()
        assert errors == []

    def test_linear_chain_valid(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        errors = g.validate_dag()
        assert errors == []

    def test_cycle_in_validation(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="a"))
        errors = g.validate_dag()
        assert len(errors) > 0


class TestDAGCriticalPath:
    def test_linear_critical_path(self):
        g = WorkflowDAG()
        for nid in ["a", "b", "c"]:
            g.add_node(_n(nid))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        path = g.get_critical_path()
        assert path == ["a", "b", "c"]

    def test_empty_dag_critical_path(self):
        g = WorkflowDAG()
        assert g.get_critical_path() == []

    def test_single_node_critical_path(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        assert g.get_critical_path() == ["a"]


class TestDAGDescendants:
    def test_all_descendants(self):
        g = WorkflowDAG()
        for nid in ["a", "b", "c", "d"]:
            g.add_node(_n(nid))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        g.add_edge(WorkflowEdge(edge_id="e3", source_node_id="a", target_node_id="d"))
        desc = g.get_all_descendants("a")
        assert desc == {"b", "c", "d"}

    def test_all_ancestors(self):
        g = WorkflowDAG()
        for nid in ["a", "b", "c"]:
            g.add_node(_n(nid))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        g.add_edge(WorkflowEdge(edge_id="e2", source_node_id="b", target_node_id="c"))
        anc = g.get_all_ancestors("c")
        assert anc == {"a", "b"}


class TestDAGToDict:
    def test_to_dict(self):
        g = WorkflowDAG()
        g.add_node(_n("a"))
        g.add_node(_n("b"))
        g.add_edge(WorkflowEdge(edge_id="e1", source_node_id="a", target_node_id="b"))
        d = g.to_dict()
        assert len(d["nodes"]) == 2
        assert len(d["edges"]) == 1
