from typing import List, Dict, Any, Tuple, Union
from src.operations.composite.composite_request import CompositeRequest
from src.operations.di_container import DIContainer
from src.env_integration.controller import EnvResourceController
from src.env_core.step.workflow import (
    generate_workflow_from_json, 
    create_step_context_from_env_context,
    validate_workflow_execution,
    debug_workflow_generation
)
from src.env_core.workflow import (
    GraphBasedWorkflowBuilder,
    RequestExecutionGraph,
    GraphToCompositeAdapter
)

class RunWorkflowBuilder:
    def __init__(self, controller: EnvResourceController, operations: DIContainer):
        self.controller = controller
        self.operations = operations
        self.graph_builder = GraphBasedWorkflowBuilder.from_controller(controller, operations)

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
    
    def build_graph_from_json_steps(
        self, 
        json_steps: List[Dict[str, Any]]
    ) -> Tuple[RequestExecutionGraph, List[str], List[str]]:
        """
        JSONステップリストからRequestExecutionGraphを生成
        
        Args:
            json_steps: JSONから読み込んだステップのリスト
            
        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]: 
                (実行グラフ, エラーリスト, 警告リスト)
        """
        return self.graph_builder.build_graph_from_json_steps(json_steps)
    
    def build_graph_from_nodes(
        self, 
        step_nodes: list
    ) -> Tuple[RequestExecutionGraph, List[str], List[str]]:
        """
        ConfigNodeのリストからRequestExecutionGraphを生成
        
        Args:
            step_nodes: ConfigNodeのリスト
            
        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]: 
                (実行グラフ, エラーリスト, 警告リスト)
        """
        return self.graph_builder.build_graph_from_nodes(step_nodes)
    
    def execute_graph(
        self, 
        graph: RequestExecutionGraph, 
        driver=None,
        parallel: bool = False,
        max_workers: int = 4
    ) -> List[Any]:
        """
        グラフを実行
        
        Args:
            graph: 実行するグラフ
            driver: 実行に使用するドライバー
            parallel: 並列実行するかどうか
            max_workers: 並列実行時の最大ワーカー数
            
        Returns:
            List[Any]: 実行結果のリスト
        """
        if parallel:
            return graph.execute_parallel(driver=driver, max_workers=max_workers)
        else:
            return graph.execute_sequential(driver=driver)
    
    def build_composite_or_graph(
        self,
        json_steps: List[Dict[str, Any]],
        use_graph: bool = False
    ) -> Union[CompositeRequest, RequestExecutionGraph]:
        """
        設定に応じてCompositeRequestまたはRequestExecutionGraphを生成
        
        Args:
            json_steps: JSONから読み込んだステップのリスト
            use_graph: グラフベースの実行を使用するかどうか
            
        Returns:
            Union[CompositeRequest, RequestExecutionGraph]: 
                生成されたリクエストまたはグラフ
        """
        if use_graph:
            graph, errors, warnings = self.build_graph_from_json_steps(json_steps)
            if errors:
                print(f"Error building graph: {errors}")
                # エラー時はCompositeRequestにフォールバック
                return self.build_from_json_steps(json_steps)[0]
            return graph
        else:
            return self.build_from_json_steps(json_steps)[0]

