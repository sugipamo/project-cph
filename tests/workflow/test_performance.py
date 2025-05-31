"""
グラフベースワークフローのパフォーマンステスト
"""
import pytest
import time
from unittest.mock import Mock
from src.env.workflow.request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
from src.env.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult


class TestPerformance:
    """パフォーマンステストクラス"""
    
    def create_mock_request(self, execution_time: float = 0.01) -> Mock:
        """指定された実行時間のモックリクエストを作成"""
        request = Mock(spec=BaseRequest)
        request.operation_type = Mock()
        request.allow_failure = False
        
        def mock_execute(driver=None):
            time.sleep(execution_time)
            return OperationResult(success=True)
        
        request.execute.side_effect = mock_execute
        return request
    
    def test_large_graph_construction_performance(self):
        """大規模グラフの構築パフォーマンステスト"""
        graph = RequestExecutionGraph()
        node_count = 1000
        
        start_time = time.time()
        
        # 1000個のノードを追加
        for i in range(node_count):
            request = self.create_mock_request()
            node = RequestNode(
                id=f"node_{i}",
                request=request,
                creates_files={f"file_{i}.txt"} if i % 3 == 0 else None,
                creates_dirs={f"dir_{i}"} if i % 5 == 0 else None,
                reads_files={f"file_{i-1}.txt"} if i > 0 and (i-1) % 3 == 0 else None
            )\n            graph.add_request_node(node)\n        \n        construction_time = time.time() - start_time\n        \n        # 依存関係を追加（線形チェーン）\n        start_time = time.time()\n        for i in range(node_count - 1):\n            edge = DependencyEdge(\n                from_node=f\"node_{i}\",\n                to_node=f\"node_{i+1}\",\n                dependency_type=DependencyType.EXECUTION_ORDER\n            )\n            graph.add_dependency(edge)\n        \n        dependency_time = time.time() - start_time\n        \n        # 実行順序の取得\n        start_time = time.time()\n        execution_order = graph.get_execution_order()\n        topological_time = time.time() - start_time\n        \n        # 並列グループの取得\n        start_time = time.time()\n        parallel_groups = graph.get_parallel_groups()\n        parallel_time = time.time() - start_time\n        \n        # パフォーマンス検証\n        assert construction_time < 0.5  # 0.5秒以内\n        assert dependency_time < 0.2    # 0.2秒以内\n        assert topological_time < 0.1   # 0.1秒以内\n        assert parallel_time < 0.1      # 0.1秒以内\n        \n        assert len(execution_order) == node_count\n        assert len(parallel_groups) == node_count  # 線形チェーンなので各ノードが独立したグループ\n    \n    def test_parallel_execution_performance(self):\n        \"\"\"並列実行のパフォーマンステスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 並列実行可能な10個のノードを作成\n        execution_time = 0.1  # 各タスクは0.1秒\n        for i in range(10):\n            request = self.create_mock_request(execution_time)\n            node = RequestNode(id=f\"task_{i}\", request=request)\n            graph.add_request_node(node)\n        \n        # 順次実行のテスト\n        start_time = time.time()\n        sequential_results = graph.execute_sequential()\n        sequential_time = time.time() - start_time\n        \n        # 新しいグラフで並列実行のテスト\n        graph2 = RequestExecutionGraph()\n        for i in range(10):\n            request = self.create_mock_request(execution_time)\n            node = RequestNode(id=f\"task_{i}\", request=request)\n            graph2.add_request_node(node)\n        \n        start_time = time.time()\n        parallel_results = graph2.execute_parallel(max_workers=4)\n        parallel_time = time.time() - start_time\n        \n        # 結果の検証\n        assert len(sequential_results) == 10\n        assert len(parallel_results) == 10\n        assert all(r.success for r in sequential_results)\n        assert all(r.success for r in parallel_results)\n        \n        # パフォーマンスの検証（並列実行は順次実行より速いはず）\n        assert parallel_time < sequential_time * 0.6  # 並列実行は少なくとも40%高速\n        \n        # 順次実行は約1秒（10 * 0.1秒）、並列実行は約0.3秒（並列度4なので3グループ）\n        assert sequential_time > 0.8  # 順次実行は最低0.8秒\n        assert parallel_time < 0.5    # 並列実行は最大0.5秒\n    \n    def test_dependency_detection_efficiency(self):\n        \"\"\"依存関係検出の効率性テスト\"\"\"\n        from src.env.workflow.graph_based_workflow_builder import GraphBasedWorkflowBuilder\n        from unittest.mock import Mock\n        \n        # モックコントローラーとオペレーション\n        controller = Mock()\n        controller.env_context = Mock()\n        operations = Mock()\n        \n        builder = GraphBasedWorkflowBuilder(controller, operations)\n        graph = RequestExecutionGraph()\n        \n        # 100個のノードでテスト\n        nodes = []\n        for i in range(100):\n            request = self.create_mock_request()\n            node = RequestNode(\n                id=f\"node_{i}\",\n                request=request,\n                creates_files={f\"file_{i}.txt\"} if i % 2 == 0 else set(),\n                reads_files={f\"file_{i-1}.txt\"} if i > 0 and (i-1) % 2 == 0 else set()\n            )\n            graph.add_request_node(node)\n            nodes.append(node)\n        \n        # 依存関係構築の時間測定\n        start_time = time.time()\n        builder._build_dependencies(graph, nodes)\n        build_time = time.time() - start_time\n        \n        # O(n+m)アルゴリズムなので100ノードでは0.1秒以内であるべき\n        assert build_time < 0.1\n        \n        # 適切な依存関係が構築されていることを確認\n        dependencies_count = len(graph.edges)\n        assert dependencies_count > 0  # 依存関係が検出されている\n    \n    def test_memory_efficiency_large_graph(self):\n        \"\"\"大規模グラフでのメモリ効率性テスト\"\"\"\n        import psutil\n        import os\n        \n        process = psutil.Process(os.getpid())\n        initial_memory = process.memory_info().rss\n        \n        # 1000個のノードを持つグラフを作成\n        graph = RequestExecutionGraph()\n        nodes = []\n        \n        for i in range(1000):\n            request = Mock(spec=BaseRequest)\n            request.operation_type = Mock()\n            \n            # リソース情報が空の場合のメモリ効率性をテスト\n            if i % 10 == 0:\n                # 10個に1個だけリソース情報を持つ\n                node = RequestNode(\n                    id=f\"node_{i}\",\n                    request=request,\n                    creates_files={f\"file_{i}.txt\"},\n                    metadata={\"type\": \"file_creator\"}\n                )\n            else:\n                # その他はリソース情報なし\n                node = RequestNode(id=f\"node_{i}\", request=request)\n            \n            graph.add_request_node(node)\n            nodes.append(node)\n        \n        final_memory = process.memory_info().rss\n        memory_increase = final_memory - initial_memory\n        \n        # 1000ノードで10MB以下のメモリ増加であるべき\n        assert memory_increase < 10 * 1024 * 1024  # 10MB\n        \n        # __slots__によるメモリ効率性を確認\n        # リソース情報がないノードは_resource_infoがNoneであることを確認\n        nodes_without_resources = [n for n in nodes if n._resource_info is None]\n        assert len(nodes_without_resources) == 900  # 90%のノードはリソース情報なし\n    \n    def test_execution_order_cache_performance(self):\n        \"\"\"実行順序キャッシュのパフォーマンステスト\"\"\"\n        graph = RequestExecutionGraph()\n        \n        # 線形チェーンのグラフを作成\n        for i in range(500):\n            request = self.create_mock_request()\n            node = RequestNode(id=f\"node_{i}\", request=request)\n            graph.add_request_node(node)\n            \n            if i > 0:\n                edge = DependencyEdge(\n                    from_node=f\"node_{i-1}\",\n                    to_node=f\"node_{i}\",\n                    dependency_type=DependencyType.EXECUTION_ORDER\n                )\n                graph.add_dependency(edge)\n        \n        # 最初の実行順序取得（キャッシュなし）\n        start_time = time.time()\n        order1 = graph.get_execution_order()\n        first_time = time.time() - start_time\n        \n        # 2回目の実行順序取得（トポロジカルソートは毎回実行される）\n        start_time = time.time()\n        order2 = graph.get_execution_order()\n        second_time = time.time() - start_time\n        \n        # 結果の一貫性を確認\n        assert order1 == order2\n        assert len(order1) == 500\n        \n        # 両方とも十分高速であることを確認\n        assert first_time < 0.1\n        assert second_time < 0.1