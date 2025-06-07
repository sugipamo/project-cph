"""
Tests for DependencyEdge class
"""
import pytest
from unittest.mock import Mock

from src.env_core.workflow.request_execution_graph import DependencyEdge, DependencyType


class TestDependencyEdge:
    """Tests for DependencyEdge class"""
    
    def test_dependency_edge_creation(self):
        """Test creating DependencyEdge"""
        edge = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION)
        
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.FILE_CREATION
        assert edge.resource_path is None
        assert edge.description == ""
    
    def test_dependency_edge_with_resource_path(self):
        """Test creating DependencyEdge with resource path"""
        edge = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION, "/tmp/file.txt", "File dependency")
        
        assert edge.resource_path == "/tmp/file.txt"
        assert edge.description == "File dependency"
    
    def test_dependency_edge_attributes(self):
        """Test DependencyEdge attributes"""
        edge = DependencyEdge("nodeA", "nodeB", DependencyType.EXECUTION_ORDER)
        
        assert edge.from_node == "nodeA"
        assert edge.to_node == "nodeB"
        assert edge.dependency_type == DependencyType.EXECUTION_ORDER
    
    def test_dependency_edge_different_instances(self):
        """Test DependencyEdge different instances"""
        edge1 = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION)
        edge2 = DependencyEdge("node1", "node2", DependencyType.FILE_CREATION)
        edge3 = DependencyEdge("node1", "node3", DependencyType.FILE_CREATION)
        
        # Test that edges have different attributes as expected
        assert edge1.to_node == edge2.to_node
        assert edge1.to_node != edge3.to_node
    
    def test_dependency_types(self):
        """Test different dependency types"""
        file_edge = DependencyEdge("n1", "n2", DependencyType.FILE_CREATION)
        dir_edge = DependencyEdge("n1", "n2", DependencyType.DIRECTORY_CREATION)
        exec_edge = DependencyEdge("n1", "n2", DependencyType.EXECUTION_ORDER)
        
        assert file_edge.dependency_type == DependencyType.FILE_CREATION
        assert dir_edge.dependency_type == DependencyType.DIRECTORY_CREATION
        assert exec_edge.dependency_type == DependencyType.EXECUTION_ORDER