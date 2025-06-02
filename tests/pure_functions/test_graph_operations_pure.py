"""
グラフ操作純粋関数のテスト
モック不要で実際の動作をテスト
"""
import pytest
from src.pure_functions.graph_operations_pure import (
    GraphNode,
    GraphEdge,
    GraphData,
    TopologicalSortResult,
    ParallelGroup,
    DependencyType,
    create_adjacency_lists_pure,
    detect_cycles_pure,
    topological_sort_pure,
    get_parallel_groups_pure,
    analyze_resource_dependencies_pure,
    validate_graph_pure,
    optimize_graph_pure,
    calculate_graph_metrics_pure
)


class TestGraphNode:
    """GraphNodeのテスト"""
    
    def test_create_simple_node(self):
        """シンプルなノード作成のテスト"""
        node = GraphNode(id="node1")
        
        assert node.id == "node1"
        assert node.creates_files == set()
        assert node.creates_dirs == set()
        assert node.reads_files == set()
        assert node.requires_dirs == set()
        assert node.metadata == {}
    
    def test_create_node_with_resources(self):
        """リソース情報付きノード作成のテスト"""
        node = GraphNode(
            id="node1",
            creates_files={"file1.txt", "file2.txt"},
            creates_dirs={"dir1"},
            reads_files={"input.txt"},
            requires_dirs={"workspace"},
            metadata={"type": "shell"}
        )
        
        assert node.creates_files == {"file1.txt", "file2.txt"}
        assert node.creates_dirs == {"dir1"}
        assert node.reads_files == {"input.txt"}
        assert node.requires_dirs == {"workspace"}
        assert node.metadata == {"type": "shell"}
    
    def test_node_immutability(self):
        """ノードの不変性テスト"""
        node = GraphNode(id="node1")
        
        with pytest.raises(AttributeError):
            node.id = "new_id"


class TestGraphEdge:
    """GraphEdgeのテスト"""
    
    def test_create_simple_edge(self):
        """シンプルなエッジ作成のテスト"""
        edge = GraphEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.FILE_CREATION
        )
        
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.dependency_type == DependencyType.FILE_CREATION
        assert edge.resource_path is None
        assert edge.description is None
    
    def test_create_edge_with_details(self):
        """詳細情報付きエッジ作成のテスト"""
        edge = GraphEdge(
            from_node="creator",
            to_node="reader",
            dependency_type=DependencyType.FILE_CREATION,
            resource_path="data.txt",
            description="File must be created before reading"
        )
        
        assert edge.resource_path == "data.txt"
        assert edge.description == "File must be created before reading"


class TestAdjacencyLists:
    """隣接リスト作成のテスト"""
    
    def test_create_empty_adjacency_lists(self):
        """空の隣接リスト作成のテスト"""
        nodes = {"node1": GraphNode(id="node1")}
        edges = []
        
        forward, reverse = create_adjacency_lists_pure(nodes, edges)
        
        assert forward == {"node1": set()}
        assert reverse == {"node1": set()}
    
    def test_create_adjacency_lists_with_edges(self):
        """エッジ付き隣接リスト作成のテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node3", DependencyType.DIRECTORY_CREATION)
        ]
        
        forward, reverse = create_adjacency_lists_pure(nodes, edges)
        
        assert forward["node1"] == {"node2"}
        assert forward["node2"] == {"node3"}
        assert forward["node3"] == set()
        
        assert reverse["node1"] == set()
        assert reverse["node2"] == {"node1"}
        assert reverse["node3"] == {"node2"}


class TestCycleDetection:
    """循環検出のテスト"""
    
    def test_no_cycles(self):
        """循環なしのテスト"""
        adjacency = {
            "node1": {"node2"},
            "node2": {"node3"},
            "node3": set()
        }
        
        cycles = detect_cycles_pure(adjacency)
        assert cycles == []
    
    def test_simple_cycle(self):
        """シンプルな循環のテスト"""
        adjacency = {
            "node1": {"node2"},
            "node2": {"node3"},
            "node3": {"node1"}
        }
        
        cycles = detect_cycles_pure(adjacency)
        assert len(cycles) >= 1
        # 循環が検出されることを確認（具体的な順序は実装依存）
        assert any("node1" in cycle and "node2" in cycle and "node3" in cycle for cycle in cycles)
    
    def test_self_loop(self):
        """自己ループのテスト"""
        adjacency = {
            "node1": {"node1"}
        }
        
        cycles = detect_cycles_pure(adjacency)
        assert len(cycles) >= 1
        assert any("node1" in cycle for cycle in cycles)


class TestTopologicalSort:
    """トポロジカルソートのテスト"""
    
    def test_simple_linear_sort(self):
        """シンプルな線形ソートのテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node3", DependencyType.FILE_CREATION)
        ]
        
        result = topological_sort_pure(nodes, edges)
        
        assert result.is_valid
        assert result.sorted_nodes == ["node1", "node2", "node3"]
        assert result.cycles == []
    
    def test_parallel_branches_sort(self):
        """並列ブランチのソートテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3"),
            "node4": GraphNode(id="node4")
        }
        edges = [
            GraphEdge("node1", "node3", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node4", DependencyType.FILE_CREATION)
        ]
        
        result = topological_sort_pure(nodes, edges)
        
        assert result.is_valid
        assert len(result.sorted_nodes) == 4
        # node1はnode3より前、node2はnode4より前
        assert result.sorted_nodes.index("node1") < result.sorted_nodes.index("node3")
        assert result.sorted_nodes.index("node2") < result.sorted_nodes.index("node4")
    
    def test_cyclic_graph_sort(self):
        """循環グラフのソートテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node3", DependencyType.FILE_CREATION),
            GraphEdge("node3", "node1", DependencyType.FILE_CREATION)  # 循環
        ]
        
        result = topological_sort_pure(nodes, edges)
        
        assert not result.is_valid
        assert len(result.cycles) > 0
        assert result.sorted_nodes == []


class TestParallelGroups:
    """並列グループのテスト"""
    
    def test_linear_execution_groups(self):
        """線形実行グループのテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node3", DependencyType.FILE_CREATION)
        ]
        
        groups = get_parallel_groups_pure(nodes, edges)
        
        assert len(groups) == 3
        assert groups[0].node_ids == {"node1"}
        assert groups[1].node_ids == {"node2"}
        assert groups[2].node_ids == {"node3"}
    
    def test_parallel_execution_groups(self):
        """並列実行グループのテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3"),
            "node4": GraphNode(id="node4")
        }
        edges = [
            GraphEdge("node1", "node3", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node4", DependencyType.FILE_CREATION)
        ]
        
        groups = get_parallel_groups_pure(nodes, edges)
        
        assert len(groups) == 2
        # 最初のグループは並列実行可能
        assert groups[0].node_ids == {"node1", "node2"}
        # 2番目のグループも並列実行可能
        assert groups[1].node_ids == {"node3", "node4"}


class TestResourceDependencyAnalysis:
    """リソース依存関係分析のテスト"""
    
    def test_file_creation_dependency(self):
        """ファイル作成依存のテスト"""
        nodes = {
            "creator": GraphNode(
                id="creator",
                creates_files={"data.txt"}
            ),
            "reader": GraphNode(
                id="reader",
                reads_files={"data.txt"}
            )
        }
        
        edges = analyze_resource_dependencies_pure(nodes)
        
        assert len(edges) == 1
        assert edges[0].from_node == "creator"
        assert edges[0].to_node == "reader"
        assert edges[0].dependency_type == DependencyType.FILE_CREATION
        assert edges[0].resource_path == "data.txt"
    
    def test_directory_creation_dependency(self):
        """ディレクトリ作成依存のテスト"""
        nodes = {
            "mkdir": GraphNode(
                id="mkdir",
                creates_dirs={"output"}
            ),
            "writer": GraphNode(
                id="writer",
                requires_dirs={"output"}
            )
        }
        
        edges = analyze_resource_dependencies_pure(nodes)
        
        assert len(edges) == 1
        assert edges[0].from_node == "mkdir"
        assert edges[0].to_node == "writer"
        assert edges[0].dependency_type == DependencyType.DIRECTORY_CREATION
        assert edges[0].resource_path == "output"
    
    def test_no_dependency_when_no_overlap(self):
        """リソース重複なしの場合の依存なしテスト"""
        nodes = {
            "node1": GraphNode(
                id="node1",
                creates_files={"file1.txt"}
            ),
            "node2": GraphNode(
                id="node2",
                reads_files={"file2.txt"}
            )
        }
        
        edges = analyze_resource_dependencies_pure(nodes)
        assert edges == []


class TestGraphValidation:
    """グラフ検証のテスト"""
    
    def test_valid_graph(self):
        """有効なグラフのテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION)
        ]
        forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
        
        graph_data = GraphData(
            nodes=nodes,
            edges=edges,
            adjacency_list=forward_adj,
            reverse_adjacency_list=reverse_adj
        )
        
        is_valid, errors = validate_graph_pure(graph_data)
        
        assert is_valid
        assert errors == []
    
    def test_empty_graph(self):
        """空のグラフのテスト"""
        graph_data = GraphData(
            nodes={},
            edges=[],
            adjacency_list={},
            reverse_adjacency_list={}
        )
        
        is_valid, errors = validate_graph_pure(graph_data)
        
        assert not is_valid
        assert "Graph has no nodes" in errors
    
    def test_invalid_edge_references(self):
        """無効なエッジ参照のテスト"""
        nodes = {"node1": GraphNode(id="node1")}
        edges = [
            GraphEdge("node1", "nonexistent", DependencyType.FILE_CREATION),
            GraphEdge("nonexistent2", "node1", DependencyType.FILE_CREATION)
        ]
        forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
        
        graph_data = GraphData(
            nodes=nodes,
            edges=edges,
            adjacency_list=forward_adj,
            reverse_adjacency_list=reverse_adj
        )
        
        is_valid, errors = validate_graph_pure(graph_data)
        
        assert not is_valid
        assert any("non-existent" in error for error in errors)


class TestGraphOptimization:
    """グラフ最適化のテスト"""
    
    def test_remove_duplicate_edges(self):
        """重複エッジ除去のテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),  # 重複
            GraphEdge("node1", "node2", DependencyType.DIRECTORY_CREATION)  # 異なるタイプ
        ]
        forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
        
        graph_data = GraphData(
            nodes=nodes,
            edges=edges,
            adjacency_list=forward_adj,
            reverse_adjacency_list=reverse_adj
        )
        
        optimized = optimize_graph_pure(graph_data)
        
        assert len(optimized.edges) == 2  # 重複が除去される
        # 異なるタイプのエッジは残る
        edge_types = {edge.dependency_type for edge in optimized.edges}
        assert DependencyType.FILE_CREATION in edge_types
        assert DependencyType.DIRECTORY_CREATION in edge_types


class TestGraphMetrics:
    """グラフメトリクスのテスト"""
    
    def test_simple_graph_metrics(self):
        """シンプルなグラフのメトリクステスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2"),
            "node3": GraphNode(id="node3")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION),
            GraphEdge("node1", "node3", DependencyType.FILE_CREATION),
            GraphEdge("node2", "node3", DependencyType.DIRECTORY_CREATION)
        ]
        forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
        
        graph_data = GraphData(
            nodes=nodes,
            edges=edges,
            adjacency_list=forward_adj,
            reverse_adjacency_list=reverse_adj
        )
        
        metrics = calculate_graph_metrics_pure(graph_data)
        
        assert metrics['node_count'] == 3
        assert metrics['edge_count'] == 3
        assert metrics['max_out_degree'] == 2  # node1が2つの出力エッジ
        assert metrics['max_in_degree'] == 2   # node3が2つの入力エッジ
        assert metrics['has_cycles'] is False


class TestPureFunctionProperties:
    """純粋関数の特性テスト"""
    
    def test_deterministic_behavior(self):
        """決定論的動作のテスト"""
        nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2")
        }
        edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION)
        ]
        
        # 同じ入力に対して常に同じ出力
        result1 = topological_sort_pure(nodes, edges)
        result2 = topological_sort_pure(nodes, edges)
        
        assert result1.sorted_nodes == result2.sorted_nodes
        assert result1.is_valid == result2.is_valid
        
        groups1 = get_parallel_groups_pure(nodes, edges)
        groups2 = get_parallel_groups_pure(nodes, edges)
        
        assert len(groups1) == len(groups2)
        for g1, g2 in zip(groups1, groups2):
            assert g1.node_ids == g2.node_ids
    
    def test_no_side_effects(self):
        """副作用なしのテスト"""
        original_nodes = {
            "node1": GraphNode(id="node1"),
            "node2": GraphNode(id="node2")
        }
        original_edges = [
            GraphEdge("node1", "node2", DependencyType.FILE_CREATION)
        ]
        
        # 関数実行
        topological_sort_pure(original_nodes, original_edges)
        get_parallel_groups_pure(original_nodes, original_edges)
        analyze_resource_dependencies_pure(original_nodes)
        
        # 元のデータが変更されていないことを確認
        assert len(original_nodes) == 2
        assert len(original_edges) == 1
        assert original_nodes["node1"].id == "node1"
        assert original_edges[0].from_node == "node1"