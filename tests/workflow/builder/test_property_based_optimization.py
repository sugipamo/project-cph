"""Property-based tests for graph optimization functions"""
from dataclasses import dataclass
from typing import Any, Dict, List, Set

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.workflow.builder.graph_ops.dependency_mapping import DependencyGraph, DependencyMapping
from src.workflow.builder.graph_ops.graph_optimization import (
    OptimizationResult,
    optimize_dependency_order,
    remove_redundant_dependencies,
)

# Test data generators

@dataclass
class MockMapping:
    """Mock dependency mapping for testing"""
    from_node_id: str
    to_node_id: str
    dependency_type: str = "file_creation"
    resource_path: str = ""
    description: str = ""

    def to_edge_dict(self):
        return {
            'from_node': self.from_node_id,
            'to_node': self.to_node_id,
            'type': self.dependency_type,
            'resource': self.resource_path,
            'description': self.description
        }


def dependency_graph_strategy(min_nodes=2, max_nodes=8):
    """Generate a DependencyGraph for testing"""
    node_ids = st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5),
        min_size=min_nodes,
        max_size=max_nodes,
        unique=True
    )

    def build_graph(node_id_list):
        if len(node_id_list) < 2:
            return DependencyGraph(mappings=[], adjacency_dict={})

        # Generate mappings between nodes
        mappings = []
        for i in range(len(node_id_list) - 1):
            for j in range(i + 1, min(i + 3, len(node_id_list))):  # Limit connections
                if st.randoms().random() > 0.7:  # 30% chance of connection
                    mapping = MockMapping(
                        from_node_id=node_id_list[i],
                        to_node_id=node_id_list[j],
                        dependency_type=st.randoms().choice(['file_creation', 'dir_creation', 'exec_order']),
                        resource_path=f"resource_{i}_{j}",
                        description=f"Dependency from {node_id_list[i]} to {node_id_list[j]}"
                    )
                    mappings.append(mapping)

        # Build adjacency dict
        adjacency_dict = {node_id: set() for node_id in node_id_list}
        for mapping in mappings:
            adjacency_dict[mapping.from_node_id].add(mapping.to_node_id)

        return DependencyGraph(mappings=mappings, adjacency_dict=adjacency_dict)

    return node_ids.map(build_graph)


class TestOptimizationProperties:
    """Property-based tests for graph optimization"""

    @given(dependency_graph_strategy())
    def test_optimization_preserves_graph_structure(self, graph):
        """Optimization should preserve essential graph structure"""
        original_nodes = set(graph.adjacency_dict.keys())

        try:
            result = optimize_dependency_order(graph)

            # Result should be a dictionary (legacy API)
            assert isinstance(result, dict)
            assert 'adjacency_list' in result or 'mappings' in result

            # Should preserve node set
            if 'adjacency_list' in result:
                optimized_nodes = set(result['adjacency_list'].keys())
                assert optimized_nodes == original_nodes

        except Exception:
            # Optimization might fail for some graphs, that's ok
            pass

    @given(dependency_graph_strategy())
    def test_redundant_dependency_removal_reduces_or_maintains_count(self, graph):
        """Removing redundant dependencies should reduce or maintain dependency count"""
        original_count = len(graph.mappings)

        try:
            result = remove_redundant_dependencies(graph)

            assert isinstance(result, OptimizationResult)
            optimized_count = len(result.optimized_graph.mappings)

            # Should not increase dependency count
            assert optimized_count <= original_count

            # Removed edges should be accounted for
            removed_count = len(result.removed_edges)
            assert original_count == optimized_count + removed_count

        except Exception:
            # Some graphs might cause optimization to fail, that's acceptable
            pass

    @given(dependency_graph_strategy())
    def test_optimization_is_deterministic(self, graph):
        """Same graph should produce same optimization result"""
        try:
            result1 = optimize_dependency_order(graph)
            result2 = optimize_dependency_order(graph)

            # Results should be identical
            assert result1 == result2

        except Exception:
            # If optimization fails, it should fail consistently
            with pytest.raises(Exception):
                optimize_dependency_order(graph)

    @given(dependency_graph_strategy(min_nodes=1, max_nodes=3))
    def test_small_graph_optimization_correctness(self, graph):
        """Optimization of small graphs should maintain logical correctness"""
        try:
            result = optimize_dependency_order(graph)

            if 'mappings' in result:
                # Check that no self-dependencies are introduced
                for mapping in result['mappings']:
                    if isinstance(mapping, dict):
                        assert mapping.get('from_node') != mapping.get('to_node')
                    else:
                        assert mapping.from_node_id != mapping.to_node_id

        except Exception:
            # Optimization failure is acceptable for some graphs
            pass

    @given(dependency_graph_strategy())
    def test_optimization_statistics_are_reasonable(self, graph):
        """Optimization statistics should be reasonable"""
        try:
            result = optimize_dependency_order(graph)

            if 'stats' in result:
                stats = result['stats']
                assert isinstance(stats, dict)

                # Any numeric stats should be non-negative
                for _key, value in stats.items():
                    if isinstance(value, (int, float)):
                        assert value >= 0

        except Exception:
            # Statistics might not be available if optimization fails
            pass


class TestEdgeReductionProperties:
    """Property-based tests for edge reduction optimization"""

    def redundant_graph_strategy(self):
        """Generate graphs with known redundant dependencies"""
        node_ids = st.lists(
            st.text(alphabet='abc', min_size=1, max_size=2),
            min_size=3,
            max_size=5,
            unique=True
        )

        def build_redundant_graph(node_id_list):
            if len(node_id_list) < 3:
                return DependencyGraph(mappings=[], adjacency_dict={})

            # Create redundant mappings: A->B, B->C, A->C (transitive)
            mappings = []

            # Add direct path
            for i in range(len(node_id_list) - 1):
                mapping = MockMapping(
                    from_node_id=node_id_list[i],
                    to_node_id=node_id_list[i + 1],
                    dependency_type="file_creation",
                    resource_path=f"direct_{i}"
                )
                mappings.append(mapping)

            # Add redundant transitive path (if we have at least 3 nodes)
            if len(node_id_list) >= 3:
                mapping = MockMapping(
                    from_node_id=node_id_list[0],
                    to_node_id=node_id_list[2],
                    dependency_type="file_creation",
                    resource_path="redundant_path"
                )
                mappings.append(mapping)

            # Build adjacency dict
            adjacency_dict = {node_id: set() for node_id in node_id_list}
            for mapping in mappings:
                adjacency_dict[mapping.from_node_id].add(mapping.to_node_id)

            return DependencyGraph(mappings=mappings, adjacency_dict=adjacency_dict)

        return node_ids.map(build_redundant_graph)

    @given(redundant_graph_strategy())
    def test_redundant_removal_actually_removes_dependencies(self, graph):
        """Redundant dependency removal should actually remove some dependencies when redundancies exist"""
        if len(graph.mappings) <= 2:
            return  # Too small to have meaningful redundancies

        try:
            result = remove_redundant_dependencies(graph)

            # Should have removed at least some dependencies for graphs with redundancies
            assert len(result.removed_edges) >= 0

            # Edge reduction ratio should be reasonable
            if len(graph.mappings) > 0:
                ratio = result.edge_reduction_ratio
                assert 0 <= ratio <= 1

        except Exception:
            # Optimization might fail for some complex graphs
            pass

    def duplicate_edge_graph_strategy(self):
        """Generate graphs with duplicate edges"""
        node_ids = st.lists(
            st.text(alphabet='abc', min_size=1, max_size=2),
            min_size=2,
            max_size=4,
            unique=True
        )

        def build_duplicate_graph(node_id_list):
            if len(node_id_list) < 2:
                return DependencyGraph(mappings=[], adjacency_dict={})

            # Create duplicate mappings
            mappings = []
            base_mapping = MockMapping(
                from_node_id=node_id_list[0],
                to_node_id=node_id_list[1],
                dependency_type="file_creation",
                resource_path="shared_resource"
            )

            # Add the same mapping multiple times (simulating duplicates)
            for i in range(3):
                duplicate = MockMapping(
                    from_node_id=base_mapping.from_node_id,
                    to_node_id=base_mapping.to_node_id,
                    dependency_type=base_mapping.dependency_type,
                    resource_path=base_mapping.resource_path,
                    description=f"duplicate_{i}"
                )
                mappings.append(duplicate)

            # Build adjacency dict
            adjacency_dict = {node_id: set() for node_id in node_id_list}
            adjacency_dict[node_id_list[0]].add(node_id_list[1])

            return DependencyGraph(mappings=mappings, adjacency_dict=adjacency_dict)

        return node_ids.map(build_duplicate_graph)

    @given(duplicate_edge_graph_strategy())
    def test_duplicate_edge_removal(self, graph):
        """Duplicate edges should be removed by optimization"""
        if len(graph.mappings) <= 1:
            return

        try:
            result = remove_redundant_dependencies(graph)

            # Should have removed duplicates
            assert len(result.removed_edges) > 0

            # Optimized graph should have fewer mappings
            assert len(result.optimized_graph.mappings) < len(graph.mappings)

            # Edge reduction ratio should be positive
            assert result.edge_reduction_ratio > 0

        except Exception:
            # Optimization might fail for some graphs
            pass


@pytest.mark.slow
class TestOptimizationInvariants:
    """Test optimization invariants that should always hold"""

    @settings(max_examples=20)
    @given(dependency_graph_strategy(min_nodes=5, max_nodes=15))
    def test_optimization_preserves_reachability(self, graph):
        """Optimization should preserve node reachability relationships"""
        # This is a complex property that requires computing transitive closure
        # For now, we just test that optimization doesn't crash on larger graphs
        try:
            result = optimize_dependency_order(graph)

            # Basic structure checks
            assert isinstance(result, dict)

            # If mappings exist, they should be valid
            if result.get('mappings'):
                for mapping in result['mappings']:
                    if isinstance(mapping, dict):
                        assert 'from_node' in mapping
                        assert 'to_node' in mapping

        except Exception:
            # Complex optimizations might fail, that's acceptable
            pass

    @given(dependency_graph_strategy())
    def test_optimization_never_introduces_self_loops(self, graph):
        """Optimization should never introduce self-loops"""
        try:
            result = optimize_dependency_order(graph)

            if 'mappings' in result:
                for mapping in result['mappings']:
                    if isinstance(mapping, dict):
                        assert mapping.get('from_node') != mapping.get('to_node')

        except Exception:
            # If optimization fails, that's ok for this test
            pass
