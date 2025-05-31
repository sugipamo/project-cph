"""
RequestExecutionGraphのテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.env.workflow.request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
from src.operations.result.result import OperationResult


class TestRequestExecutionGraph:
    """RequestExecutionGraphのテストクラス"""
    
    @pytest.fixture
    def mock_request(self):
        """モックリクエストを生成"""
        request = Mock()
        request.execute.return_value = OperationResult(success=True)
        request.allow_failure = False
        return request
    
    @pytest.fixture
    def simple_graph(self, mock_request):
        """シンプルなグラフを生成"""
        graph = RequestExecutionGraph()
        
        # ノードを追加
        node1 = RequestNode(
            id="node1",
            request=mock_request,
            creates_files={"file1.txt"}
        )
        node2 = RequestNode(
            id="node2", 
            request=mock_request,
            reads_files={"file1.txt"}
        )
        
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        # 依存関係を追加
        edge = DependencyEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.FILE_CREATION,
            resource_path="file1.txt"
        )
        graph.add_dependency(edge)
        
        return graph
    
    def test_add_request_node(self, mock_request):
        """ノード追加のテスト"""
        graph = RequestExecutionGraph()
        node = RequestNode(id="test", request=mock_request)
        
        graph.add_request_node(node)
        
        assert "test" in graph.nodes
        assert graph.nodes["test"] == node
        assert "test" in graph.adjacency_list
    
    def test_add_dependency(self):
        """依存関係追加のテスト"""
        graph = RequestExecutionGraph()
        
        # ノードを追加
        node1 = RequestNode(id="node1", request=Mock())
        node2 = RequestNode(id="node2", request=Mock())
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        # 依存関係を追加
        edge = DependencyEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.EXECUTION_ORDER
        )
        graph.add_dependency(edge)
        
        assert len(graph.edges) == 1
        assert "node2" in graph.adjacency_list.get("node1", set())
    
    def test_detect_cycles(self, mock_request):
        """循環依存検出のテスト"""
        graph = RequestExecutionGraph()
        
        # 循環するグラフを作成
        for i in range(3):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("node0", "node1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node0", DependencyType.EXECUTION_ORDER))
        
        cycles = graph.detect_cycles()
        assert len(cycles) > 0
        assert set(cycles[0]) == {"node0", "node1", "node2"}
    
    def test_get_execution_order(self, simple_graph):
        """実行順序取得のテスト"""
        order = simple_graph.get_execution_order()
        
        assert len(order) == 2
        assert order.index("node1") < order.index("node2")
    
    def test_get_execution_order_with_cycle(self, mock_request):
        """循環依存がある場合の実行順序取得テスト"""
        graph = RequestExecutionGraph()
        
        # 循環するグラフを作成
        node1 = RequestNode(id="node1", request=mock_request)
        node2 = RequestNode(id="node2", request=mock_request)
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node1", DependencyType.EXECUTION_ORDER))
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            graph.get_execution_order()
    
    def test_get_parallel_groups(self, mock_request):
        """並列実行グループ取得のテスト"""
        graph = RequestExecutionGraph()
        
        # 並列実行可能なグラフを作成
        # node1 -> node3
        # node2 -> node3
        # node1とnode2は並列実行可能
        for i in range(1, 4):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))
        
        groups = graph.get_parallel_groups()
        
        assert len(groups) == 2
        assert set(groups[0]) == {"node1", "node2"}
        assert groups[1] == ["node3"]
    
    def test_execute_sequential(self, simple_graph, mock_request):
        """順次実行のテスト"""
        driver = Mock()
        results = simple_graph.execute_sequential(driver=driver)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert mock_request.execute.call_count == 2
        
        # ノードのステータスが更新されているか確認
        assert simple_graph.nodes["node1"].status == "completed"
        assert simple_graph.nodes["node2"].status == "completed"
    
    def test_execute_sequential_with_failure(self, mock_request):
        """失敗を含む順次実行のテスト"""
        graph = RequestExecutionGraph()
        
        # 失敗するリクエストを作成
        failing_request = Mock()
        failing_request.execute.return_value = OperationResult(success=False, error_message="Test error")
        failing_request.allow_failure = False
        
        # ノードを追加
        node1 = RequestNode(id="node1", request=failing_request)
        node2 = RequestNode(id="node2", request=mock_request)
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        
        results = graph.execute_sequential()
        
        assert len(results) == 1  # node2は実行されない
        assert not results[0].success
        assert graph.nodes["node1"].status == "failed"
        assert graph.nodes["node2"].status == "skipped"
    
    def test_execute_parallel(self, mock_request):
        """並列実行のテスト"""
        graph = RequestExecutionGraph()
        
        # 並列実行可能なグラフを作成
        for i in range(3):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("node0", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        
        results = graph.execute_parallel(max_workers=2)
        
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(node.status == "completed" for node in graph.nodes.values())
    
    def test_get_dependencies(self, simple_graph):
        """依存関係取得のテスト"""
        deps = simple_graph.get_dependencies("node2")
        assert deps == ["node1"]
        
        deps = simple_graph.get_dependencies("node1")
        assert deps == []
    
    def test_get_dependents(self, simple_graph):
        """依存するノード取得のテスト"""
        deps = simple_graph.get_dependents("node1")
        assert deps == ["node2"]
        
        deps = simple_graph.get_dependents("node2")
        assert deps == []
    
    def test_remove_dependency(self, simple_graph):
        """依存関係削除のテスト"""
        simple_graph.remove_dependency("node1", "node2")
        
        assert "node2" not in simple_graph.adjacency_list.get("node1", set())
        assert len(simple_graph.edges) == 0
    
    def test_visualize(self, simple_graph):
        """可視化文字列生成のテスト"""
        viz = simple_graph.visualize()
        
        assert "Request Execution Graph:" in viz
        assert "Nodes: 2" in viz
        assert "Edges: 1" in viz
        assert "node1" in viz
        assert "node2" in viz
        assert "file_creation" in viz
    
    def test_complex_dependency_graph(self, mock_request):
        """複雑な依存関係グラフのテスト"""
        graph = RequestExecutionGraph()
        
        # より複雑なグラフを作成
        # node1 -> node2 -> node4
        #       -> node3 -> node4
        for i in range(1, 5):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node3", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node4", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.EXECUTION_ORDER))
        
        # 実行順序の確認
        order = graph.get_execution_order()
        assert order.index("node1") < order.index("node2")
        assert order.index("node1") < order.index("node3")
        assert order.index("node2") < order.index("node4")
        assert order.index("node3") < order.index("node4")
        
        # 並列グループの確認
        groups = graph.get_parallel_groups()
        assert ["node1"] in groups
        assert set(groups[1]) == {"node2", "node3"} or groups[1] == ["node2"] or groups[1] == ["node3"]
        assert ["node4"] in groups