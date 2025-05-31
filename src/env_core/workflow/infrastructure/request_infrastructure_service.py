"""
Request infrastructure service
"""
from typing import List, Any
from src.operations.composite.composite_request import CompositeRequest
from ..request_execution_graph import RequestExecutionGraph, RequestNode
from ..graph_to_composite_adapter import GraphToCompositeAdapter


class RequestInfrastructureService:
    """リクエスト実行のインフラストラクチャサービス"""
    
    def __init__(self):
        self.graph_adapter = GraphToCompositeAdapter()
    
    def create_execution_graph(self, requests: List[Any]) -> RequestExecutionGraph:
        """
        リクエストから実行グラフを作成
        
        Args:
            requests: リクエストのリスト
            
        Returns:
            実行グラフ
        """
        graph = RequestExecutionGraph()
        
        # リクエストをノードとして追加
        for i, request in enumerate(requests):
            node = RequestNode(
                id=f"request_{i}",
                request=request,
                metadata={}
            )
            graph.add_node(node)
        
        return graph
    
    def convert_graph_to_composite(self, graph: RequestExecutionGraph) -> CompositeRequest:
        """
        実行グラフをCompositeRequestに変換
        
        Args:
            graph: 実行グラフ
            
        Returns:
            CompositeRequest
        """
        return self.graph_adapter.convert(graph)
    
    def create_composite_request(self, requests: List[Any], 
                               name: str = None) -> CompositeRequest:
        """
        リクエストのリストからCompositeRequestを作成
        
        Args:
            requests: リクエストのリスト
            name: CompositeRequestの名前
            
        Returns:
            CompositeRequest
        """
        return CompositeRequest.make_composite_request(requests, name=name)