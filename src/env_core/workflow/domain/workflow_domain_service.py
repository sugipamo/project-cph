"""
Workflow domain service - pure domain logic
"""
from typing import List, Dict, Any, Tuple, Optional
from src.env_core.step.step import Step, StepType, StepContext
from src.env_core.step.core import generate_steps_from_json
from src.env_core.step.dependency import resolve_dependencies
from src.env_core.step.workflow import (
    create_step_context_from_env_context,
    optimize_workflow_steps
)


class WorkflowDomainService:
    """ワークフローのドメインロジックを処理"""
    
    @staticmethod
    def generate_steps_from_config(config_data: List[Dict[str, Any]], 
                                 step_context: StepContext) -> List[Step]:
        """
        設定データからステップを生成
        
        Args:
            config_data: 設定データ
            step_context: ステップコンテキスト
            
        Returns:
            生成されたステップのリスト
        """
        return generate_steps_from_json(config_data, step_context)
    
    @staticmethod
    def resolve_step_dependencies(steps: List[Step]) -> List[Step]:
        """
        ステップの依存関係を解決
        
        Args:
            steps: 依存関係を解決するステップのリスト
            
        Returns:
            依存関係が解決されたステップのリスト
        """
        return resolve_dependencies(steps)
    
    @staticmethod
    def optimize_steps(steps: List[Step]) -> List[Step]:
        """
        ステップを最適化
        
        Args:
            steps: 最適化するステップのリスト
            
        Returns:
            最適化されたステップのリスト
        """
        return optimize_workflow_steps(steps)
    
    @staticmethod
    def create_step_context(env_context: Any) -> StepContext:
        """
        環境コンテキストからステップコンテキストを作成
        
        Args:
            env_context: 環境コンテキスト
            
        Returns:
            ステップコンテキスト
        """
        return create_step_context_from_env_context(env_context)
    
    @staticmethod
    def validate_steps(steps: List[Step]) -> Tuple[bool, Optional[str]]:
        """
        ステップのバリデーション
        
        Args:
            steps: バリデーションするステップのリスト
            
        Returns:
            Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
        """
        if not steps:
            return False, "ステップが定義されていません"
        
        for step in steps:
            if not step.type:
                return False, f"ステップ {step} にタイプが定義されていません"
        
        return True, None