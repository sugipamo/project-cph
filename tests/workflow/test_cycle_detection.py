"""
循環依存検出とエラーメッセージのテスト
"""
import pytest
from unittest.mock import Mock
from src.env.workflow.request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
from src.operations.base_request import BaseRequest


class TestCycleDetection:
    """循環依存検出のテストクラス"""
    
    @pytest.fixture
    def mock_request(self):
        """モックリクエストを生成"""
        request = Mock(spec=BaseRequest)
        request.operation_type = Mock()
        request.allow_failure = False
        return request
    
    def test_simple_cycle_detection(self, mock_request):
        """シンプルな循環依存の検出テスト"""
        graph = RequestExecutionGraph()
        
        # 3ノードの循環を作成
        for i in range(3):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        # node0 -> node1 -> node2 -> node0 の循環
        graph.add_dependency(DependencyEdge("node0", "node1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node0", DependencyType.EXECUTION_ORDER))
        
        # 循環検出
        cycles = graph.detect_cycles()
        assert len(cycles) > 0
        
        # 循環の内容確認
        cycle = cycles[0]
        assert len(cycle) == 3
        assert set(cycle) == {"node0", "node1", "node2"}
    
    def test_multiple_cycles_detection(self, mock_request):
        """複数の循環依存の検出テスト"""
        graph = RequestExecutionGraph()
        
        # 6ノードで2つの循環を作成
        for i in range(6):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        # 最初の循環: node0 -> node1 -> node2 -> node0
        graph.add_dependency(DependencyEdge("node0", "node1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node2", "node0", DependencyType.EXECUTION_ORDER))
        
        # 2番目の循環: node3 -> node4 -> node5 -> node3
        graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node4", "node5", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node5", "node3", DependencyType.EXECUTION_ORDER))
        
        # 循環検出
        cycles = graph.detect_cycles()
        assert len(cycles) >= 2  # 少なくとも2つの循環が検出される
    
    def test_self_cycle_detection(self, mock_request):
        """自己循環の検出テスト"""
        graph = RequestExecutionGraph()
        
        node = RequestNode(id="node0", request=mock_request)
        graph.add_request_node(node)
        
        # 自己循環を作成
        graph.add_dependency(DependencyEdge("node0", "node0", DependencyType.EXECUTION_ORDER))
        
        cycles = graph.detect_cycles()
        assert len(cycles) > 0
        assert cycles[0] == ["node0"]
    
    def test_no_cycle_detection(self, mock_request):
        """循環がない場合のテスト"""
        graph = RequestExecutionGraph()
        
        # 線形チェーンを作成（循環なし）
        for i in range(5):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
            
            if i > 0:
                graph.add_dependency(DependencyEdge(
                    f"node{i-1}", f"node{i}", DependencyType.EXECUTION_ORDER
                ))
        
        cycles = graph.detect_cycles()
        assert len(cycles) == 0
    
    def test_cycle_analysis_detailed(self, mock_request):
        """循環分析の詳細テスト"""
        graph = RequestExecutionGraph()
        
        # ファイル依存の循環を作成
        node1 = RequestNode(
            id="create_file1",
            request=mock_request,
            creates_files={"file1.txt"},
            reads_files={"file2.txt"}
        )
        node2 = RequestNode(
            id="create_file2",
            request=mock_request,
            creates_files={"file2.txt"},
            reads_files={"file1.txt"}
        )
        
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        # 相互ファイル依存を作成
        graph.add_dependency(DependencyEdge(
            "create_file1", "create_file2",
            DependencyType.FILE_CREATION,
            resource_path="file1.txt",
            description="file1.txt must be created before file2.txt can be read"
        ))
        graph.add_dependency(DependencyEdge(
            "create_file2", "create_file1",
            DependencyType.FILE_CREATION,
            resource_path="file2.txt",
            description="file2.txt must be created before file1.txt can be read"
        ))
        
        # 循環分析
        analysis = graph.analyze_cycles()
        
        assert analysis['has_cycles'] is True
        assert analysis['cycle_count'] >= 1
        
        cycle = analysis['cycles'][0]
        assert cycle['length'] == 2
        assert set(cycle['nodes']) == {"create_file1", "create_file2"}
        
        # 依存関係の詳細確認
        dependencies = cycle['dependencies']
        assert len(dependencies) == 2
        
        # ファイル作成依存が記録されていることを確認
        dep_types = [dep['type'] for dep in dependencies]
        assert 'file_creation' in dep_types
    
    def test_cycle_error_message_formatting(self, mock_request):
        """循環依存エラーメッセージのフォーマットテスト"""
        graph = RequestExecutionGraph()
        
        # 3ノードの循環を作成
        node_names = ["mkdir_task", "copy_task", "remove_task"]
        for name in node_names:
            node = RequestNode(id=name, request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge(
            "mkdir_task", "copy_task", 
            DependencyType.DIRECTORY_CREATION,
            resource_path="/tmp/test",
            description="Directory must be created before copying"
        ))
        graph.add_dependency(DependencyEdge(
            "copy_task", "remove_task",
            DependencyType.FILE_CREATION,
            resource_path="/tmp/test/file.txt",
            description="File must be copied before removal"
        ))
        graph.add_dependency(DependencyEdge(
            "remove_task", "mkdir_task",
            DependencyType.EXECUTION_ORDER,
            description="Task must be removed before creating directory"
        ))
        
        # エラーメッセージのフォーマット
        error_message = graph.format_cycle_error()
        
        # エラーメッセージの内容確認
        assert "Circular dependency detected" in error_message
        assert "mkdir_task" in error_message
        assert "copy_task" in error_message
        assert "remove_task" in error_message
        assert "Resolution suggestions" in error_message
        assert "dir_creation" in error_message
        assert "/tmp/test" in error_message
    
    def test_execution_order_with_cycle_error(self, mock_request):
        """循環がある場合の実行順序取得エラーテスト"""
        graph = RequestExecutionGraph()
        
        # 循環を作成
        for i in range(2):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("node0", "node1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node0", DependencyType.EXECUTION_ORDER))
        
        # ValueError が発生することを確認
        with pytest.raises(ValueError) as exc_info:
            graph.get_execution_order()
        
        error_message = str(exc_info.value)
        assert "Circular dependency detected" in error_message
        assert "node0" in error_message
        assert "node1" in error_message
    
    def test_parallel_groups_with_cycle_error(self, mock_request):
        """循環がある場合の並列グループ取得エラーテスト"""
        graph = RequestExecutionGraph()
        
        # 循環を作成
        for i in range(3):
            node = RequestNode(id=f"task{i}", request=mock_request)
            graph.add_request_node(node)
        
        graph.add_dependency(DependencyEdge("task0", "task1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("task1", "task2", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("task2", "task0", DependencyType.EXECUTION_ORDER))
        
        # ValueError が発生することを確認
        with pytest.raises(ValueError) as exc_info:
            graph.get_parallel_groups()
        
        error_message = str(exc_info.value)
        assert "Circular dependency detected" in error_message
    
    def test_complex_cycle_with_acyclic_parts(self, mock_request):
        """循環部分と非循環部分が混在するグラフのテスト"""
        graph = RequestExecutionGraph()
        
        # 7ノードのグラフ（一部に循環あり）
        for i in range(7):
            node = RequestNode(id=f"node{i}", request=mock_request)
            graph.add_request_node(node)
        
        # 非循環部分
        graph.add_dependency(DependencyEdge("node0", "node1", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        
        # 循環部分 node2 -> node3 -> node4 -> node2
        graph.add_dependency(DependencyEdge("node2", "node3", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node3", "node4", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node4", "node2", DependencyType.EXECUTION_ORDER))
        
        # 非循環部分（続き）
        graph.add_dependency(DependencyEdge("node4", "node5", DependencyType.EXECUTION_ORDER))
        graph.add_dependency(DependencyEdge("node5", "node6", DependencyType.EXECUTION_ORDER))
        
        # 循環検出
        cycles = graph.detect_cycles()
        assert len(cycles) > 0
        
        # 循環部分のみが検出されることを確認
        cycle = cycles[0]
        cycle_nodes = set(cycle)
        assert "node2" in cycle_nodes
        assert "node3" in cycle_nodes
        assert "node4" in cycle_nodes
        
        # 非循環部分のノードは循環に含まれない
        assert "node0" not in cycle_nodes
        assert "node1" not in cycle_nodes
        assert "node5" not in cycle_nodes
        assert "node6" not in cycle_nodes
    
    def test_cycle_analysis_empty_graph(self):
        """空のグラフでの循環分析テスト"""
        graph = RequestExecutionGraph()
        
        analysis = graph.analyze_cycles()
        assert analysis['has_cycles'] is False
        assert analysis['cycles'] == []
        
        error_message = graph.format_cycle_error()
        assert error_message == ""