"""
GraphToCompositeAdapterのテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.env.workflow.graph_to_composite_adapter import GraphToCompositeAdapter
from src.env.workflow.request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
from src.operations.composite.composite_request import CompositeRequest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.constants.operation_type import OperationType


class TestGraphToCompositeAdapter:
    """GraphToCompositeAdapterのテストクラス"""
    
    @pytest.fixture
    def simple_graph(self):
        """シンプルなグラフを生成"""
        graph = RequestExecutionGraph()
        
        # モックリクエストを作成
        request1 = Mock()
        request1.execute.return_value = Mock(success=True)
        request2 = Mock()
        request2.execute.return_value = Mock(success=True)
        
        # ノードを追加
        node1 = RequestNode(id="node1", request=request1)
        node2 = RequestNode(id="node2", request=request2)
        
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        # 依存関係を追加
        edge = DependencyEdge(
            from_node="node1",
            to_node="node2",
            dependency_type=DependencyType.EXECUTION_ORDER
        )
        graph.add_dependency(edge)
        
        return graph
    
    @pytest.fixture
    def file_request_graph(self):
        """ファイル操作を含むグラフを生成"""
        graph = RequestExecutionGraph()
        
        # FileRequestのモックを作成
        mkdir_request = Mock(spec=FileRequest)
        mkdir_request.op = FileOpType.MKDIR
        mkdir_request.operation_type = OperationType.FILE
        mkdir_request.target_path = "/tmp/test"
        
        touch_request = Mock(spec=FileRequest)
        touch_request.op = FileOpType.TOUCH
        touch_request.operation_type = OperationType.FILE
        touch_request.target_path = "/tmp/test/file.txt"
        
        # ノードを追加
        node1 = RequestNode(
            id="mkdir",
            request=mkdir_request,
            creates_dirs={"/tmp/test"}
        )
        node2 = RequestNode(
            id="touch",
            request=touch_request,
            creates_files={"/tmp/test/file.txt"},
            requires_dirs={"/tmp/test"}
        )
        
        graph.add_request_node(node1)
        graph.add_request_node(node2)
        
        # 依存関係を追加
        edge = DependencyEdge(
            from_node="mkdir",
            to_node="touch",
            dependency_type=DependencyType.DIRECTORY_CREATION,
            resource_path="/tmp/test"
        )
        graph.add_dependency(edge)
        
        return graph
    
    def test_to_composite_request(self, simple_graph):
        """グラフからCompositeRequestへの変換テスト"""
        # モックにBaseRequestを継承させる
        from src.operations.base_request import BaseRequest
        for node in simple_graph.nodes.values():
            node.request.__class__ = type('MockRequest', (BaseRequest,), {})
            node.request.operation_type = OperationType.FILE
        
        composite = GraphToCompositeAdapter.to_composite_request(simple_graph)
        
        assert isinstance(composite, CompositeRequest)
        assert len(composite.requests) == 2
        # 実行順序が保持されているか確認
        assert composite.requests[0] == simple_graph.nodes["node1"].request
        assert composite.requests[1] == simple_graph.nodes["node2"].request
    
    def test_from_composite_request_simple(self):
        """CompositeRequestからグラフへの変換テスト（シンプル）"""
        # BaseRequestを継承したモックを作成
        from src.operations.base_request import BaseRequest
        request1 = Mock(spec=BaseRequest)
        request1.operation_type = OperationType.FILE
        request2 = Mock(spec=BaseRequest)
        request2.operation_type = OperationType.FILE
        composite = CompositeRequest.make_composite_request([request1, request2])
        
        # グラフに変換
        graph = GraphToCompositeAdapter.from_composite_request(
            composite, 
            extract_dependencies=False
        )
        
        assert len(graph.nodes) == 2
        assert "request_0" in graph.nodes
        assert "request_1" in graph.nodes
        
        # 順序依存が追加されているか確認
        assert len(graph.edges) == 1
        assert graph.edges[0].dependency_type == DependencyType.EXECUTION_ORDER
    
    def test_from_composite_request_with_dependencies(self):
        """CompositeRequestからグラフへの変換テスト（依存関係抽出あり）"""
        # FileRequestのモックを作成
        from src.operations.base_request import BaseRequest
        mkdir_request = Mock(spec=BaseRequest)
        mkdir_request.op = FileOpType.MKDIR
        mkdir_request.operation_type = OperationType.FILE
        mkdir_request.target_path = "/tmp/test"
        
        touch_request = Mock(spec=BaseRequest)
        touch_request.op = FileOpType.TOUCH
        touch_request.operation_type = OperationType.FILE
        touch_request.target_path = "/tmp/test/file.txt"
        
        composite = CompositeRequest.make_composite_request([mkdir_request, touch_request])
        
        # グラフに変換（依存関係を抽出）
        graph = GraphToCompositeAdapter.from_composite_request(
            composite,
            extract_dependencies=True
        )
        
        assert len(graph.nodes) == 2
        
        # ディレクトリ作成依存が検出されているか確認
        deps = graph.get_dependencies("request_1")
        assert "request_0" in deps
    
    def test_extract_resource_info_mkdir(self):
        """リソース情報抽出のテスト（MKDIR）"""
        request = Mock()
        request.op = FileOpType.MKDIR
        request.operation_type = OperationType.FILE
        request.target_path = "/tmp/test"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(request)
        
        assert creates_dirs == {"/tmp/test"}
        assert len(creates_files) == 0
        assert len(reads_files) == 0
        assert len(requires_dirs) == 0
    
    def test_extract_resource_info_touch(self):
        """リソース情報抽出のテスト（TOUCH）"""
        request = Mock()
        request.op = FileOpType.TOUCH
        request.operation_type = OperationType.FILE
        request.target_path = "/tmp/test/file.txt"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(request)
        
        assert creates_files == {"/tmp/test/file.txt"}
        assert len(creates_dirs) == 0
        assert len(reads_files) == 0
        assert requires_dirs == {"/tmp/test"}
    
    def test_extract_resource_info_copy(self):
        """リソース情報抽出のテスト（COPY）"""
        request = Mock()
        request.op = FileOpType.COPY
        request.operation_type = OperationType.FILE
        request.source_path = "/tmp/source.txt"
        request.target_path = "/tmp/dest/target.txt"
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(request)
        
        assert creates_files == {"/tmp/dest/target.txt"}
        assert len(creates_dirs) == 0
        assert reads_files == {"/tmp/source.txt"}
        assert requires_dirs == {"/tmp/dest"}
    
    def test_extract_resource_info_composite(self):
        """リソース情報抽出のテスト（CompositeRequest）"""
        # サブリクエストを作成
        from src.operations.base_request import BaseRequest
        sub_request1 = Mock(spec=BaseRequest)
        sub_request1.op = FileOpType.MKDIR
        sub_request1.operation_type = OperationType.FILE
        sub_request1.target_path = "/tmp/dir1"
        
        sub_request2 = Mock(spec=BaseRequest)
        sub_request2.op = FileOpType.TOUCH
        sub_request2.operation_type = OperationType.FILE
        sub_request2.target_path = "/tmp/dir1/file.txt"
        
        # CompositeRequestを作成
        composite = CompositeRequest.make_composite_request([sub_request1, sub_request2])
        
        creates_files, creates_dirs, reads_files, requires_dirs = \
            GraphToCompositeAdapter._extract_resource_info(composite)
        
        assert creates_files == {"/tmp/dir1/file.txt"}
        assert creates_dirs == {"/tmp/dir1"}
        assert len(reads_files) == 0
        assert requires_dirs == {"/tmp/dir1"}
    
    def test_merge_graphs(self):
        """グラフのマージテスト"""
        # グラフ1を作成
        graph1 = RequestExecutionGraph()
        node1 = RequestNode(id="node1", request=Mock())
        node2 = RequestNode(id="node2", request=Mock())
        graph1.add_request_node(node1)
        graph1.add_request_node(node2)
        graph1.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        
        # グラフ2を作成
        graph2 = RequestExecutionGraph()
        node3 = RequestNode(id="node1", request=Mock())  # 同じIDだが別のグラフ
        node4 = RequestNode(id="node2", request=Mock())
        graph2.add_request_node(node3)
        graph2.add_request_node(node4)
        graph2.add_dependency(DependencyEdge("node1", "node2", DependencyType.EXECUTION_ORDER))
        
        # マージ
        merged = GraphToCompositeAdapter.merge_graphs([graph1, graph2])
        
        # ノード数の確認
        assert len(merged.nodes) == 4
        assert "graph0_node1" in merged.nodes
        assert "graph0_node2" in merged.nodes
        assert "graph1_node1" in merged.nodes
        assert "graph1_node2" in merged.nodes
        
        # エッジ数の確認（元の2つ + 接続用1つ）
        assert len(merged.edges) == 3
        
        # グラフ間の接続が追加されているか確認
        has_connection = any(
            e.from_node == "graph0_node2" and e.to_node == "graph1_node1"
            for e in merged.edges
        )
        assert has_connection
    
    def test_roundtrip_conversion(self, file_request_graph):
        """グラフ→コンポジット→グラフの往復変換テスト"""
        # グラフからコンポジットに変換
        composite = GraphToCompositeAdapter.to_composite_request(file_request_graph)
        
        # コンポジットからグラフに戻す
        restored_graph = GraphToCompositeAdapter.from_composite_request(
            composite,
            extract_dependencies=True
        )
        
        # ノード数が同じか確認
        assert len(restored_graph.nodes) == len(file_request_graph.nodes)
        
        # リクエストが保持されているか確認
        original_requests = [n.request for n in file_request_graph.nodes.values()]
        restored_requests = [n.request for n in restored_graph.nodes.values()]
        assert original_requests == restored_requests