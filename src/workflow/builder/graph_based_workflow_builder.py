"""グラフベースのワークフロービルダー

ConfigNodeからRequestExecutionGraphを生成し、
依存関係を考慮した実行計画を構築する
"""
from pathlib import Path
from typing import Any, Optional

from src.context.resolver.config_node import ConfigNode

# from .graph_to_composite_adapter import GraphToCompositeAdapter  # Temporarily disabled
from src.domain.requests.composite.composite_request import CompositeRequest
from src.workflow.step.core import generate_steps_from_json
from src.workflow.step.dependency import resolve_dependencies
from src.workflow.step.step import Step
from src.workflow.step.workflow import create_step_context_from_env_context, optimize_workflow_steps

from .request_execution_graph import DependencyEdge, DependencyType, RequestExecutionGraph, RequestNode


class GraphBasedWorkflowBuilder:
    """グラフベースのワークフロー生成器"""

    def __init__(self, context: Optional[Any] = None):
        """純粋なワークフロービルダー

        Args:
            context: StepContextまたは環境情報（オプション）
        """
        self.context = context

    @classmethod
    def from_context(cls, context: Any) -> 'GraphBasedWorkflowBuilder':
        """コンテキストからGraphBasedWorkflowBuilderを生成

        Args:
            context: StepContextまたは環境情報
        """
        return cls(context)

    @classmethod
    def from_controller(
        cls,
        controller: Any,
        operations: Any
    ) -> 'GraphBasedWorkflowBuilder':
        """controller(既存互換性のため保持)
        """
        # controllerからcontextを抽出
        context = create_step_context_from_env_context(controller.env_context)
        return cls(context)

    def build_graph_from_json_steps(
        self,
        json_steps: list[dict[str, Any]]
    ) -> tuple[RequestExecutionGraph, list[str], list[str]]:
        """JSONステップリストからRequestExecutionGraphを生成

        Args:
            json_steps: JSONから読み込んだステップのリスト

        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]:
                (実行グラフ, エラーリスト, 警告リスト)
        """
        # コンテキストを取得（事前に設定済み、またはデフォルト）
        context = self.context
        if context is None:
            # デフォルトコンテキストを作成
            from src.workflow.step.step import StepContext
            context = StepContext(
                contest_name="",
                problem_name="",
                language="",
                env_type="local",
                command_type="",
                workspace_path="./workspace",
                contest_current_path="./contest_current"
            )

        # JSON から Step オブジェクトを生成
        generation_result = generate_steps_from_json(json_steps, context)

        if not generation_result.is_success:
            # エラーがある場合は空のグラフを返す
            return RequestExecutionGraph(), generation_result.errors, generation_result.warnings

        steps = generation_result.steps
        errors = list(generation_result.errors)
        warnings = list(generation_result.warnings)

        # 依存関係を解決
        resolved_steps = resolve_dependencies(steps, context)

        # ステップを最適化
        optimized_steps = optimize_workflow_steps(resolved_steps)

        # ステップからグラフを構築
        graph = self._build_graph_from_steps(optimized_steps)

        return graph, errors, warnings

    def build_graph_from_nodes(
        self,
        step_nodes: list[ConfigNode]
    ) -> tuple[RequestExecutionGraph, list[str], list[str]]:
        """ConfigNodeのリストからRequestExecutionGraphを生成

        Args:
            step_nodes: ConfigNodeのリスト

        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]:
                (実行グラフ, エラーリスト, 警告リスト)
        """
        # ConfigNode から JSON 形式のデータを抽出
        json_steps = []

        for node in step_nodes:
            if not node.value or not isinstance(node.value, dict):
                continue
            json_steps.append(node.value)

        # JSONステップからグラフを構築
        return self.build_graph_from_json_steps(json_steps)

    def build_composite_from_graph(
        self,
        graph: RequestExecutionGraph
    ) -> CompositeRequest:
        """グラフからCompositeRequestを生成（後方互換性）

        Args:
            graph: RequestExecutionGraph

        Returns:
            CompositeRequest: 順次実行用のコンポジットリクエスト
        """
        # TODO: GraphToCompositeAdapter implementation needed
        raise NotImplementedError("GraphToCompositeAdapter is temporarily disabled")

    def _build_graph_from_steps(self, steps: list[Step]) -> RequestExecutionGraph:
        """Stepリストから実行グラフを構築

        Args:
            steps: ステップのリスト

        Returns:
            RequestExecutionGraph: 構築されたグラフ
        """
        # デバッグ設定を取得
        debug_config = None
        if self.context and hasattr(self.context, 'env_json') and self.context.env_json:
            language_config = self.context.env_json.get(self.context.language, {})
            debug_config = language_config.get('debug')

        graph = RequestExecutionGraph(debug_config)
        node_map: dict[int, RequestNode] = {}

        # ステップからリクエストノードを作成
        for i, step in enumerate(steps):
            request = self._step_to_request(step)
            if not request:
                continue

            # ステップからリソース情報を抽出
            creates_files, creates_dirs, reads_files, requires_dirs = \
                self._extract_resource_info_from_step(step)

            node = RequestNode(
                id=f"step_{i}",
                request=request,
                creates_files=creates_files,
                creates_dirs=creates_dirs,
                reads_files=reads_files,
                requires_dirs=requires_dirs,
                metadata={
                    'step_type': step.type.value,
                    'step_cmd': step.cmd,
                    'original_index': i
                }
            )

            graph.add_request_node(node)
            node_map[i] = node

        # ノード間の依存関係を構築
        self._build_dependencies(graph, list(node_map.values()))

        return graph

    def _step_to_request(self, step: Step) -> Optional[Any]:
        """StepからRequestを生成（統一ファクトリー版）

        Args:
            step: 変換するステップ

        Returns:
            生成されたリクエスト、または None
        """
        from src.application.factories.unified_request_factory import create_request

        # 統一ファクトリを使用してリクエストを生成
        return create_request(step, context=self.context)

    def _extract_resource_info_from_step(
        self,
        step: Step
    ) -> tuple[set, set, set, set]:
        """ステップからリソース情報を抽出（純粋関数版使用）

        Returns:
            (creates_files, creates_dirs, reads_files, requires_dirs)
        """
        from src.workflow.builder.graph_builder_utils import extract_node_resource_info
        return extract_node_resource_info(step)

    def _build_dependencies(
        self,
        graph: RequestExecutionGraph,
        nodes: list[RequestNode]
    ) -> None:
        """ノード間の依存関係を構築（純粋関数版）

        Args:
            graph: 依存関係を追加するグラフ
            nodes: ノードのリスト
        """
        from .functional_utils import pipe
        from .graph_ops.metadata_extraction import extract_request_metadata
        from .graph_ops.dependency_mapping import build_dependency_mapping
        from .graph_ops.cycle_detection import validate_no_circular_dependencies
        from .graph_ops.graph_optimization import optimize_dependency_order
        
        # 関数型パイプライン
        result = pipe(
            nodes,
            extract_request_metadata,           # 純粋関数
            build_dependency_mapping,           # 純粋関数  
            validate_no_circular_dependencies,  # 純粋関数
            optimize_dependency_order           # 純粋関数
        )
        
        # 副作用: グラフに依存関係を追加
        self._apply_dependencies_to_graph(graph, result)

    def _is_parent_directory(self, parent_path: str, child_path: str) -> bool:
        """parent_pathがchild_pathの親ディレクトリかどうかを判定（純粋関数版使用）
        """
        from src.workflow.builder.graph_builder_utils import is_parent_directory
        return is_parent_directory(parent_path, child_path)

    def _has_resource_conflict(
        self,
        node1: RequestNode,
        node2: RequestNode
    ) -> bool:
        """2つのノード間でリソースの競合があるかどうかを判定（純粋関数版使用）

        Args:
            node1: 最初のノード
            node2: 2番目のノード

        Returns:
            bool: 競合がある場合True
        """
        from src.workflow.builder.graph_builder_utils import NodeInfo, has_resource_conflict

        # RequestNodeからNodeInfoへの変換
        node_info1 = NodeInfo(
            id=node1.id,
            step=None,  # ダミー
            creates_files=node1.creates_files,
            creates_dirs=node1.creates_dirs,
            reads_files=node1.reads_files,
            requires_dirs=node1.requires_dirs,
            metadata={}
        )
        node_info2 = NodeInfo(
            id=node2.id,
            step=None,  # ダミー
            creates_files=node2.creates_files,
            creates_dirs=node2.creates_dirs,
            reads_files=node2.reads_files,
            requires_dirs=node2.requires_dirs,
            metadata={}
        )

        return has_resource_conflict(node_info1, node_info2)

    def build_graph_with_utils(
        self,
        steps: list[Step]
    ) -> tuple[RequestExecutionGraph, list[str], list[str]]:
        """純粋関数を使用したグラフ構築

        Args:
            steps: ステップのリスト

        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]:
                (実行グラフ, エラーリスト, 警告リスト)
        """
        from src.workflow.builder.graph_builder_utils import build_execution_graph

        # 純粋関数でグラフ構築結果を取得
        result = build_execution_graph(steps, self.context)

        # RequestExecutionGraphを作成
        debug_config = None
        if self.context and hasattr(self.context, 'env_json') and self.context.env_json:
            language_config = self.context.env_json.get(self.context.language, {})
            debug_config = language_config.get('debug')

        graph = RequestExecutionGraph(debug_config)

        # ノード情報からRequestNodeを作成
        for node_info in result.nodes:
            request = self._step_to_request(node_info.step)
            if not request:
                continue

            request_node = RequestNode(
                id=node_info.id,
                request=request,
                creates_files=node_info.creates_files,
                creates_dirs=node_info.creates_dirs,
                reads_files=node_info.reads_files,
                requires_dirs=node_info.requires_dirs,
                metadata=node_info.metadata
            )
            graph.add_request_node(request_node)

        # 依存関係を追加
        for dep_info in result.dependencies:
            edge = DependencyEdge(
                from_node=dep_info.from_node_id,
                to_node=dep_info.to_node_id,
                dependency_type=getattr(DependencyType, dep_info.dependency_type, DependencyType.EXECUTION_ORDER),
                resource_path=dep_info.resource_path,
                description=dep_info.description
            )
            graph.add_dependency(edge)

        return graph, result.errors, result.warnings

    def validate_graph(
        self,
        graph: RequestExecutionGraph
    ) -> tuple[bool, list[str]]:
        """グラフの妥当性を検証

        Args:
            graph: 検証するグラフ

        Returns:
            Tuple[bool, List[str]]: (有効かどうか, メッセージリスト)
        """
        messages = []
        is_valid = True

        # 循環依存のチェック
        cycles = graph.detect_cycles()
        if cycles:
            is_valid = False
            messages.append(f"Circular dependencies detected: {cycles}")

        # ノードが空でないかチェック
        if not graph.nodes:
            is_valid = False
            messages.append("No executable nodes in graph")

        # 並列実行グループの確認
        try:
            groups = graph.get_parallel_groups()
            messages.append(f"Graph has {len(groups)} execution groups")
            for i, group in enumerate(groups):
                messages.append(f"  Group {i+1}: {len(group)} nodes can run in parallel")
        except ValueError as e:
            is_valid = False
            messages.append(f"Failed to determine execution groups: {e!s}")

        return is_valid, messages

    def _apply_dependencies_to_graph(self, graph: RequestExecutionGraph, result: dict) -> None:
        """純粋関数の結果をグラフに適用（副作用を集約）
        
        Args:
            graph: 適用先グラフ
            result: 最適化結果辞書
        """
        from .request_execution_graph import DependencyEdge, DependencyType
        
        # 結果の形式を確認して適用
        if 'mappings' in result:
            # 最適化結果の場合
            for mapping_dict in result['mappings']:
                edge = DependencyEdge(
                    from_node=mapping_dict['from_node'],
                    to_node=mapping_dict['to_node'],
                    dependency_type=DependencyType(mapping_dict['type']),
                    resource_path=mapping_dict.get('resource', ''),
                    description=mapping_dict.get('description', '')
                )
                graph.add_dependency(edge)
        elif hasattr(result, 'mappings'):
            # DependencyGraphオブジェクトの場合
            for mapping in result.mappings:
                edge = DependencyEdge(
                    from_node=mapping.from_node_id,
                    to_node=mapping.to_node_id,
                    dependency_type=mapping.dependency_type,
                    resource_path=mapping.resource_path,
                    description=mapping.description
                )
                graph.add_dependency(edge)

