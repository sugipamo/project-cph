"""Tests for node operations module."""
from unittest.mock import Mock

import pytest

from src.workflow.builder.node_operations import (
    NodeInfo,
    NodeState,
    calculate_completion_statistics,
    calculate_node_priority,
    create_node_batch,
    create_node_state,
    filter_executable_nodes,
    group_nodes_by_status,
    is_node_executable,
    mark_dependent_nodes_skipped,
    update_node_status,
    validate_node_states,
)


class TestNodeState:
    """Test NodeState dataclass."""

    def test_init_basic(self):
        state = NodeState(
            node_id="n1",
            status="pending",
            allow_failure=False,
            result=None
        )

        assert state.node_id == "n1"
        assert state.status == "pending"
        assert state.allow_failure is False
        assert state.result is None

    def test_with_status(self):
        original = NodeState(node_id="n1", status="pending")
        updated = original.with_status("running")

        # Original unchanged
        assert original.status == "pending"

        # New instance with updated status
        assert updated.status == "running"
        assert updated.node_id == "n1"

    def test_with_result(self):
        original = NodeState(node_id="n1", status="pending")
        result = {"data": "value"}
        updated = original.with_result(result)

        # Original unchanged
        assert original.result is None

        # New instance with result
        assert updated.result == result
        assert updated.node_id == "n1"
        assert updated.status == "pending"

    def test_immutability(self):
        state = NodeState(node_id="n1", status="pending")

        with pytest.raises(AttributeError):
            state.status = "running"


class TestNodeInfo:
    """Test NodeInfo dataclass."""

    def test_init_complete(self):
        info = NodeInfo(
            id="n1",
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"file2.txt"},
            requires_dirs={"dir2"},
            metadata={"type": "test"}
        )

        assert info.id == "n1"
        assert info.creates_files == {"file1.txt"}
        assert info.metadata == {"type": "test"}

    def test_from_request_node_complete(self):
        mock_node = Mock()
        mock_node.id = "test_node"
        mock_node.creates_files = {"file1.txt", "file2.txt"}
        mock_node.creates_dirs = {"dir1"}
        mock_node.reads_files = {"file3.txt"}
        mock_node.requires_dirs = {"dir2"}
        mock_node.metadata = {"type": "mock", "priority": 1}

        info = NodeInfo.from_request_node(mock_node)

        assert info.id == "test_node"
        assert info.creates_files == {"file1.txt", "file2.txt"}
        assert info.creates_dirs == {"dir1"}
        assert info.reads_files == {"file3.txt"}
        assert info.requires_dirs == {"dir2"}
        assert info.metadata == {"type": "mock", "priority": 1}

    def test_from_request_node_missing_attributes(self):
        # Create node with only id attribute
        mock_node = type('MinimalNode', (), {'id': 'minimal_node'})()

        info = NodeInfo.from_request_node(mock_node)

        assert info.id == "minimal_node"
        assert info.creates_files == set()
        assert info.creates_dirs == set()
        assert info.reads_files == set()
        assert info.requires_dirs == set()
        assert info.metadata == {}


class TestNodeOperations:
    """Test node operation functions."""

    def test_create_node_state_default(self):
        state = create_node_state("n1")

        assert state.node_id == "n1"
        assert state.status == "pending"
        assert state.allow_failure is False
        assert state.result is None

    def test_create_node_state_custom(self):
        result = {"success": True}
        state = create_node_state(
            node_id="n2",
            status="completed",
            allow_failure=True,
            result=result
        )

        assert state.node_id == "n2"
        assert state.status == "completed"
        assert state.allow_failure is True
        assert state.result == result

    def test_update_node_status_no_result(self):
        original = create_node_state("n1", "pending")
        updated = update_node_status(original, "running")

        assert updated.status == "running"
        assert updated.node_id == "n1"
        assert updated.result is None

    def test_update_node_status_with_result(self):
        original = create_node_state("n1", "pending")
        result = {"error": "timeout"}
        updated = update_node_status(original, "failed", result)

        assert updated.status == "failed"
        assert updated.result == result

    def test_is_node_executable_pending_no_deps(self):
        state = create_node_state("n1", "pending")
        failed_nodes = set()
        dependencies = set()

        assert is_node_executable(state, failed_nodes, dependencies) is True

    def test_is_node_executable_non_pending(self):
        state = create_node_state("n1", "running")
        failed_nodes = set()
        dependencies = set()

        assert is_node_executable(state, failed_nodes, dependencies) is False

    def test_is_node_executable_failed_dependency(self):
        state = create_node_state("n1", "pending")
        failed_nodes = {"n0"}
        dependencies = {"n0"}  # Dependency failed

        assert is_node_executable(state, failed_nodes, dependencies) is False

    def test_is_node_executable_no_failed_deps(self):
        state = create_node_state("n1", "pending")
        failed_nodes = {"n3"}
        dependencies = {"n0", "n2"}  # Dependencies OK

        assert is_node_executable(state, failed_nodes, dependencies) is True

    def test_mark_dependent_nodes_skipped(self):
        node_states = {
            "n1": create_node_state("n1", "failed"),
            "n2": create_node_state("n2", "pending"),
            "n3": create_node_state("n3", "pending"),
            "n4": create_node_state("n4", "completed"),
            "n5": create_node_state("n5", "pending")
        }

        # n1 -> n2 -> n3, n1 -> n5
        adjacency_list = {
            "n1": {"n2", "n5"},
            "n2": {"n3"},
            "n3": set(),
            "n4": set(),
            "n5": set()
        }

        updated = mark_dependent_nodes_skipped(node_states, adjacency_list, "n1")

        assert updated["n1"].status == "failed"  # Unchanged
        assert updated["n2"].status == "skipped"  # Dependent on n1
        assert updated["n3"].status == "skipped"  # Dependent on n2 (recursive)
        assert updated["n4"].status == "completed"  # Unchanged
        assert updated["n5"].status == "skipped"  # Dependent on n1

    def test_filter_executable_nodes(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n2": create_node_state("n2", "pending"),
            "n3": create_node_state("n3", "running"),
            "n4": create_node_state("n4", "pending"),
            "n5": create_node_state("n5", "pending")
        }

        failed_nodes = {"n0"}  # n0 failed

        # Dependencies: n1->[], n2->[n0], n3->[], n4->[n1], n5->[n0, n1]
        reverse_adjacency_list = {
            "n1": set(),
            "n2": {"n0"},  # Depends on failed node
            "n3": set(),
            "n4": {"n1"},
            "n5": {"n0", "n1"}  # Depends on failed node
        }

        executable = filter_executable_nodes(node_states, failed_nodes, reverse_adjacency_list)

        # Only n1 and n4 should be executable
        # n1: pending, no failed deps
        # n2: pending, but depends on failed n0
        # n3: running (not pending)
        # n4: pending, depends on n1 (not failed)
        # n5: pending, but depends on failed n0
        assert set(executable) == {"n1", "n4"}

    def test_calculate_node_priority(self):
        # Basic node
        node_info = NodeInfo(
            id="n1",
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set(),
            metadata={}
        )

        priority = calculate_node_priority(node_info, dependents_count=2)
        assert priority == 20  # 2 * 10

        # Critical path node
        priority = calculate_node_priority(node_info, dependents_count=1, critical_path_member=True)
        assert priority == 110  # 1 * 10 + 100

        # Resource creating node
        resource_node = NodeInfo(
            id="n2",
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files=set(),
            requires_dirs=set(),
            metadata={}
        )
        priority = calculate_node_priority(resource_node, dependents_count=0)
        assert priority == 50  # 0 + 50

        # File reading only node
        reader_node = NodeInfo(
            id="n3",
            creates_files=set(),
            creates_dirs=set(),
            reads_files={"file1.txt"},
            requires_dirs=set(),
            metadata={}
        )
        priority = calculate_node_priority(reader_node, dependents_count=0)
        assert priority == -20  # 0 - 20

    def test_group_nodes_by_status(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n2": create_node_state("n2", "pending"),
            "n3": create_node_state("n3", "running"),
            "n4": create_node_state("n4", "completed"),
            "n5": create_node_state("n5", "failed")
        }

        groups = group_nodes_by_status(node_states)

        assert set(groups["pending"]) == {"n1", "n2"}
        assert groups["running"] == ["n3"]
        assert groups["completed"] == ["n4"]
        assert groups["failed"] == ["n5"]

    def test_calculate_completion_statistics(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n2": create_node_state("n2", "pending"),
            "n3": create_node_state("n3", "running"),
            "n4": create_node_state("n4", "completed"),
            "n5": create_node_state("n5", "failed"),
            "n6": create_node_state("n6", "skipped")
        }

        stats = calculate_completion_statistics(node_states)

        assert stats["total"] == 6
        assert stats["pending"] == 2
        assert stats["running"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["skipped"] == 1

    def test_calculate_completion_statistics_empty(self):
        stats = calculate_completion_statistics({})

        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["skipped"] == 0

    def test_validate_node_states_valid(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n2": create_node_state("n2", "completed")
        }
        all_node_ids = {"n1", "n2"}

        errors = validate_node_states(node_states, all_node_ids)
        assert errors == []

    def test_validate_node_states_invalid(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n3": create_node_state("n3", "invalid_status")  # Invalid status
        }
        all_node_ids = {"n1", "n2"}  # n2 missing, n3 extra

        errors = validate_node_states(node_states, all_node_ids)

        assert len(errors) == 3
        assert any("Missing node states" in e and "n2" in e for e in errors)
        assert any("Extra node states" in e and "n3" in e for e in errors)
        assert any("Invalid status for n3" in e for e in errors)

    def test_create_node_batch_empty(self):
        batches = create_node_batch({}, [])
        assert batches == []

    def test_create_node_batch_single_batch(self):
        node_states = {
            "n1": create_node_state("n1", "pending"),
            "n2": create_node_state("n2", "pending"),
            "n3": create_node_state("n3", "running")  # Not pending
        }

        batch_nodes = ["n1", "n2", "n3"]
        batches = create_node_batch(node_states, batch_nodes, max_batch_size=5)

        assert len(batches) == 1
        assert set(batches[0]) == {"n1", "n2"}  # Only pending nodes

    def test_create_node_batch_multiple_batches(self):
        node_states = {
            f"n{i}": create_node_state(f"n{i}", "pending")
            for i in range(1, 8)  # n1 to n7
        }

        batch_nodes = [f"n{i}" for i in range(1, 8)]
        batches = create_node_batch(node_states, batch_nodes, max_batch_size=3)

        assert len(batches) == 3  # 7 nodes / 3 = 3 batches
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1

        # All nodes should be included
        all_batched = []
        for batch in batches:
            all_batched.extend(batch)
        assert set(all_batched) == {f"n{i}" for i in range(1, 8)}

    def test_create_node_batch_unknown_nodes(self):
        node_states = {
            "n1": create_node_state("n1", "pending")
        }

        batch_nodes = ["n1", "n2", "n3"]  # n2, n3 not in node_states
        batches = create_node_batch(node_states, batch_nodes)

        assert len(batches) == 1
        assert batches[0] == ["n1"]  # Only known pending node
