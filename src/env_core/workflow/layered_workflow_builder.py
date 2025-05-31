"""
Layered workflow builder with clear separation of concerns
"""
from typing import List, Dict, Any, Optional
from src.context.resolver.config_node import ConfigNode
from src.operations.composite.composite_request import CompositeRequest
from .domain.workflow_domain_service import WorkflowDomainService
from .application.step_to_request_adapter import StepToRequestAdapter
from .infrastructure.request_infrastructure_service import RequestInfrastructureService


class LayeredWorkflowBuilder:
    """
    レイヤー分離されたワークフロービルダー
    
    Domain Layer: 純粋なビジネスロジック（Step処理）
    Application Layer: ドメインとインフラの橋渡し（Step→Request変換）
    Infrastructure Layer: 具体的なリクエスト生成・実行
    """
    
    def __init__(self, context: Optional[Any] = None):
        """
        初期化
        
        Args:
            context: 実行コンテキスト
        """
        self.context = context
        self.domain_service = WorkflowDomainService()
        self.step_adapter = StepToRequestAdapter()
        self.infrastructure_service = RequestInfrastructureService()
    
    @classmethod
    def from_context(cls, context: Any) -> 'LayeredWorkflowBuilder':
        """
        コンテキストからビルダーを生成
        
        Args:
            context: 実行コンテキスト
            
        Returns:
            LayeredWorkflowBuilder
        """
        return cls(context)
    
    def build_workflow_from_config_nodes(self, 
                                       config_nodes: List[ConfigNode]) -> CompositeRequest:
        """
        設定ノードからワークフローを構築
        
        Args:
            config_nodes: 設定ノードのリスト
            
        Returns:
            構築されたCompositeRequest
        """
        # 1. Domain Layer: 設定からステップを生成
        config_data = [node.to_dict() for node in config_nodes]
        step_context = self.domain_service.create_step_context(self.context)
        steps = self.domain_service.generate_steps_from_config(config_data, step_context)
        
        # 2. Domain Layer: 依存関係解決と最適化
        steps = self.domain_service.resolve_step_dependencies(steps)
        steps = self.domain_service.optimize_steps(steps)
        
        # 3. Domain Layer: バリデーション
        is_valid, error_msg = self.domain_service.validate_steps(steps)
        if not is_valid:
            raise ValueError(f"ステップのバリデーションに失敗しました: {error_msg}")
        
        # 4. Application Layer: ステップをリクエストに変換
        requests = self.step_adapter.convert_steps_to_requests(steps)
        
        # 5. Application Layer: 変換結果のバリデーション
        if not self.step_adapter.validate_conversion(steps, requests):
            raise ValueError("ステップのリクエスト変換に失敗しました")
        
        # 6. Infrastructure Layer: CompositeRequest作成
        return self.infrastructure_service.create_composite_request(
            [r for r in requests if r is not None],
            name=f"workflow_{len(steps)}_steps"
        )
    
    def build_workflow_from_json(self, config_data: List[Dict[str, Any]]) -> CompositeRequest:
        """
        JSON設定からワークフローを構築
        
        Args:
            config_data: JSON設定データ
            
        Returns:
            構築されたCompositeRequest
        """
        # 1. Domain Layer: 設定からステップを生成
        step_context = self.domain_service.create_step_context(self.context)
        steps = self.domain_service.generate_steps_from_config(config_data, step_context)
        
        # 2-6. 共通処理
        return self._process_steps_to_composite(steps)
    
    def _process_steps_to_composite(self, steps) -> CompositeRequest:
        """ステップからCompositeRequestへの共通処理"""
        # Domain Layer処理
        steps = self.domain_service.resolve_step_dependencies(steps)
        steps = self.domain_service.optimize_steps(steps)
        
        is_valid, error_msg = self.domain_service.validate_steps(steps)
        if not is_valid:
            raise ValueError(f"ステップのバリデーションに失敗しました: {error_msg}")
        
        # Application Layer処理
        requests = self.step_adapter.convert_steps_to_requests(steps)
        
        if not self.step_adapter.validate_conversion(steps, requests):
            raise ValueError("ステップのリクエスト変換に失敗しました")
        
        # Infrastructure Layer処理
        return self.infrastructure_service.create_composite_request(
            [r for r in requests if r is not None],
            name=f"workflow_{len(steps)}_steps"
        )