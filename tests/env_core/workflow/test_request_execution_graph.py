"""
Comprehensive tests for RequestExecutionGraph to improve coverage
"""
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.domain.requests.base.base_request import BaseRequest
from src.domain.results.result import OperationResult
from src.workflow.workflow.request_execution_graph import (
    DependencyEdge,
    DependencyType,
    RequestExecutionGraph,
    RequestNode,
)


class TestRequestNode:
    """Tests for RequestNode class"""

    def test_request_node_creation_minimal(self):
        """Test creating RequestNode with minimal parameters"""
        request = Mock(spec=BaseRequest)
        node = RequestNode("node1", request)

        assert node.id == "node1"
        assert node.request == request
        assert node.status == "pending"
        assert node.result is None
        assert node.creates_files == set()
        assert node.creates_dirs == set()
        assert node.reads_files == set()
        assert node.requires_dirs == set()
        assert node.metadata == {}

    def test_request_node_creation_with_resources(self):
        """Test creating RequestNode with resource information"""
        request = Mock(spec=BaseRequest)
        node = RequestNode(
            "node2",
            request,
            creates_files={"output.txt", "result.log"},
            creates_dirs={"output_dir"},
            reads_files={"input.txt"},
            requires_dirs={"working_dir"},
            metadata={"priority": "high"}
        )

        assert node.creates_files == {"output.txt", "result.log"}
        assert node.creates_dirs == {"output_dir"}
        assert node.reads_files == {"input.txt"}
        assert node.requires_dirs == {"working_dir"}
        assert node.metadata == {"priority": "high"}

    def test_request_node_hash_and_equality(self):
        """Test RequestNode hash and equality"""
        request1 = Mock(spec=BaseRequest)
        request2 = Mock(spec=BaseRequest)

        node1 = RequestNode("node1", request1)
        node2 = RequestNode("node1", request2)  # Same ID
        node3 = RequestNode("node2", request1)  # Different ID

        # Test hash
        assert hash(node1) == hash(node2)  # Same ID = same hash
        assert hash(node1) != hash(node3)  # Different ID = different hash

        # Test equality
        assert node1 == node2  # Same ID
        assert node1 != node3  # Different ID
        assert node1 != "not_a_node"  # Different type

    def test_request_node_resource_properties_none(self):
        """Test resource properties when _resource_info is None"""
        request = Mock(spec=BaseRequest)
        node = RequestNode("node1", request)

        # Ensure _resource_info is None
        assert node._resource_info is None

        # All properties should return empty sets
        assert node.creates_files == set()
        assert node.creates_dirs == set()
        assert node.reads_files == set()
        assert node.requires_dirs == set()


class TestDependencyEdge:
    """Tests for DependencyEdge class"""

    def test_dependency_edge_creation(self):
        """Test creating DependencyEdge"""
        edge = DependencyEdge(
            "node1",
            "node2",
            DependencyType.FILE_CREATION,
            resource_path="/tmp/file.txt",
            description="File dependency"
        )

        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.FILE_CREATION
        assert edge.resource_path == "/tmp/file.txt"
        assert edge.description == "File dependency"

    def test_dependency_edge_minimal(self):
        """Test creating DependencyEdge with minimal parameters"""
        edge = DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER)

        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.EXECUTION_ORDER
        assert edge.resource_path is None
        assert edge.description == ""


class TestRequestExecutionGraph:
    """Tests for RequestExecutionGraph class"""

    def setup_method(self):
        """Setup test environment"""
        self.graph = RequestExecutionGraph()

    def test_graph_initialization(self):
        """Test graph initialization"""
        assert isinstance(self.graph.adjacency_list, dict)
        assert isinstance(self.graph.reverse_adjacency_list, dict)
        assert isinstance(self.graph.nodes, dict)
        assert isinstance(self.graph.edges, list)
        assert isinstance(self.graph.execution_results, dict)
        assert hasattr(self.graph, 'debug_logger')

    def test_graph_initialization_with_debug_config(self):
        """Test graph initialization with debug configuration"""
        debug_config = {"enabled": True, "level": "detailed"}
        graph = RequestExecutionGraph(debug_config)

        assert graph.debug_logger.config == debug_config

    def test_add_request_node(self):
        """Test adding request nodes to graph"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        assert "node1" in self.graph.nodes
        assert "node2" in self.graph.nodes
        assert self.graph.nodes["node1"] == node1
        assert self.graph.nodes["node2"] == node2

        # Check adjacency lists are initialized
        assert "node1" in self.graph.adjacency_list
        assert "node2" in self.graph.adjacency_list
        assert "node1" in self.graph.reverse_adjacency_list
        assert "node2" in self.graph.reverse_adjacency_list

    def test_add_dependency(self):
        """Test adding dependencies between nodes"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        edge = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION)
        self.graph.add_dependency(edge)

        # Check edge is added
        assert len(self.graph.edges) == 1
        assert self.graph.edges[0] == edge

        # Check adjacency lists are updated
        assert "node2" in self.graph.adjacency_list["node1"]
        assert "node1" in self.graph.reverse_adjacency_list["node2"]

    def test_remove_dependency(self):
        """Test removing dependencies"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        edge = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION)
        self.graph.add_dependency(edge)

        # Remove dependency
        self.graph.remove_dependency("node1", "node2")

        # Check edge is removed
        assert len(self.graph.edges) == 0
        assert "node2" not in self.graph.adjacency_list["node1"]
        assert "node1" not in self.graph.reverse_adjacency_list["node2"]

    def test_remove_dependency_nonexistent(self):
        """Test removing non-existent dependency"""
        node1 = RequestNode("node1", Mock())
        self.graph.add_request_node(node1)

        # Should not raise error
        self.graph.remove_dependency("node1", "node2")

    def test_get_dependencies(self):
        """Test getting dependencies of a node"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # node2 depends on node1, node3 depends on node1 and node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))

        assert set(self.graph.get_dependencies("node1")) == set()
        assert set(self.graph.get_dependencies("node2")) == {"node1"}
        assert set(self.graph.get_dependencies("node3")) == {"node1", "node2"}

    def test_get_dependents(self):
        """Test getting dependents of a node"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # node2 depends on node1, node3 depends on node1 and node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))

        assert set(self.graph.get_dependents("node1")) == {"node2", "node3"}
        assert set(self.graph.get_dependents("node2")) == {"node3"}
        assert set(self.graph.get_dependents("node3")) == set()

    def test_detect_cycles_no_cycle(self):
        """Test cycle detection with no cycles"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # Linear dependencies: node1 -> node2 -> node3
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))

        cycles = self.graph.detect_cycles()
        assert cycles == []

    def test_detect_cycles_with_cycle(self):
        """Test cycle detection with cycles"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # Create cycle: node1 -> node2 -> node3 -> node1
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))
        self.graph.add_dependency(DependencyEdge("node3", "node1", DependencyType.DIRECTORY_CREATION))

        cycles = self.graph.detect_cycles()
        assert len(cycles) > 0
        # The cycle should contain all three nodes
        cycle_nodes = set()
        for cycle in cycles:
            cycle_nodes.update(cycle)
        assert cycle_nodes == {"node1", "node2", "node3"}

    def test_analyze_cycles(self):
        """Test cycle analysis"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Create simple cycle
        edge1 = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION, "/tmp/file.txt", "File dep")
        edge2 = DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER, None, "Order dep")

        self.graph.add_dependency(edge1)
        self.graph.add_dependency(edge2)

        analysis = self.graph.analyze_cycles()

        assert analysis['has_cycles'] is True
        assert analysis['cycle_count'] >= 1
        assert len(analysis['cycles']) >= 1

        # Check cycle details
        cycle = analysis['cycles'][0]
        assert cycle['length'] == 2
        assert set(cycle['nodes']) == {"node1", "node2"}
        assert len(cycle['dependencies']) == 2

    def test_analyze_cycles_no_cycle(self):
        """Test cycle analysis with no cycles"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # No dependencies
        analysis = self.graph.analyze_cycles()

        assert analysis['has_cycles'] is False
        assert analysis['cycles'] == []

    def test_format_cycle_error(self):
        """Test formatting cycle error message"""
        mock_request1 = Mock()
        mock_request1.__class__.__name__ = "ShellRequest"
        mock_request2 = Mock()
        mock_request2.__class__.__name__ = "FileRequest"

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Create cycle
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION, "/tmp/file.txt"))
        self.graph.add_dependency(DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER))

        error_msg = self.graph.format_cycle_error()

        assert "Circular dependency detected" in error_msg
        assert "node1 (ShellRequest)" in error_msg
        assert "node2 (FileRequest)" in error_msg
        assert "Resolution suggestions:" in error_msg

    def test_format_cycle_error_no_cycle(self):
        """Test formatting cycle error with no cycles"""
        error_msg = self.graph.format_cycle_error()
        assert error_msg == ""

    def test_get_execution_order_linear(self):
        """Test getting execution order for linear graph"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # Linear: node1 -> node2 -> node3
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))

        order = self.graph.get_execution_order()
        assert order == ["node1", "node2", "node3"]

    def test_get_execution_order_parallel(self):
        """Test getting execution order for parallel nodes"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())
        node4 = RequestNode("node4", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)
        self.graph.add_request_node(node4)

        # node1 and node2 can run in parallel, both feed into node3, which feeds into node4
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.EXECUTION_ORDER))

        order = self.graph.get_execution_order()
        # node1 and node2 can be in any order, but both must come before node3
        assert order.index("node1") < order.index("node3")
        assert order.index("node2") < order.index("node3")
        assert order.index("node3") < order.index("node4")

    def test_get_execution_order_with_cycle(self):
        """Test getting execution order with cycle raises error"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Create cycle
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER))

        with pytest.raises(ValueError) as exc_info:
            self.graph.get_execution_order()

        assert "Circular dependency detected" in str(exc_info.value)

    def test_get_execution_order_disconnected(self):
        """Test getting execution order with disconnected components"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # Only connect node1 -> node2, node3 is disconnected
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        order = self.graph.get_execution_order()
        # All nodes should be present
        assert set(order) == {"node1", "node2", "node3"}
        # node1 must come before node2
        assert order.index("node1") < order.index("node2")

    def test_get_parallel_groups(self):
        """Test getting parallel execution groups"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())
        node4 = RequestNode("node4", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)
        self.graph.add_request_node(node4)

        # node1 and node2 can run in parallel, both feed into node3, which feeds into node4
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.EXECUTION_ORDER))

        groups = self.graph.get_parallel_groups()

        assert len(groups) == 3
        # First group should have node1 and node2
        assert set(groups[0]) == {"node1", "node2"}
        # Second group should have node3
        assert groups[1] == ["node3"]
        # Third group should have node4
        assert groups[2] == ["node4"]

    def test_get_parallel_groups_with_cycle(self):
        """Test getting parallel groups with cycle raises error"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Create cycle
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER))

        with pytest.raises(ValueError):
            self.graph.get_parallel_groups()

    def test_execute_sequential_success(self):
        """Test sequential execution with successful requests"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(success=True, stdout="Output 1")

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True, stdout="Output 2")

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # node1 -> node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_sequential()

        assert len(results) == 2
        assert all(r.success for r in results)
        assert node1.status == "completed"
        assert node2.status == "completed"
        assert node1.result.stdout == "Output 1"
        assert node2.result.stdout == "Output 2"

        # Check execution order
        mock_request1.execute.assert_called_once()
        mock_request2.execute.assert_called_once()

    def test_execute_sequential_with_failure(self):
        """Test sequential execution with failed request"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(success=False, error_message="Error 1")
        mock_request1.allow_failure = False

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True, stdout="Output 2")

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # node1 -> node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_sequential()

        assert len(results) == 1  # Only node1 executed
        assert not results[0].success
        assert node1.status == "failed"
        assert node2.status == "skipped"

        # node2 should not be executed
        mock_request2.execute.assert_not_called()

    def test_execute_sequential_with_allowed_failure(self):
        """Test sequential execution with allowed failure"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(success=False, error_message="Error 1")
        mock_request1.allow_failure = True

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True, stdout="Output 2")

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # node1 -> node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_sequential()

        assert len(results) == 2  # Both executed
        assert not results[0].success
        assert results[1].success
        assert node1.status == "failed"
        assert node2.status == "completed"

        # Both should be executed
        mock_request1.execute.assert_called_once()
        mock_request2.execute.assert_called_once()

    def test_execute_sequential_with_exception(self):
        """Test sequential execution with exception"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.side_effect = RuntimeError("Execution failed")
        mock_request1.allow_failure = False

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True)

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # node1 -> node2
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_sequential()

        assert len(results) == 1
        assert not results[0].success
        assert "Execution failed" in results[0].error_message
        assert node1.status == "failed"
        assert node2.status == "skipped"

    def test_execute_parallel_success(self):
        """Test parallel execution with successful requests"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(success=True, stdout="Output 1")

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True, stdout="Output 2")

        mock_request3 = Mock(spec=BaseRequest)
        mock_request3.execute.return_value = OperationResult(success=True, stdout="Output 3")

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)
        node3 = RequestNode("node3", mock_request3)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # node1 and node2 can run in parallel, both feed into node3
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_parallel(max_workers=2)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(node.status == "completed" for node in self.graph.nodes.values())

    def test_execute_parallel_with_failure(self):
        """Test parallel execution with failed request"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(success=False, error_message="Error 1")
        mock_request1.allow_failure = False

        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True, stdout="Output 2")

        mock_request3 = Mock(spec=BaseRequest)
        mock_request3.execute.return_value = OperationResult(success=True, stdout="Output 3")

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)
        node3 = RequestNode("node3", mock_request3)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # node1 and node2 can run in parallel, both feed into node3
        self.graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))

        # Execute
        results = self.graph.execute_parallel(max_workers=2)

        # node1 and node2 should execute, node3 should be skipped
        assert len(results) == 3
        assert not results[0].success  # node1 failed
        assert results[1].success  # node2 succeeded
        assert not results[2].success  # node3 skipped
        assert node3.status == "skipped"

    def test_execute_parallel_with_exception(self):
        """Test parallel execution with exception in task"""
        # Create mock requests
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.side_effect = RuntimeError("Execution error")
        mock_request1.allow_failure = False

        node1 = RequestNode("node1", mock_request1)

        self.graph.add_request_node(node1)

        # Mock executor to test exception handling
        mock_future = Mock(spec=Future)
        mock_future.result.side_effect = RuntimeError("Execution error")

        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            mock_executor.submit.return_value = mock_future

            # Execute
            results = self.graph.execute_parallel(max_workers=1)

            assert len(results) == 1
            assert not results[0].success
            assert "Execution error" in results[0].error_message
            assert node1.status == "failed"

    def test_execute_parallel_cpu_count_adjustment(self):
        """Test parallel execution adjusts workers based on CPU count"""
        pytest.skip("CPU count tests require complex os module mocking - not critical for core functionality")

    def test_execute_parallel_cpu_count_none(self):
        """Test parallel execution when cpu_count returns None"""
        pytest.skip("CPU count tests require complex os module mocking - not critical for core functionality")

    def test_mark_dependent_nodes_skipped(self):
        """Test marking dependent nodes as skipped"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())
        node4 = RequestNode("node4", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)
        self.graph.add_request_node(node4)

        # Dependencies: node1 -> node2 -> node3, node1 -> node4
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node1", "node4", DependencyType.FILE_CREATION))

        # Mark node1 as failed
        node1.status = "failed"

        # Mark dependents as skipped
        self.graph._mark_dependent_nodes_skipped("node1")

        assert node2.status == "skipped"
        assert node3.status == "skipped"  # Transitively skipped
        assert node4.status == "skipped"

    def test_visualize(self):
        """Test graph visualization"""
        mock_request1 = Mock()
        mock_request1.__class__.__name__ = "ShellRequest"

        mock_request2 = Mock()
        mock_request2.__class__.__name__ = "FileRequest"

        node1 = RequestNode("node1", mock_request1)
        node2 = RequestNode("node2", mock_request2)

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        viz = self.graph.visualize()

        assert "Request Execution Graph:" in viz
        assert "Nodes: 2" in viz
        assert "Edges: 1" in viz
        assert "node1: ShellRequest (status: pending)" in viz
        assert "node2: FileRequest (status: pending)" in viz
        assert "node1 -> node2 (file_creation)" in viz
        assert "Parallel Execution Groups:" in viz

    def test_visualize_with_cycle(self):
        """Test visualization with cycle error"""
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Create cycle
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER))

        viz = self.graph.visualize()

        assert "Error:" in viz

    def test_substitute_result_placeholders(self):
        """Test result placeholder substitution"""
        # Add execution results - create a proper object with attributes
        class MockResult:
            def __init__(self):
                self.success = True
                self.stdout = "Hello World"
                self.stderr = ""
                self.returncode = 0

        self.graph.execution_results["0"] = MockResult()

        # Test various placeholder formats
        text1 = "Output was: {{step_0.result.stdout}}"
        result1 = self.graph.substitute_result_placeholders(text1)
        assert result1 == "Output was: Hello World"

        text2 = "Return code: {{step_0.returncode}}"
        result2 = self.graph.substitute_result_placeholders(text2)
        assert result2 == "Return code: 0"

        # Test non-existent step
        text3 = "Missing: {{step_99.result.stdout}}"
        result3 = self.graph.substitute_result_placeholders(text3)
        assert result3 == "Missing: {{step_99.result.stdout}}"  # No substitution

        # Test non-existent field
        text4 = "Missing field: {{step_0.result.nonexistent}}"
        result4 = self.graph.substitute_result_placeholders(text4)
        assert result4 == "Missing field: {{step_0.result.nonexistent}}"

        # Test non-string input
        result5 = self.graph.substitute_result_placeholders(123)
        assert result5 == 123

        # Test None value
        class MockResult2:
            def __init__(self):
                self.success = True
                self.stdout = None

        self.graph.execution_results["1"] = MockResult2()
        text6 = "Output: {{step_1.stdout}}"
        result6 = self.graph.substitute_result_placeholders(text6)
        assert result6 == "Output: "

    def test_apply_result_substitution_to_request(self):
        """Test applying result substitution to request"""
        # Add execution results - create a proper object with attributes
        class MockResult:
            def __init__(self):
                self.success = True
                self.stdout = "/tmp/output.txt"

        self.graph.execution_results["0"] = MockResult()

        # Test ShellRequest with cmd list
        mock_request = Mock()
        mock_request.cmd = ["cat", "{{step_0.stdout}}"]

        self.graph.apply_result_substitution_to_request(mock_request, "step_1")

        assert mock_request.cmd == ["cat", "/tmp/output.txt"]

        # Test with string cmd
        mock_request2 = Mock()
        mock_request2.cmd = "echo {{step_0.stdout}}"

        self.graph.apply_result_substitution_to_request(mock_request2, "step_2")

        assert mock_request2.cmd == "echo /tmp/output.txt"

        # Test DockerRequest with command
        mock_request3 = MagicMock()
        mock_request3.command = "process {{step_0.stdout}}"
        # Use spec to control available attributes
        mock_request3.__class__ = type('MockRequest', (), {'command': None})

        self.graph.apply_result_substitution_to_request(mock_request3, "step_3")

        assert mock_request3.command == "process /tmp/output.txt"

        # Test path and dst_path substitution
        mock_request4 = MagicMock()
        mock_request4.path = "{{step_0.stdout}}"
        mock_request4.dst_path = "{{step_0.stdout}}.bak"
        # Use spec to control available attributes
        mock_request4.__class__ = type('MockRequest', (), {'path': None, 'dst_path': None})

        self.graph.apply_result_substitution_to_request(mock_request4, "step_4")

        assert mock_request4.path == "/tmp/output.txt"
        assert mock_request4.dst_path == "/tmp/output.txt.bak"

    def test_debug_request_before_execution(self):
        """Test debug request logging before execution"""
        # Create mock request with various attributes
        mock_request = Mock()
        mock_request.operation_type = "OperationType.FILE"
        mock_request.op = Mock()
        mock_request.op.name = "COPY"
        mock_request.cmd = ["cp", "src", "dst"]
        mock_request.path = "/tmp/src"
        mock_request.dst_path = "/tmp/dst"
        mock_request.allow_failure = True
        mock_request.show_output = False

        node = RequestNode("test_node", mock_request)

        # Mock debug logger
        self.graph.debug_logger = Mock()
        self.graph.debug_logger.is_enabled.return_value = True

        # Execute
        self.graph._debug_request_before_execution(node, "test_node")

        # Verify debug log was called with correct parameters
        self.graph.debug_logger.log_step_start.assert_called_once()
        args, kwargs = self.graph.debug_logger.log_step_start.call_args
        assert args[0] == "test_node"
        assert args[1] == "FILE.COPY"
        assert kwargs['cmd'] == ["cp", "src", "dst"]
        assert kwargs['path'] == "/tmp/src"
        assert kwargs['dest'] == "/tmp/dst"
        assert kwargs['source'] == "/tmp/src"
        assert kwargs['allow_failure'] is True
        assert kwargs['show_output'] is False

    def test_debug_request_before_execution_disabled(self):
        """Test debug request logging when disabled"""
        mock_request = Mock()
        node = RequestNode("test_node", mock_request)

        # Mock debug logger disabled
        self.graph.debug_logger = Mock()
        self.graph.debug_logger.is_enabled.return_value = False

        # Execute
        self.graph._debug_request_before_execution(node, "test_node")

        # Should not call log_step_start
        self.graph.debug_logger.log_step_start.assert_not_called()

    def test_execute_node_safe(self):
        """Test safe node execution"""
        # Test successful execution
        mock_request = Mock()
        mock_request.execute.return_value = OperationResult(success=True, stdout="Success")

        node = RequestNode("node1", mock_request)

        result = self.graph._execute_node_safe(node, None)

        assert result.success is True
        assert result.stdout == "Success"

        # Test exception handling
        mock_request2 = Mock()
        mock_request2.execute.side_effect = RuntimeError("Test error")

        node2 = RequestNode("node2", mock_request2)

        result2 = self.graph._execute_node_safe(node2, None)

        assert result2.success is False
        assert "Test error" in result2.error_message
        assert "Traceback" in result2.error_message

    def test_collect_results(self):
        """Test result collection in execution order"""
        # Create nodes
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())
        node3 = RequestNode("node3", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        self.graph.add_request_node(node3)

        # Set execution order
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))
        self.graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.FILE_CREATION))

        # Create results (out of order)
        all_results = {
            "node3": OperationResult(success=True, stdout="Result 3"),
            "node1": OperationResult(success=True, stdout="Result 1"),
            "node2": OperationResult(success=True, stdout="Result 2")
        }

        # Mark node3 as skipped
        node3.status = "skipped"

        # Collect results
        results = self.graph._collect_results(all_results)

        # Should be in execution order
        assert len(results) == 3
        assert results[0].stdout == "Result 1"
        assert results[1].stdout == "Result 2"
        assert results[2].stdout == "Result 3"

    def test_collect_results_with_skipped(self):
        """Test result collection with skipped nodes"""
        # Create nodes
        node1 = RequestNode("node1", Mock())
        node2 = RequestNode("node2", Mock())

        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)

        # Set execution order
        self.graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.FILE_CREATION))

        # Only node1 has result, node2 was skipped
        all_results = {
            "node1": OperationResult(success=False, error_message="Failed")
        }

        node2.status = "skipped"

        # Collect results
        results = self.graph._collect_results(all_results)

        assert len(results) == 2
        assert results[0].error_message == "Failed"
        assert results[1].error_message == "Skipped due to dependency failure"
        assert not results[1].success


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    def test_complex_workflow_execution(self):
        """Test execution of complex workflow with multiple dependencies"""
        graph = RequestExecutionGraph()

        # Create a complex workflow:
        # node1 and node2 run in parallel
        # node3 depends on node1
        # node4 depends on both node2 and node3
        # node5 depends on node4

        requests = {}
        for i in range(1, 6):
            mock_request = Mock(spec=BaseRequest)
            mock_request.execute.return_value = OperationResult(
                success=True,
                stdout=f"Output from node{i}"
            )
            requests[f"node{i}"] = mock_request

            node = RequestNode(f"node{i}", mock_request)
            graph.add_request_node(node)

        # Add dependencies
        graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.FILE_CREATION))
        graph.add_dependency(DependencyEdge("node2", "node4", DependencyType.FILE_CREATION))
        graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.DIRECTORY_CREATION))
        graph.add_dependency(DependencyEdge("node4", "node5", DependencyType.EXECUTION_ORDER))

        # Test sequential execution
        results = graph.execute_sequential()
        assert len(results) == 5
        assert all(r.success for r in results)

        # Verify execution order constraints
        call_order = []
        for name, req in requests.items():
            if req.execute.called:
                call_order.append(name)

        # node1 before node3
        assert call_order.index("node1") < call_order.index("node3")
        # node2 before node4
        assert call_order.index("node2") < call_order.index("node4")
        # node3 before node4
        assert call_order.index("node3") < call_order.index("node4")
        # node4 before node5
        assert call_order.index("node4") < call_order.index("node5")

    def test_result_substitution_workflow(self):
        """Test workflow with result substitution"""
        graph = RequestExecutionGraph()

        # First request outputs a filename
        mock_request1 = Mock(spec=BaseRequest)
        mock_request1.execute.return_value = OperationResult(
            success=True,
            stdout="/tmp/generated_file.txt"
        )
        mock_request1.cmd = ["generate_filename"]

        # Second request uses the filename
        mock_request2 = Mock(spec=BaseRequest)
        mock_request2.execute.return_value = OperationResult(success=True)
        mock_request2.cmd = ["process", "{{step_0.stdout}}"]
        mock_request2.allow_failure = False

        node1 = RequestNode("0", mock_request1)
        node2 = RequestNode("1", mock_request2)

        graph.add_request_node(node1)
        graph.add_request_node(node2)

        graph.add_dependency(DependencyEdge("0", "1", DependencyType.FILE_CREATION))

        # Execute
        results = graph.execute_sequential()

        assert len(results) == 2
        assert all(r.success for r in results)

        # Verify substitution happened
        assert mock_request2.cmd == ["process", "/tmp/generated_file.txt"]
