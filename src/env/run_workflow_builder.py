from typing import List, Dict, Any, Tuple
from src.operations.composite.composite_request import CompositeRequest
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController
from src.env.step_generation.workflow import (
    generate_workflow_from_json, 
    create_step_context_from_env_context,
    validate_workflow_execution,
    debug_workflow_generation
)

class RunWorkflowBuilder:
    def __init__(self, controller: EnvResourceController, operations: DIContainer):
        self.controller = controller
        self.operations = operations

    @classmethod
    def from_controller(cls, controller: EnvResourceController, operations: DIContainer) -> 'RunWorkflowBuilder':
        """
        controllerとoperationsからRunWorkflowBuilderを生成
        """
        return cls(controller, operations)

    def build_from_json_steps(self, json_steps: List[Dict[str, Any]]) -> Tuple[CompositeRequest, List[str], List[str]]:
        """
        JSONステップリストから純粋関数ベースでCompositeRequestを生成
        
        Args:
            json_steps: JSONから読み込んだステップのリスト
            
        Returns:
            Tuple[CompositeRequest, List[str], List[str]]: 
                (実行可能リクエスト, エラーリスト, 警告リスト)
        """
        # EnvContext から StepContext を作成
        context = create_step_context_from_env_context(self.controller.env_context)
        
        # 純粋関数を使用してワークフローを生成
        composite_request, errors, warnings = generate_workflow_from_json(
            json_steps, context, self.operations
        )
        
        return composite_request, errors, warnings

    def build_from_nodes(self, step_nodes: list) -> CompositeRequest:
        """
        ConfigNodeのリストからCompositeRequestを生成（既存互換性のため保持）
        """
        # ConfigNode から JSON 形式のデータを抽出
        json_steps = []
        
        for node in step_nodes:
            if not node.value or not isinstance(node.value, dict):
                continue
            json_steps.append(node.value)
        
        # 新しい純粋関数ベースの方法でビルド
        composite_request, errors, warnings = self.build_from_json_steps(json_steps)
        
        # エラーがある場合はログ出力（互換性のため）
        if errors:
            print(f"Warning: Workflow generation errors: {errors}")
        if warnings:
            print(f"Info: Workflow generation warnings: {warnings}")
        
        return composite_request

    def validate_and_build(self, json_steps: List[Dict[str, Any]]) -> Tuple[bool, CompositeRequest, List[str]]:
        """
        JSONステップを検証してからワークフローをビルドする
        
        Args:
            json_steps: JSONから読み込んだステップのリスト
            
        Returns:
            Tuple[bool, CompositeRequest, List[str]]: 
                (成功フラグ, リクエスト, メッセージリスト)
        """
        composite_request, errors, warnings = self.build_from_json_steps(json_steps)
        
        # 最終検証
        is_valid, messages = validate_workflow_execution(composite_request, errors, warnings)
        
        return is_valid, composite_request, messages

    def debug_build(self, json_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ワークフロー生成をデバッグモードで実行
        
        Args:
            json_steps: JSONから読み込んだステップのリスト
            
        Returns:
            Dict[str, Any]: デバッグ情報
        """
        context = create_step_context_from_env_context(self.controller.env_context)
        return debug_workflow_generation(json_steps, context)

