"""
Comprehensive tests for src/env_core/workflow/graph_to_composite_adapter.py
Tests graph to composite request conversion and related functionality
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.env_core.workflow.graph_to_composite_adapter import GraphToCompositeAdapter
from src.env_core.workflow.request_execution_graph import (
    RequestExecutionGraph, 
    RequestNode, 
    DependencyEdge, 
    DependencyType
)
from src.operations.composite.composite_request import CompositeRequest
from src.operations.base_request import BaseRequest
from src.operations.constants.operation_type import OperationType
from src.operations.file.file_op_type import FileOpType


class TestGraphToCompositeAdapter:
    """Tests for GraphToCompositeAdapter class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create mock requests
        self.mock_request1 = Mock(spec=BaseRequest)
        self.mock_request1.operation_type = OperationType.SHELL
        
        self.mock_request2 = Mock(spec=BaseRequest)
        self.mock_request2.operation_type = OperationType.FILE
        
        self.mock_request3 = Mock(spec=BaseRequest)
        self.mock_request3.operation_type = OperationType.DOCKER
    
    def test_to_composite_request_empty_graph(self):
        """Test conversion of empty graph to composite request"""
        graph = RequestExecutionGraph()
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_make.return_value = Mock(spec=CompositeRequest)
            
            result = GraphToCompositeAdapter.to_composite_request(graph)
            
            # Should call make_composite_request with empty list
            mock_make.assert_called_once_with([])
            assert result is not None
    
    def test_to_composite_request_single_node(self):
        """Test conversion of single node graph"""
        graph = RequestExecutionGraph()
        node = RequestNode(
            id="node1",
            request=self.mock_request1
        )
        graph.add_request_node(node)
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = GraphToCompositeAdapter.to_composite_request(graph)
            
            # Should call make_composite_request with the single request
            mock_make.assert_called_once_with([self.mock_request1])
            assert result == mock_composite
    
    def test_to_composite_request_multiple_nodes_with_dependencies(self):
        """Test conversion of multi-node graph with dependencies"""
        graph = RequestExecutionGraph()
        
        # Add nodes
        node1 = RequestNode(id="node1", request=self.mock_request1)
        node2 = RequestNode(id="node2", request=self.mock_request2)
        node3 = RequestNode(id="node3", request=self.mock_request3)
        
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        graph.add_request_node(node3)
        
        # Add dependencies: node1 -> node2 -> node3
        edge1 = DependencyEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.EXECUTION_ORDER
        )
        edge2 = DependencyEdge(
            from_node="node2",
            to_node="node3",
            dependency_type=DependencyType.FILE_CREATION
        )
        
        graph.add_dependency(edge1)
        graph.add_dependency(edge2)
        
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_composite = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_composite
            
            result = GraphToCompositeAdapter.to_composite_request(graph)
            
            # Should call make_composite_request with requests in topological order
            mock_make.assert_called_once_with([self.mock_request1, self.mock_request2, self.mock_request3])
            assert result == mock_composite
    
    def test_from_composite_request_empty(self):
        """Test conversion from empty composite request"""
        mock_composite = Mock(spec=CompositeRequest)
        mock_composite.requests = []
        
        result = GraphToCompositeAdapter.from_composite_request(mock_composite)
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0
    
    def test_from_composite_request_single_request(self):
        """Test conversion from composite request with single request"""
        mock_composite = Mock(spec=CompositeRequest)
        mock_composite.requests = [self.mock_request1]
        
        result = GraphToCompositeAdapter.from_composite_request(mock_composite, extract_dependencies=False)
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 1
        assert "request_0" in result.nodes
        assert result.nodes["request_0"].request == self.mock_request1
        assert len(result.edges) == 0  # No dependencies with single request
    
    def test_from_composite_request_multiple_requests_no_extraction(self):
        """Test conversion with multiple requests without dependency extraction"""
        mock_composite = Mock(spec=CompositeRequest)
        mock_composite.requests = [self.mock_request1, self.mock_request2, self.mock_request3]
        
        result = GraphToCompositeAdapter.from_composite_request(mock_composite, extract_dependencies=False)
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 3
        assert "request_0" in result.nodes
        assert "request_1" in result.nodes
        assert "request_2" in result.nodes
        
        # Should have sequential execution order dependencies
        assert len(result.edges) == 2
        
        # Check edges
        edge_dict = {(e.from_node, e.to_node): e for e in result.edges}
        assert ("request_0", "request_1") in edge_dict
        assert ("request_1", "request_2") in edge_dict
        
        # Check edge types
        assert edge_dict[("request_0", "request_1")].dependency_type == DependencyType.EXECUTION_ORDER
        assert edge_dict[("request_1", "request_2")].dependency_type == DependencyType.EXECUTION_ORDER
    
    def test_from_composite_request_with_dependency_extraction(self):
        """Test conversion with dependency extraction enabled"""
        mock_composite = Mock(spec=CompositeRequest)
        mock_composite.requests = [self.mock_request1, self.mock_request2]
        
        with patch.object(GraphToCompositeAdapter, '_extract_dependencies') as mock_extract:
            result = GraphToCompositeAdapter.from_composite_request(mock_composite, extract_dependencies=True)
            
            # Should call _extract_dependencies
            mock_extract.assert_called_once()
            args = mock_extract.call_args[0]
            assert args[0] == result  # graph
            assert len(args[1]) == 2  # nodes list


class TestExtractResourceInfo:
    """Tests for _extract_resource_info method"""
    
    def test_extract_resource_info_non_file_request(self):
        """Test resource extraction for non-file request"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.SHELL
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == set()
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == set()
    
    def test_extract_resource_info_mkdir_request(self):
        """Test resource extraction for MKDIR file request"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.FILE
        mock_request.op = FileOpType.MKDIR
        mock_request.target_path = "/test/directory"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == set()
        assert creates_dirs == {"/test/directory"}
        assert reads_files == set()
        assert requires_dirs == set()
    
    def test_extract_resource_info_touch_request(self):
        """Test resource extraction for TOUCH file request"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.FILE
        mock_request.op = FileOpType.TOUCH
        mock_request.target_path = "/test/dir/file.txt"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == {"/test/dir/file.txt"}
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == {"/test/dir"}
    
    def test_extract_resource_info_copy_request(self):
        """Test resource extraction for COPY file request"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.FILE
        mock_request.op = FileOpType.COPY
        mock_request.source_path = "/src/file.txt"
        mock_request.target_path = "/dest/dir/file.txt"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == {"/dest/dir/file.txt"}
        assert creates_dirs == set()
        assert reads_files == {"/src/file.txt"}
        assert requires_dirs == {"/dest/dir"}
    
    def test_extract_resource_info_touch_with_root_parent(self):
        """Test resource extraction for TOUCH with root directory parent"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.FILE
        mock_request.op = FileOpType.TOUCH
        mock_request.target_path = "file.txt"  # Current directory
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == {"file.txt"}
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == set()  # Parent is '.' so not added
    
    def test_extract_resource_info_composite_request(self):
        """Test resource extraction for nested CompositeRequest"""
        # Create mock sub-requests
        mock_sub_request1 = Mock(spec=BaseRequest)
        mock_sub_request1.operation_type = OperationType.FILE
        mock_sub_request1.op = FileOpType.MKDIR
        mock_sub_request1.target_path = "/test/dir"
        
        mock_sub_request2 = Mock(spec=BaseRequest)
        mock_sub_request2.operation_type = OperationType.FILE
        mock_sub_request2.op = FileOpType.TOUCH
        mock_sub_request2.target_path = "/test/dir/file.txt"
        
        # Create composite request
        mock_composite = Mock(spec=CompositeRequest)
        mock_composite.requests = [mock_sub_request1, mock_sub_request2]
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_composite)
        
        # Should combine results from both sub-requests
        assert creates_files == {"/test/dir/file.txt"}
        assert creates_dirs == {"/test/dir"}
        assert reads_files == set()
        assert requires_dirs == {"/test/dir"}
    
    def test_extract_resource_info_missing_attributes(self):
        """Test resource extraction when request lacks expected attributes"""
        mock_request = Mock(spec=BaseRequest)
        mock_request.operation_type = OperationType.FILE
        mock_request.op = FileOpType.MKDIR
        # Missing target_path attribute
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(mock_request)
        
        assert creates_files == set()
        assert creates_dirs == set()
        assert reads_files == set()
        assert requires_dirs == set()


class TestExtractDependencies:
    """Tests for _extract_dependencies method"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.graph = RequestExecutionGraph()
    
    def test_extract_dependencies_no_dependencies(self):
        """Test dependency extraction with no actual dependencies"""
        node1 = RequestNode(
            id="node1",
            request=Mock(),
            creates_files={"file1.txt"},
            reads_files=set()
        )
        node2 = RequestNode(
            id="node2",
            request=Mock(),
            creates_files=set(),
            reads_files={"file2.txt"}
        )
        
        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        
        GraphToCompositeAdapter._extract_dependencies(self.graph, [node1, node2])
        
        # No dependencies should be added since file1 != file2
        assert len(self.graph.edges) == 0
    
    def test_extract_dependencies_file_creation_dependency(self):
        """Test extraction of file creation dependency"""
        node1 = RequestNode(
            id="node1",
            request=Mock(),
            creates_files={"shared_file.txt"},
            reads_files=set()
        )
        node2 = RequestNode(
            id="node2",
            request=Mock(),
            creates_files=set(),
            reads_files={"shared_file.txt"}
        )
        
        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        
        GraphToCompositeAdapter._extract_dependencies(self.graph, [node1, node2])
        
        # Should add file creation dependency
        assert len(self.graph.edges) == 1
        edge = self.graph.edges[0]
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.FILE_CREATION
        assert edge.resource_path == "shared_file.txt"
        assert "shared_file.txt" in edge.description
    
    def test_extract_dependencies_directory_creation_dependency(self):
        """Test extraction of directory creation dependency"""
        node1 = RequestNode(
            id="node1",
            request=Mock(),
            creates_dirs={"test_dir"},
            requires_dirs=set()
        )
        node2 = RequestNode(
            id="node2",
            request=Mock(),
            creates_dirs=set(),
            requires_dirs={"test_dir"}
        )
        
        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        
        # Keep original order (node1, node2) for proper dependency detection
        GraphToCompositeAdapter._extract_dependencies(self.graph, [node1, node2])
        
        # Should add directory creation dependency (node1 -> node2)
        assert len(self.graph.edges) == 1
        edge = self.graph.edges[0]
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.DIRECTORY_CREATION
        assert edge.resource_path == "test_dir"
        assert "test_dir" in edge.description
    
    def test_extract_dependencies_multiple_dependencies(self):
        """Test extraction of multiple different dependencies"""
        node1 = RequestNode(
            id="node1",
            request=Mock(),
            creates_files={"file1.txt"},
            creates_dirs={"dir1"}
        )
        node2 = RequestNode(
            id="node2",
            request=Mock(),
            reads_files={"file1.txt"},
            requires_dirs={"dir1"}
        )
        
        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        
        GraphToCompositeAdapter._extract_dependencies(self.graph, [node1, node2])
        
        # Should add both file and directory dependencies
        assert len(self.graph.edges) == 2
        
        edges_by_type = {e.dependency_type: e for e in self.graph.edges}
        assert DependencyType.FILE_CREATION in edges_by_type
        assert DependencyType.DIRECTORY_CREATION in edges_by_type
        
        file_edge = edges_by_type[DependencyType.FILE_CREATION]
        assert file_edge.resource_path == "file1.txt"
        
        dir_edge = edges_by_type[DependencyType.DIRECTORY_CREATION]
        assert dir_edge.resource_path == "dir1"
    
    def test_extract_dependencies_multiple_files_same_dependency(self):
        """Test extraction when multiple files create same dependency"""
        node1 = RequestNode(
            id="node1",
            request=Mock(),
            creates_files={"file1.txt", "file2.txt"}
        )
        node2 = RequestNode(
            id="node2",
            request=Mock(),
            reads_files={"file1.txt", "file2.txt"}
        )
        
        self.graph.add_request_node(node1)
        self.graph.add_request_node(node2)
        
        GraphToCompositeAdapter._extract_dependencies(self.graph, [node1, node2])
        
        # Should add separate dependency for each file
        assert len(self.graph.edges) == 2
        resource_paths = {e.resource_path for e in self.graph.edges}
        assert resource_paths == {"file1.txt", "file2.txt"}


class TestMergeGraphs:
    """Tests for merge_graphs method"""
    
    def test_merge_graphs_empty_list(self):
        """Test merging empty list of graphs"""
        result = GraphToCompositeAdapter.merge_graphs([])
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 0
        assert len(result.edges) == 0
    
    def test_merge_graphs_single_graph(self):
        """Test merging single graph"""
        graph = RequestExecutionGraph()
        node = RequestNode(id="node1", request=Mock())
        graph.add_request_node(node)
        
        result = GraphToCompositeAdapter.merge_graphs([graph])
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 1
        assert "graph0_node1" in result.nodes
        assert result.nodes["graph0_node1"].request == node.request
        assert len(result.edges) == 0
    
    def test_merge_graphs_multiple_graphs_with_nodes(self):
        """Test merging multiple graphs with nodes"""
        # Create first graph
        graph1 = RequestExecutionGraph()
        node1 = RequestNode(id="node1", request=Mock())
        node2 = RequestNode(id="node2", request=Mock())
        graph1.add_request_node(node1)
        graph1.add_request_node(node2)
        
        edge1 = DependencyEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.EXECUTION_ORDER
        )
        graph1.add_dependency(edge1)
        
        # Create second graph
        graph2 = RequestExecutionGraph()
        node3 = RequestNode(id="node3", request=Mock())
        graph2.add_request_node(node3)
        
        result = GraphToCompositeAdapter.merge_graphs([graph1, graph2])
        
        assert isinstance(result, RequestExecutionGraph)
        assert len(result.nodes) == 3
        
        # Check renamed node IDs
        assert "graph0_node1" in result.nodes
        assert "graph0_node2" in result.nodes
        assert "graph1_node3" in result.nodes
        
        # Check internal edges are preserved with renamed IDs
        internal_edges = [e for e in result.edges if e.dependency_type != DependencyType.EXECUTION_ORDER or "Graph connection" not in e.description]
        assert len(internal_edges) == 1
        assert internal_edges[0].from_node == "graph0_node1"
        assert internal_edges[0].to_node == "graph0_node2"
        
        # Check connection edge between graphs
        connection_edges = [e for e in result.edges if "Graph connection" in e.description]
        assert len(connection_edges) == 1
        assert connection_edges[0].from_node == "graph0_node2"  # Last of graph1
        assert connection_edges[0].to_node == "graph1_node3"    # First of graph2
    
    def test_merge_graphs_with_metadata_and_status(self):
        """Test merging graphs preserves node metadata and status"""
        graph = RequestExecutionGraph()
        node = RequestNode(
            id="node1",
            request=Mock(),
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"file2.txt"},
            requires_dirs={"dir2"},
            metadata={"key": "value"}
        )
        node.status = "completed"  # Status is string, not enum
        node.result = Mock()
        
        graph.add_request_node(node)
        
        result = GraphToCompositeAdapter.merge_graphs([graph])
        
        merged_node = result.nodes["graph0_node1"]
        assert merged_node.creates_files == {"file1.txt"}
        assert merged_node.creates_dirs == {"dir1"}
        assert merged_node.reads_files == {"file2.txt"}
        assert merged_node.requires_dirs == {"dir2"}
        assert merged_node.metadata == {"key": "value"}
        assert merged_node.status == "completed"
        assert merged_node.result == node.result
    
    def test_merge_graphs_empty_graphs_no_connection(self):
        """Test merging graphs where some are empty (no connection edges)"""
        # Empty graph
        graph1 = RequestExecutionGraph()
        
        # Non-empty graph
        graph2 = RequestExecutionGraph()
        node = RequestNode(id="node1", request=Mock())
        graph2.add_request_node(node)
        
        result = GraphToCompositeAdapter.merge_graphs([graph1, graph2])
        
        assert len(result.nodes) == 1
        assert "graph1_node1" in result.nodes
        assert len(result.edges) == 0  # No connection edge because graph1 is empty
    
    def test_merge_graphs_complex_scenario(self):
        """Test merging complex scenario with multiple graphs and edges"""
        # Graph 1: node1 -> node2
        graph1 = RequestExecutionGraph()
        node1 = RequestNode(id="a", request=Mock())
        node2 = RequestNode(id="b", request=Mock())
        graph1.add_request_node(node1)
        graph1.add_request_node(node2)
        edge1 = DependencyEdge("a", "b", DependencyType.FILE_CREATION, "file1.txt")
        graph1.add_dependency(edge1)
        
        # Graph 2: node3 -> node4
        graph2 = RequestExecutionGraph()
        node3 = RequestNode(id="c", request=Mock())
        node4 = RequestNode(id="d", request=Mock())
        graph2.add_request_node(node3)
        graph2.add_request_node(node4)
        edge2 = DependencyEdge("c", "d", DependencyType.DIRECTORY_CREATION, "dir1")
        graph2.add_dependency(edge2)
        
        # Graph 3: single node
        graph3 = RequestExecutionGraph()
        node5 = RequestNode(id="e", request=Mock())
        graph3.add_request_node(node5)
        
        result = GraphToCompositeAdapter.merge_graphs([graph1, graph2, graph3])
        
        assert len(result.nodes) == 5
        assert len(result.edges) == 4  # 2 internal + 2 connection edges
        
        # Check connection edges
        connection_edges = [e for e in result.edges if "Graph connection" in e.description]
        assert len(connection_edges) == 2
        
        # Should connect: graph0_b -> graph1_c and graph1_d -> graph2_e
        connection_pairs = {(e.from_node, e.to_node) for e in connection_edges}
        assert ("graph0_b", "graph1_c") in connection_pairs
        assert ("graph1_d", "graph2_e") in connection_pairs


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    def test_round_trip_conversion(self):
        """Test converting CompositeRequest -> Graph -> CompositeRequest"""
        # Create original composite request
        mock_request1 = Mock(spec=BaseRequest)
        mock_request2 = Mock(spec=BaseRequest)
        mock_request3 = Mock(spec=BaseRequest)
        
        original_composite = Mock(spec=CompositeRequest)
        original_composite.requests = [mock_request1, mock_request2, mock_request3]
        
        # Convert to graph
        graph = GraphToCompositeAdapter.from_composite_request(original_composite, extract_dependencies=False)
        
        # Convert back to composite request
        with patch('src.operations.composite.composite_request.CompositeRequest.make_composite_request') as mock_make:
            mock_result = Mock(spec=CompositeRequest)
            mock_make.return_value = mock_result
            
            result_composite = GraphToCompositeAdapter.to_composite_request(graph)
            
            # Should preserve request order
            mock_make.assert_called_once_with([mock_request1, mock_request2, mock_request3])
            assert result_composite == mock_result
    
    def test_complex_dependency_scenario(self):
        """Test complex scenario with file and directory dependencies"""
        # Create requests with specific resource requirements
        mkdir_request = Mock(spec=BaseRequest)
        mkdir_request.operation_type = OperationType.FILE
        mkdir_request.op = FileOpType.MKDIR
        mkdir_request.target_path = "/workspace"
        
        touch_request = Mock(spec=BaseRequest)
        touch_request.operation_type = OperationType.FILE
        touch_request.op = FileOpType.TOUCH
        touch_request.target_path = "/workspace/file.txt"
        
        copy_request = Mock(spec=BaseRequest)
        copy_request.operation_type = OperationType.FILE
        copy_request.op = FileOpType.COPY
        copy_request.source_path = "/workspace/file.txt"
        copy_request.target_path = "/output/file.txt"
        
        composite = Mock(spec=CompositeRequest)
        composite.requests = [mkdir_request, touch_request, copy_request]
        
        # Convert with dependency extraction
        graph = GraphToCompositeAdapter.from_composite_request(composite, extract_dependencies=True)
        
        # Should have 3 nodes
        assert len(graph.nodes) == 3
        
        # Should have dependencies beyond just execution order
        # Note: The actual number depends on the _extract_dependencies implementation
        assert len(graph.edges) >= 2  # At least sequential execution order
        
        # Verify nodes have correct resource info
        nodes = list(graph.nodes.values())
        mkdir_node = next(n for n in nodes if n.request == mkdir_request)
        touch_node = next(n for n in nodes if n.request == touch_request)
        copy_node = next(n for n in nodes if n.request == copy_request)
        
        assert "/workspace" in mkdir_node.creates_dirs
        assert "/workspace/file.txt" in touch_node.creates_files
        assert "/workspace" in touch_node.requires_dirs
        assert "/workspace/file.txt" in copy_node.reads_files