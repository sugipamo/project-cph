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
        \n        # 循環検出\n        cycles = graph.detect_cycles()\n        assert len(cycles) >= 2  # 少なくとも2つの循環が検出される\n    \n    def test_self_cycle_detection(self, mock_request):\n        \"\"\"自己循環の検出テスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        node = RequestNode(id=\"node0\", request=mock_request)\n        graph.add_request_node(node)\n        \n        # 自己循環を作成\n        graph.add_dependency(DependencyEdge(\"node0\", \"node0\", DependencyType.EXECUTION_ORDER))\n        \n        cycles = graph.detect_cycles()\n        assert len(cycles) > 0\n        assert cycles[0] == [\"node0\"]\n    \n    def test_no_cycle_detection(self, mock_request):\n        \"\"\"循環がない場合のテスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 線形チェーンを作成（循環なし）\n        for i in range(5):\n            node = RequestNode(id=f\"node{i}\", request=mock_request)\n            graph.add_request_node(node)\n            \n            if i > 0:\n                graph.add_dependency(DependencyEdge(\n                    f\"node{i-1}\", f\"node{i}\", DependencyType.EXECUTION_ORDER\n                ))\n        \n        cycles = graph.detect_cycles()\n        assert len(cycles) == 0\n    \n    def test_cycle_analysis_detailed(self, mock_request):\n        \"\"\"循環分析の詳細テスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # ファイル依存の循環を作成\n        node1 = RequestNode(\n            id=\"create_file1\",\n            request=mock_request,\n            creates_files={\"file1.txt\"},\n            reads_files={\"file2.txt\"}\n        )\n        node2 = RequestNode(\n            id=\"create_file2\",\n            request=mock_request,\n            creates_files={\"file2.txt\"},\n            reads_files={\"file1.txt\"}\n        )\n        \n        graph.add_request_node(node1)\n        graph.add_request_node(node2)\n        \n        # 相互ファイル依存を作成\n        graph.add_dependency(DependencyEdge(\n            \"create_file1\", \"create_file2\",\n            DependencyType.FILE_CREATION,\n            resource_path=\"file1.txt\",\n            description=\"file1.txt must be created before file2.txt can be read\"\n        ))\n        graph.add_dependency(DependencyEdge(\n            \"create_file2\", \"create_file1\",\n            DependencyType.FILE_CREATION,\n            resource_path=\"file2.txt\",\n            description=\"file2.txt must be created before file1.txt can be read\"\n        ))\n        \n        # 循環分析\n        analysis = graph.analyze_cycles()\n        \n        assert analysis['has_cycles'] is True\n        assert analysis['cycle_count'] >= 1\n        \n        cycle = analysis['cycles'][0]\n        assert cycle['length'] == 2\n        assert set(cycle['nodes']) == {\"create_file1\", \"create_file2\"}\n        \n        # 依存関係の詳細確認\n        dependencies = cycle['dependencies']\n        assert len(dependencies) == 2\n        \n        # ファイル作成依存が記録されていることを確認\n        dep_types = [dep['type'] for dep in dependencies]\n        assert 'file_creation' in dep_types\n    \n    def test_cycle_error_message_formatting(self, mock_request):\n        \"\"\"循環依存エラーメッセージのフォーマットテスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 3ノードの循環を作成\n        node_names = [\"mkdir_task\", \"copy_task\", \"remove_task\"]\n        for name in node_names:\n            node = RequestNode(id=name, request=mock_request)\n            graph.add_request_node(node)\n        \n        graph.add_dependency(DependencyEdge(\n            \"mkdir_task\", \"copy_task\", \n            DependencyType.DIRECTORY_CREATION,\n            resource_path=\"/tmp/test\",\n            description=\"Directory must be created before copying\"\n        ))\n        graph.add_dependency(DependencyEdge(\n            \"copy_task\", \"remove_task\",\n            DependencyType.FILE_CREATION,\n            resource_path=\"/tmp/test/file.txt\",\n            description=\"File must be copied before removal\"\n        ))\n        graph.add_dependency(DependencyEdge(\n            \"remove_task\", \"mkdir_task\",\n            DependencyType.EXECUTION_ORDER,\n            description=\"Task must be removed before creating directory\"\n        ))\n        \n        # エラーメッセージのフォーマット\n        error_message = graph.format_cycle_error()\n        \n        # エラーメッセージの内容確認\n        assert \"Circular dependency detected\" in error_message\n        assert \"mkdir_task\" in error_message\n        assert \"copy_task\" in error_message\n        assert \"remove_task\" in error_message\n        assert \"Resolution suggestions\" in error_message\n        assert \"DIRECTORY_CREATION\" in error_message or \"directory_creation\" in error_message\n        assert \"/tmp/test\" in error_message\n    \n    def test_execution_order_with_cycle_error(self, mock_request):\n        \"\"\"循環がある場合の実行順序取得エラーテスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 循環を作成\n        for i in range(2):\n            node = RequestNode(id=f\"node{i}\", request=mock_request)\n            graph.add_request_node(node)\n        \n        graph.add_dependency(DependencyEdge(\"node0\", \"node1\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"node1\", \"node0\", DependencyType.EXECUTION_ORDER))\n        \n        # ValueError が発生することを確認\n        with pytest.raises(ValueError) as exc_info:\n            graph.get_execution_order()\n        \n        error_message = str(exc_info.value)\n        assert \"Circular dependency detected\" in error_message\n        assert \"node0\" in error_message\n        assert \"node1\" in error_message\n    \n    def test_parallel_groups_with_cycle_error(self, mock_request):\n        \"\"\"循環がある場合の並列グループ取得エラーテスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 循環を作成\n        for i in range(3):\n            node = RequestNode(id=f\"task{i}\", request=mock_request)\n            graph.add_request_node(node)\n        \n        graph.add_dependency(DependencyEdge(\"task0\", \"task1\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"task1\", \"task2\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"task2\", \"task0\", DependencyType.EXECUTION_ORDER))\n        \n        # ValueError が発生することを確認\n        with pytest.raises(ValueError) as exc_info:\n            graph.get_parallel_groups()\n        \n        error_message = str(exc_info.value)\n        assert \"Circular dependency detected\" in error_message\n    \n    def test_complex_cycle_with_acyclic_parts(self, mock_request):\n        \"\"\"循環部分と非循環部分が混在するグラフのテスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 7ノードのグラフ（一部に循環あり）\n        for i in range(7):\n            node = RequestNode(id=f\"node{i}\", request=mock_request)\n            graph.add_request_node(node)\n        \n        # 非循環部分\n        graph.add_dependency(DependencyEdge(\"node0\", \"node1\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"node1\", \"node2\", DependencyType.EXECUTION_ORDER))\n        \n        # 循環部分 node2 -> node3 -> node4 -> node2\n        graph.add_dependency(DependencyEdge(\"node2\", \"node3\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"node3\", \"node4\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"node4\", \"node2\", DependencyType.EXECUTION_ORDER))\n        \n        # 非循環部分（続き）\n        graph.add_dependency(DependencyEdge(\"node4\", \"node5\", DependencyType.EXECUTION_ORDER))\n        graph.add_dependency(DependencyEdge(\"node5\", \"node6\", DependencyType.EXECUTION_ORDER))\n        \n        # 循環検出\n        cycles = graph.detect_cycles()\n        assert len(cycles) > 0\n        \n        # 循環部分のみが検出されることを確認\n        cycle = cycles[0]\n        cycle_nodes = set(cycle)\n        assert \"node2\" in cycle_nodes\n        assert \"node3\" in cycle_nodes\n        assert \"node4\" in cycle_nodes\n        \n        # 非循環部分のノードは循環に含まれない\n        assert \"node0\" not in cycle_nodes\n        assert \"node1\" not in cycle_nodes\n        assert \"node5\" not in cycle_nodes\n        assert \"node6\" not in cycle_nodes\n    \n    def test_cycle_analysis_empty_graph(self):\n        \"\"\"空のグラフでの循環分析テスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        analysis = graph.analyze_cycles()\n        assert analysis['has_cycles'] is False\n        assert analysis['cycles'] == []\n        \n        error_message = graph.format_cycle_error()\n        assert error_message == \"\"