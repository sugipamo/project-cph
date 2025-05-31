"""
グラフとコンポジットリクエストの相互変換アダプター

既存のCompositeRequestとの互換性を保ちながら、
グラフベースの実行システムを利用可能にする
"""
from typing import List, Dict, Optional, Set
from src.operations.composite.composite_request import CompositeRequest
from src.operations.base_request import BaseRequest
from .request_execution_graph import (
    RequestExecutionGraph, 
    RequestNode, 
    DependencyEdge, 
    DependencyType
)


class GraphToCompositeAdapter:
    """RequestExecutionGraphとCompositeRequest間の変換を行うアダプター"""
    
    @staticmethod
    def to_composite_request(graph: RequestExecutionGraph) -> CompositeRequest:
        """
        グラフから順次実行用のCompositeRequestに変換
        
        トポロジカルソートされた順序でリクエストを配置し、
        依存関係は事前に解決済みとして扱う
        
        Args:
            graph: 変換元のRequestExecutionGraph
            
        Returns:
            CompositeRequest: 順次実行可能なコンポジットリクエスト
        """
        # 実行順序を取得
        execution_order = graph.get_execution_order()
        
        # 順序に従ってリクエストを取得
        requests = []
        for node_id in execution_order:
            node = graph.nodes[node_id]
            requests.append(node.request)
        
        # CompositeRequestを作成
        return CompositeRequest.make_composite_request(requests)
    
    @staticmethod
    def from_composite_request(
        composite: CompositeRequest,
        extract_dependencies: bool = True
    ) -> RequestExecutionGraph:
        """
        CompositeRequestからグラフ構造に変換
        
        Args:
            composite: 変換元のCompositeRequest
            extract_dependencies: リクエストから依存関係を推測するかどうか
            
        Returns:
            RequestExecutionGraph: 生成されたグラフ
        """
        graph = RequestExecutionGraph()
        
        # ノードを作成
        node_map: Dict[int, RequestNode] = {}
        for i, request in enumerate(composite.requests):
            node_id = f"request_{i}"
            
            # リソース情報を抽出（可能な場合）
            creates_files, creates_dirs, reads_files, requires_dirs = \
                GraphToCompositeAdapter._extract_resource_info(request)
            
            node = RequestNode(
                id=node_id,
                request=request,
                creates_files=creates_files,
                creates_dirs=creates_dirs,
                reads_files=reads_files,
                requires_dirs=requires_dirs
            )
            
            graph.add_request_node(node)
            node_map[i] = node
        
        # 依存関係を推測（オプション）
        if extract_dependencies:
            GraphToCompositeAdapter._extract_dependencies(graph, list(node_map.values()))
        else:
            # 単純な実行順序依存を追加
            for i in range(len(composite.requests) - 1):
                edge = DependencyEdge(
                    from_node=f"request_{i}",
                    to_node=f"request_{i+1}",
                    dependency_type=DependencyType.EXECUTION_ORDER,
                    description="Sequential execution order"
                )
                graph.add_dependency(edge)
        
        return graph
    
    @staticmethod
    def _extract_resource_info(request: BaseRequest) -> tuple[Set[str], Set[str], Set[str], Set[str]]:
        """
        リクエストからリソース情報を抽出（可能な場合）
        
        Returns:
            (creates_files, creates_dirs, reads_files, requires_dirs)
        """
        creates_files = set()
        creates_dirs = set()
        reads_files = set()
        requires_dirs = set()
        
        # リクエストタイプに基づいて情報を抽出
        # FileRequestの場合
        if hasattr(request, 'operation_type') and hasattr(request, 'op'):
            from src.operations.constants.operation_type import OperationType
            from src.operations.file.file_op_type import FileOpType
            
            if request.operation_type == OperationType.FILE:
                file_op = request.op
                
                if file_op == FileOpType.MKDIR and hasattr(request, 'target_path'):
                    creates_dirs.add(request.target_path)
                elif file_op == FileOpType.TOUCH and hasattr(request, 'target_path'):
                    creates_files.add(request.target_path)
                    # 親ディレクトリも必要
                    from pathlib import Path
                    parent = str(Path(request.target_path).parent)
                    if parent != '.':
                        requires_dirs.add(parent)
                elif file_op == FileOpType.COPY:
                    if hasattr(request, 'source_path'):
                        reads_files.add(request.source_path)
                    if hasattr(request, 'target_path'):
                        creates_files.add(request.target_path)
                        from pathlib import Path
                        parent = str(Path(request.target_path).parent)
                        if parent != '.':
                            requires_dirs.add(parent)
        
        # CompositeRequestの場合は再帰的に処理
        elif isinstance(request, CompositeRequest):
            for sub_request in request.requests:
                sub_creates_files, sub_creates_dirs, sub_reads_files, sub_requires_dirs = \
                    GraphToCompositeAdapter._extract_resource_info(sub_request)
                creates_files.update(sub_creates_files)
                creates_dirs.update(sub_creates_dirs)
                reads_files.update(sub_reads_files)
                requires_dirs.update(sub_requires_dirs)
        
        return creates_files, creates_dirs, reads_files, requires_dirs
    
    @staticmethod
    def _extract_dependencies(graph: RequestExecutionGraph, nodes: List[RequestNode]) -> None:
        """
        ノード間の依存関係を推測して追加
        """
        # 各ノードペアについて依存関係をチェック
        for i, from_node in enumerate(nodes):
            for j, to_node in enumerate(nodes[i+1:], i+1):
                # ファイル作成依存
                for file_path in from_node.creates_files:
                    if file_path in to_node.reads_files:
                        edge = DependencyEdge(
                            from_node=from_node.id,
                            to_node=to_node.id,
                            dependency_type=DependencyType.FILE_CREATION,
                            resource_path=file_path,
                            description=f"File {file_path} must be created before being read"
                        )
                        graph.add_dependency(edge)
                
                # ディレクトリ作成依存
                for dir_path in from_node.creates_dirs:
                    if dir_path in to_node.requires_dirs:
                        edge = DependencyEdge(
                            from_node=from_node.id,
                            to_node=to_node.id,
                            dependency_type=DependencyType.DIRECTORY_CREATION,
                            resource_path=dir_path,
                            description=f"Directory {dir_path} must be created before being used"
                        )
                        graph.add_dependency(edge)
    
    @staticmethod
    def merge_graphs(graphs: List[RequestExecutionGraph]) -> RequestExecutionGraph:
        """
        複数のグラフを1つに統合
        
        Args:
            graphs: 統合するグラフのリスト
            
        Returns:
            RequestExecutionGraph: 統合されたグラフ
        """
        merged_graph = RequestExecutionGraph()
        node_id_offset = 0
        
        for graph_idx, graph in enumerate(graphs):
            # ノードIDをユニークにするためのマッピング
            id_mapping = {}
            
            # ノードを追加（IDを調整）
            for old_id, node in graph.nodes.items():
                new_id = f"graph{graph_idx}_{old_id}"
                id_mapping[old_id] = new_id
                
                new_node = RequestNode(
                    id=new_id,
                    request=node.request,
                    creates_files=node.creates_files.copy() if node.creates_files else None,
                    creates_dirs=node.creates_dirs.copy() if node.creates_dirs else None,
                    reads_files=node.reads_files.copy() if node.reads_files else None,
                    requires_dirs=node.requires_dirs.copy() if node.requires_dirs else None,
                    metadata=node.metadata.copy() if node.metadata else None
                )
                
                # ステータスと結果を手動でコピー
                new_node.status = node.status
                new_node.result = node.result
                merged_graph.add_request_node(new_node)
            
            # エッジを追加（IDを調整）
            for edge in graph.edges:
                new_edge = DependencyEdge(
                    from_node=id_mapping[edge.from_node],
                    to_node=id_mapping[edge.to_node],
                    dependency_type=edge.dependency_type,
                    resource_path=edge.resource_path,
                    description=edge.description
                )
                merged_graph.add_dependency(new_edge)
            
            # グラフ間の依存関係を追加（前のグラフの最後から次のグラフの最初へ）
            if graph_idx > 0:
                prev_graph = graphs[graph_idx - 1]
                if prev_graph.nodes and graph.nodes:
                    # 前のグラフの最終ノードを取得
                    prev_execution_order = prev_graph.get_execution_order()
                    if prev_execution_order:
                        prev_last_id = f"graph{graph_idx-1}_{prev_execution_order[-1]}"
                        
                        # 現在のグラフの最初のノードを取得
                        curr_execution_order = graph.get_execution_order()
                        if curr_execution_order:
                            curr_first_id = f"graph{graph_idx}_{curr_execution_order[0]}"
                            
                            # 接続エッジを追加
                            connect_edge = DependencyEdge(
                                from_node=prev_last_id,
                                to_node=curr_first_id,
                                dependency_type=DependencyType.EXECUTION_ORDER,
                                description="Graph connection"
                            )
                            merged_graph.add_dependency(connect_edge)
        
        return merged_graph