"""Tests for graph construction module."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.workflow.builder.graph_construction import (
    GraphConstructionResult,
    NodeConstructionInfo,
    construct_graph_from_steps,
    create_nodes_from_steps,
    build_node_dependencies,
    create_graph_metadata,
    validate_graph_construction,
    optimize_graph_structure,
    _has_resource_conflict_between_nodes,
    _calculate_graph_complexity,
    _remove_redundant_dependencies
)


class TestGraphConstructionResult:
    """Test GraphConstructionResult dataclass."""
    
    def test_init_basic(self):
        nodes = [Mock(), Mock()]
        dependencies = [Mock()]
        
        result = GraphConstructionResult(
            nodes=nodes,
            dependencies=dependencies,
            metadata={"key": "value"},
            errors=[],
            warnings=["Warning 1"]
        )
        
        assert result.nodes == nodes
        assert result.dependencies == dependencies
        assert result.metadata == {"key": "value"}
        assert result.errors == []
        assert result.warnings == ["Warning 1"]
    
    def test_is_success_property(self):
        # Success case
        result = GraphConstructionResult(
            nodes=[Mock()],
            dependencies=[],
            metadata={},
            errors=[],
            warnings=[]
        )
        assert result.is_success is True
        
        # Failure case - has errors
        result = GraphConstructionResult(
            nodes=[Mock()],
            dependencies=[],
            metadata={},
            errors=["Error 1"],
            warnings=[]
        )
        assert result.is_success is False
        
        # Failure case - no nodes
        result = GraphConstructionResult(
            nodes=[],
            dependencies=[],
            metadata={},
            errors=[],
            warnings=[]
        )
        assert result.is_success is False


class TestNodeConstructionInfo:
    """Test NodeConstructionInfo dataclass."""
    
    def test_init_complete(self):
        info = NodeConstructionInfo(
            node_id="n1",
            request=Mock(),
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"file2.txt"},
            requires_dirs={"dir2"},
            metadata={"type": "test"},
            original_index=0
        )
        
        assert info.node_id == "n1"
        assert info.creates_files == {"file1.txt"}
        assert info.metadata == {"type": "test"}
        assert info.original_index == 0


class TestGraphConstruction:
    """Test graph construction functions."""
    
    @patch('src.workflow.builder.graph_construction.create_graph_metadata')
    @patch('src.workflow.builder.graph_construction.build_node_dependencies')
    @patch('src.workflow.builder.graph_construction.create_nodes_from_steps')
    def test_construct_graph_from_steps_success(self, mock_create_nodes, mock_build_deps, mock_create_metadata):
        # Setup mocks
        node_info = NodeConstructionInfo(
            node_id="n1",
            request=Mock(),
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set(),
            metadata={},
            original_index=0
        )
        
        mock_create_nodes.return_value = [node_info]
        mock_build_deps.return_value = [Mock()]
        mock_create_metadata.return_value = {"total": 1}
        
        steps = [Mock()]
        result = construct_graph_from_steps(steps)
        
        assert result.is_success is True
        assert len(result.nodes) == 1
        assert len(result.dependencies) == 1
        assert result.metadata == {"total": 1}
        assert result.errors == []
    
    @patch('src.workflow.builder.graph_construction.create_nodes_from_steps')
    def test_construct_graph_from_steps_no_valid_nodes(self, mock_create_nodes):
        # All nodes failed to create requests
        node_info = NodeConstructionInfo(
            node_id="n1",
            request=None,  # Failed to create
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set(),
            metadata={},
            original_index=0
        )
        
        mock_create_nodes.return_value = [node_info]
        
        result = construct_graph_from_steps([Mock()])
        
        assert result.is_success is False
        assert len(result.nodes) == 0
        assert "Failed to create request" in result.errors[0]
        assert "No valid nodes created" in result.errors[-1]
    
    def test_construct_graph_from_steps_exception(self):
        # Force an exception
        steps = None  # This will cause an error when iterating
        
        result = construct_graph_from_steps(steps)
        
        assert result.is_success is False
        assert len(result.errors) == 1
        assert "Graph construction failed" in result.errors[0]
    
    @patch('src.workflow.builder.step_conversion.convert_step_to_request')
    def test_create_nodes_from_steps(self, mock_convert):
        # Mock conversion result
        conversion_result = Mock()
        conversion_result.request = Mock()
        conversion_result.resource_info = (
            {"file1.txt"},  # creates_files
            {"dir1"},       # creates_dirs
            {"file2.txt"},  # reads_files
            {"dir2"}        # requires_dirs
        )
        conversion_result.metadata = {"converted": True}
        
        mock_convert.return_value = conversion_result
        
        steps = [Mock(), Mock()]
        node_infos = create_nodes_from_steps(steps)
        
        assert len(node_infos) == 2
        assert node_infos[0].node_id == "step_0"
        assert node_infos[1].node_id == "step_1"
        assert node_infos[0].creates_files == {"file1.txt"}
        assert node_infos[0].metadata == {"converted": True}
    
    @patch('src.workflow.builder.functional_utils.pipe')
    @patch('src.workflow.builder.graph_construction._convert_mappings_to_edges')
    def test_build_node_dependencies_success(self, mock_convert_edges, mock_pipe):
        # Mock pipe result with mappings attribute
        pipe_result = Mock()
        pipe_result.mappings = [Mock()]
        mock_pipe.return_value = pipe_result
        
        mock_convert_edges.return_value = [Mock()]
        
        node_infos = [
            NodeConstructionInfo(
                node_id="n1",
                request=Mock(),
                creates_files={"file1.txt"},
                creates_dirs=set(),
                reads_files=set(),
                requires_dirs=set(),
                metadata={},
                original_index=0
            )
        ]
        
        dependencies = build_node_dependencies(node_infos)
        
        assert len(dependencies) == 1
        mock_pipe.assert_called_once()
        mock_convert_edges.assert_called_once()
    
    @patch('src.workflow.builder.functional_utils.pipe')
    @patch('src.workflow.builder.graph_construction._create_sequential_dependencies')
    def test_build_node_dependencies_fallback(self, mock_sequential, mock_pipe):
        # Mock pipe to raise exception
        mock_pipe.side_effect = Exception("Pipeline error")
        mock_sequential.return_value = [Mock()]
        
        node_infos = [Mock()]
        dependencies = build_node_dependencies(node_infos)
        
        assert len(dependencies) == 1
        mock_sequential.assert_called_once_with(node_infos)
    
    def test_has_resource_conflict_between_nodes(self):
        node1 = NodeConstructionInfo(
            node_id="n1",
            request=Mock(),
            creates_files={"file1.txt", "file2.txt"},
            creates_dirs={"dir1"},
            reads_files={"file3.txt"},
            requires_dirs={"dir2"},
            metadata={},
            original_index=0
        )
        
        # No conflict
        node2 = NodeConstructionInfo(
            node_id="n2",
            request=Mock(),
            creates_files={"file4.txt"},
            creates_dirs={"dir3"},
            reads_files={"file5.txt"},
            requires_dirs={"dir4"},
            metadata={},
            original_index=1
        )
        assert _has_resource_conflict_between_nodes(node1, node2) is False
        
        # Creation conflict - same file
        node3 = NodeConstructionInfo(
            node_id="n3",
            request=Mock(),
            creates_files={"file1.txt"},  # Conflicts with node1
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set(),
            metadata={},
            original_index=2
        )
        assert _has_resource_conflict_between_nodes(node1, node3) is True
        
        # Read-write conflict
        node4 = NodeConstructionInfo(
            node_id="n4",
            request=Mock(),
            creates_files=set(),
            creates_dirs=set(),
            reads_files={"file1.txt"},  # Reads what node1 creates
            requires_dirs=set(),
            metadata={},
            original_index=3
        )
        assert _has_resource_conflict_between_nodes(node1, node4) is True
    
    def test_create_graph_metadata(self):
        node_infos = [
            NodeConstructionInfo(
                node_id="n1",
                request=Mock(__class__=type('TestRequest', (), {})),
                creates_files={"file1.txt", "file2.txt"},
                creates_dirs={"dir1"},
                reads_files={"file3.txt"},
                requires_dirs={"dir2"},
                metadata={},
                original_index=0
            ),
            NodeConstructionInfo(
                node_id="n2",
                request=Mock(__class__=type('TestRequest', (), {})),
                creates_files={"file4.txt"},
                creates_dirs={"dir1"},  # Same dir as n1
                reads_files={"file1.txt"},  # Reads from n1
                requires_dirs={"dir3"},
                metadata={},
                original_index=1
            )
        ]
        
        # Mock dependencies with type
        dep1 = Mock()
        dep1.dependency_type = Mock(value="FILE_CREATION")
        
        dependencies = [dep1]
        
        metadata = create_graph_metadata(node_infos, dependencies)
        
        assert metadata["total_nodes"] == 2
        assert metadata["total_dependencies"] == 1
        assert "Mock" in metadata["node_types"]
        assert metadata["node_types"]["Mock"] == 2
        assert "FILE_CREATION" in metadata["dependency_types"]
        assert metadata["resource_stats"]["creates_files"] == 3  # file1, file2, file4
        assert metadata["resource_stats"]["creates_dirs"] == 1   # dir1 (unique)
        assert "complexity_score" in metadata
    
    def test_calculate_graph_complexity(self):
        # Empty graph
        assert _calculate_graph_complexity([], []) == 0.0
        
        # Simple graph
        node_infos = [
            NodeConstructionInfo(
                node_id="n1",
                request=Mock(),
                creates_files={"file1.txt"},
                creates_dirs=set(),
                reads_files=set(),
                requires_dirs=set(),
                metadata={},
                original_index=0
            )
        ]
        dependencies = []
        
        complexity = _calculate_graph_complexity(node_infos, dependencies)
        assert complexity == 0.5  # (0 + 1/1) / 2
        
        # Complex graph
        node_infos = [
            NodeConstructionInfo(
                node_id=f"n{i}",
                request=Mock(),
                creates_files={f"file{i}.txt"},
                creates_dirs={f"dir{i}"},
                reads_files={f"file{i-1}.txt"} if i > 0 else set(),
                requires_dirs={f"dir{i-1}"} if i > 0 else set(),
                metadata={},
                original_index=i
            )
            for i in range(3)
        ]
        dependencies = [Mock(), Mock(), Mock(), Mock()]  # 4 dependencies
        
        complexity = _calculate_graph_complexity(node_infos, dependencies)
        # Base: 4/3 = 1.33, Resource: 6/3 = 2.0, Average: 1.67
        assert complexity > 1.5
    
    def test_validate_graph_construction_valid(self):
        node1 = Mock()
        node1.node_id = "n1"
        node1.request = Mock()
        
        node2 = Mock()
        node2.node_id = "n2"
        node2.request = Mock()
        
        dep = Mock()
        dep.from_node = "n1"
        dep.to_node = "n2"
        
        result = GraphConstructionResult(
            nodes=[node1, node2],
            dependencies=[dep],
            metadata={},
            errors=[],
            warnings=[]
        )
        
        errors = validate_graph_construction(result)
        assert errors == []
    
    def test_validate_graph_construction_invalid(self):
        # Various validation errors
        node1 = Mock()
        node1.node_id = "n1"
        node1.request = None  # Invalid
        
        node2 = Mock()
        node2.node_id = "n1"  # Duplicate ID
        node2.request = Mock()
        
        node3 = type('MockNode', (), {})()  # Missing node_id
        
        dep1 = Mock()
        dep1.from_node = "n1"
        dep1.to_node = "n1"  # Self-dependency
        
        dep2 = Mock()
        dep2.from_node = "n1"
        dep2.to_node = "n99"  # Unknown node
        
        dep3 = type('MockDep', (), {})()  # Missing attributes
        
        result = GraphConstructionResult(
            nodes=[node1, node2, node3],
            dependencies=[dep1, dep2, dep3],
            metadata={},
            errors=[],
            warnings=[]
        )
        
        errors = validate_graph_construction(result)
        
        assert any("None request" in e for e in errors)
        assert any("Duplicate node_id" in e for e in errors)
        assert any("missing node_id" in e for e in errors)
        assert any("Self-dependency" in e for e in errors)
        assert any("unknown to_node" in e for e in errors)
        assert any("missing from_node or to_node" in e for e in errors)
    
    def test_optimize_graph_structure_success(self):
        # Create duplicate dependencies
        dep1 = Mock()
        dep1.from_node = "n1"
        dep1.to_node = "n2"
        
        dep2 = Mock()
        dep2.from_node = "n1"
        dep2.to_node = "n2"  # Duplicate
        
        dep3 = Mock()
        dep3.from_node = "n2"
        dep3.to_node = "n3"
        
        original_result = GraphConstructionResult(
            nodes=[Mock()],
            dependencies=[dep1, dep2, dep3],
            metadata={"original": True},
            errors=[],
            warnings=[]
        )
        
        optimized = optimize_graph_structure(original_result)
        
        assert optimized.is_success is True
        assert len(optimized.dependencies) == 2  # Duplicate removed
        assert optimized.metadata["optimized"] is True
        assert optimized.metadata["original_dependencies"] == 3
        assert optimized.metadata["optimized_dependencies"] == 2
    
    def test_optimize_graph_structure_failed_graph(self):
        # Don't optimize failed graphs
        failed_result = GraphConstructionResult(
            nodes=[],
            dependencies=[],
            metadata={},
            errors=["Error"],
            warnings=[]
        )
        
        optimized = optimize_graph_structure(failed_result)
        assert optimized == failed_result  # Unchanged
    
    def test_remove_redundant_dependencies(self):
        dep1 = Mock()
        dep1.from_node = "n1"
        dep1.to_node = "n2"
        
        dep2 = Mock()
        dep2.from_node = "n1"
        dep2.to_node = "n2"  # Duplicate
        
        dep3 = Mock()
        dep3.from_node = "n2"
        dep3.to_node = "n3"
        
        dep4 = type('MockDep', (), {})()  # Missing attributes
        
        unique = _remove_redundant_dependencies([dep1, dep2, dep3, dep4])
        
        assert len(unique) == 2  # dep1 and dep3 only
        assert dep1 in unique
        assert dep3 in unique
        assert dep2 not in unique  # Duplicate removed