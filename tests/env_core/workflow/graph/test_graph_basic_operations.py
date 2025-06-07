"""
Tests for basic RequestExecutionGraph operations
"""
import pytest
from unittest.mock import Mock

from src.env_core.workflow.request_execution_graph import (
    RequestExecutionGraph, RequestNode, DependencyEdge, DependencyType
)
from src.domain.requests.base.base_request import BaseRequest


class TestRequestExecutionGraphBasicOperations:
    """Tests for basic RequestExecutionGraph operations"""
    
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