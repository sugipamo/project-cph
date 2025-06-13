"""Property-based tests for workflow builder validation functions"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from dataclasses import dataclass
from typing import Dict, List, Set, Any

from src.workflow.builder.builder_validation import (
    validate_graph_structure,
    check_graph_connectivity,
    ValidationResult
)
from src.workflow.builder.graph_builder_utils import (
    build_resource_mappings,
    detect_file_creation_dependencies,
    detect_directory_creation_dependencies,
    NodeInfo,
    DependencyInfo
)


# Test data generators for property-based testing

@dataclass
class MockRequest:
    """Mock request for testing"""
    allow_failure: bool = False


@dataclass  
class MockNode:
    """Mock node for testing"""
    id: str
    request: MockRequest
    status: str = "pending"
    

def mock_nodes_strategy(min_nodes=1, max_nodes=10):
    """Generate a dictionary of mock nodes"""
    return st.dictionaries(
        keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
        values=st.builds(
            MockNode,
            id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10),
            request=st.builds(MockRequest, allow_failure=st.booleans()),
            status=st.sampled_from(["pending", "running", "completed", "failed", "skipped"])
        ),
        min_size=min_nodes,
        max_size=max_nodes
    )


def mock_edges_strategy(node_ids):
    """Generate edges between existing nodes"""
    if len(node_ids) < 2:
        return st.lists(st.nothing(), max_size=0)
    
    @dataclass
    class MockEdge:
        from_node: str
        to_node: str
        dependency_type: str = "file_creation"
    
    return st.lists(
        st.builds(
            MockEdge,
            from_node=st.sampled_from(node_ids),
            to_node=st.sampled_from(node_ids)
        ).filter(lambda e: e.from_node != e.to_node),  # No self-loops
        max_size=len(node_ids) * 2
    )


class TestGraphValidationProperties:
    """Property-based tests for graph validation"""

    @given(mock_nodes_strategy())
    def test_validation_always_returns_result(self, nodes):
        """Validation should always return a ValidationResult"""
        result = validate_graph_structure(nodes, [])
        assert isinstance(result, ValidationResult)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.statistics, dict)

    @given(mock_nodes_strategy())
    def test_empty_edges_never_cause_edge_errors(self, nodes):
        """Empty edge list should never produce edge-related errors"""
        result = validate_graph_structure(nodes, [])
        # Should not have any edge-related errors
        edge_errors = [e for e in result.errors if 'edge' in e.lower() or 'dependency' in e.lower()]
        assert len(edge_errors) == 0

    @given(st.data())
    def test_valid_edges_reference_existing_nodes(self, data):
        """Valid edges should never produce reference errors"""
        nodes = data.draw(mock_nodes_strategy(min_nodes=2))
        node_ids = list(nodes.keys())
        edges = data.draw(mock_edges_strategy(node_ids))
        
        result = validate_graph_structure(nodes, edges)
        
        # Should not have any "references unknown" errors
        ref_errors = [e for e in result.errors if 'references unknown' in e]
        assert len(ref_errors) == 0

    @given(mock_nodes_strategy())
    def test_node_count_statistics_accuracy(self, nodes):
        """Node count in statistics should match actual node count"""
        result = validate_graph_structure(nodes, [])
        assert result.statistics.get('total_nodes', 0) == len(nodes)

    @given(st.data())
    def test_validation_is_deterministic(self, data):
        """Same input should always produce same validation result"""
        nodes = data.draw(mock_nodes_strategy())
        node_ids = list(nodes.keys()) if nodes else []
        edges = data.draw(mock_edges_strategy(node_ids))
        
        result1 = validate_graph_structure(nodes, edges)
        result2 = validate_graph_structure(nodes, edges)
        
        assert result1.is_valid == result2.is_valid
        assert result1.errors == result2.errors
        assert result1.warnings == result2.warnings
        assert result1.statistics == result2.statistics


class TestConnectivityProperties:
    """Property-based tests for graph connectivity"""

    def adjacency_list_strategy(self, node_ids):
        """Generate adjacency list for given nodes"""
        if not node_ids:
            return st.just({})
        
        return st.dictionaries(
            keys=st.sampled_from(node_ids),
            values=st.sets(st.sampled_from(node_ids), max_size=len(node_ids)),
            min_size=len(node_ids),
            max_size=len(node_ids)
        )

    @given(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=8, unique=True))
    def test_connectivity_check_returns_result(self, node_ids):
        """Connectivity check should always return a ValidationResult"""
        # Create a simple adjacency list
        adjacency_list = {node_id: set() for node_id in node_ids}
        
        result = check_graph_connectivity(adjacency_list)
        assert isinstance(result, ValidationResult)
        assert 'connected_components' in result.statistics

    @given(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5, unique=True))
    def test_fully_connected_graph_has_one_component(self, node_ids):
        """A fully connected graph should have exactly one component"""
        if len(node_ids) < 2:
            return
        
        # Create fully connected adjacency list
        adjacency_list = {}
        for node_id in node_ids:
            adjacency_list[node_id] = set(node_ids) - {node_id}
        
        result = check_graph_connectivity(adjacency_list)
        assert result.statistics['connected_components'] == 1

    @given(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=8, unique=True))
    def test_isolated_nodes_increase_component_count(self, node_ids):
        """Isolated nodes should each be their own component"""
        # Create adjacency list with no connections (all isolated)
        adjacency_list = {node_id: set() for node_id in node_ids}
        
        result = check_graph_connectivity(adjacency_list)
        assert result.statistics['connected_components'] == len(node_ids)


class TestResourceMappingProperties:
    """Property-based tests for resource mapping and dependency detection"""

    def node_info_strategy(self, min_nodes=1, max_nodes=5):
        """Generate NodeInfo objects for testing"""
        return st.lists(
            st.builds(
                NodeInfo,
                id=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=8),
                step=st.none(),  # We don't need real Step objects for these tests
                creates_files=st.sets(st.text(min_size=1, max_size=10), max_size=3),
                creates_dirs=st.sets(st.text(min_size=1, max_size=10), max_size=3),
                reads_files=st.sets(st.text(min_size=1, max_size=10), max_size=3),
                requires_dirs=st.sets(st.text(min_size=1, max_size=10), max_size=3),
                metadata=st.dictionaries(st.text(), st.text(), max_size=2)
            ),
            min_size=min_nodes,
            max_size=max_nodes,
            unique_by=lambda x: x.id
        )

    @given(node_info_strategy())
    def test_resource_mapping_preserves_all_resources(self, node_infos):
        """Resource mapping should preserve all resource information"""
        mappings = build_resource_mappings(node_infos)
        
        # Check that all mappings are dictionaries
        assert isinstance(mappings, dict)
        assert 'file_creators' in mappings
        assert 'dir_creators' in mappings
        assert 'file_readers' in mappings
        assert 'dir_requirers' in mappings
        
        # Count total resources in input vs output
        total_creates_files = sum(len(node.creates_files) for node in node_infos)
        total_creates_dirs = sum(len(node.creates_dirs) for node in node_infos)
        total_reads_files = sum(len(node.reads_files) for node in node_infos)
        total_requires_dirs = sum(len(node.requires_dirs) for node in node_infos)
        
        # Check that mapping preserves the count
        mapped_creates_files = sum(len(creators) for creators in mappings['file_creators'].values())
        mapped_creates_dirs = sum(len(creators) for creators in mappings['dir_creators'].values())
        mapped_reads_files = sum(len(readers) for readers in mappings['file_readers'].values())
        mapped_requires_dirs = sum(len(requirers) for requirers in mappings['dir_requirers'].values())
        
        assert mapped_creates_files == total_creates_files
        assert mapped_creates_dirs == total_creates_dirs
        assert mapped_reads_files == total_reads_files
        assert mapped_requires_dirs == total_requires_dirs

    @given(node_info_strategy())
    def test_file_dependencies_are_logical(self, node_infos):
        """File creation dependencies should follow logical rules"""
        mappings = build_resource_mappings(node_infos)
        dependencies = detect_file_creation_dependencies(mappings)
        
        for dep in dependencies:
            assert isinstance(dep, DependencyInfo)
            assert dep.dependency_type == "FILE_CREATION"
            assert dep.resource_path  # Should have a resource path
            
            # Find the creator and reader nodes
            creator_found = False
            reader_found = False
            
            for node in node_infos:
                if node.id == dep.from_node_id and dep.resource_path in node.creates_files:
                    creator_found = True
                if node.id == dep.to_node_id and dep.resource_path in node.reads_files:
                    reader_found = True
            
            assert creator_found, f"Creator node {dep.from_node_id} should create {dep.resource_path}"
            assert reader_found, f"Reader node {dep.to_node_id} should read {dep.resource_path}"

    @given(node_info_strategy())
    def test_directory_dependencies_are_logical(self, node_infos):
        """Directory creation dependencies should follow logical rules"""
        mappings = build_resource_mappings(node_infos)
        dependencies = detect_directory_creation_dependencies(mappings)
        
        for dep in dependencies:
            assert isinstance(dep, DependencyInfo)
            assert dep.dependency_type == "DIRECTORY_CREATION"
            assert dep.resource_path  # Should have a resource path
            
            # Find the creator and requirer nodes
            creator_found = False
            requirer_found = False
            
            for node in node_infos:
                if node.id == dep.from_node_id and dep.resource_path in node.creates_dirs:
                    creator_found = True
                if node.id == dep.to_node_id and dep.resource_path in node.requires_dirs:
                    requirer_found = True
            
            assert creator_found, f"Creator node {dep.from_node_id} should create {dep.resource_path}"
            assert requirer_found, f"Requirer node {dep.to_node_id} should require {dep.resource_path}"


@pytest.mark.slow
class TestLargeGraphProperties:
    """Property-based tests for larger graphs"""

    @settings(max_examples=20)  # Reduce examples for slow tests
    @given(mock_nodes_strategy(min_nodes=10, max_nodes=50))
    def test_validation_scales_with_graph_size(self, nodes):
        """Validation should handle larger graphs without issues"""
        result = validate_graph_structure(nodes, [])
        
        # Should still return valid result structure
        assert isinstance(result, ValidationResult)
        assert result.statistics['total_nodes'] == len(nodes)
        
        # Density should be reasonable for empty edge list
        assert result.statistics.get('density', 0) == 0

    @settings(max_examples=10)
    @given(st.data())
    def test_large_graph_connectivity_analysis(self, data):
        """Connectivity analysis should work for larger graphs"""
        node_ids = data.draw(st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=3), 
            min_size=20, 
            max_size=50, 
            unique=True
        ))
        
        # Create random adjacency list
        adjacency_list = {}
        for node_id in node_ids:
            # Each node connects to 0-3 other random nodes
            connections = data.draw(st.sets(
                st.sampled_from(node_ids), 
                max_size=min(3, len(node_ids)-1)
            ))
            connections.discard(node_id)  # Remove self-connection
            adjacency_list[node_id] = connections
        
        result = check_graph_connectivity(adjacency_list)
        
        # Should have reasonable component count
        components = result.statistics['connected_components']
        assert 1 <= components <= len(node_ids)
        assert result.statistics['largest_component_size'] >= 1
        assert result.statistics['smallest_component_size'] >= 1