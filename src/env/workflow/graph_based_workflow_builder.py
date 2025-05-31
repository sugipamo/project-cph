"""
グラフベースのワークフロービルダー

ConfigNodeからRequestExecutionGraphを生成し、
依存関係を考慮した実行計画を構築する
"""
from typing import List, Dict, Any, Tuple, Optional
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController
from src.context.resolver.config_node import ConfigNode
from .request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
from .graph_to_composite_adapter import GraphToCompositeAdapter
from src.operations.composite.composite_request import CompositeRequest
from src.env.step_generation.step import Step, StepType, StepContext
from src.env.step_generation.core import generate_steps_from_json
from src.env.step_generation.dependency import resolve_dependencies
from src.env.step_generation.workflow import (
    create_step_context_from_env_context,
    optimize_workflow_steps
)
from pathlib import Path


class GraphBasedWorkflowBuilder:
    """グラフベースのワークフロー生成器"""
    
    def __init__(self, controller: EnvResourceController, operations: DIContainer):
        self.controller = controller
        self.operations = operations
    
    @classmethod
    def from_controller(
        cls, 
        controller: EnvResourceController, 
        operations: DIContainer
    ) -> 'GraphBasedWorkflowBuilder':
        """
        controllerとoperationsからGraphBasedWorkflowBuilderを生成
        """
        return cls(controller, operations)
    
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
        # EnvContext から StepContext を作成
        context = create_step_context_from_env_context(self.controller.env_context)
        
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
        step_nodes: List[ConfigNode]
    ) -> Tuple[RequestExecutionGraph, List[str], List[str]]:
        """
        ConfigNodeのリストからRequestExecutionGraphを生成
        
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
        """
        グラフからCompositeRequestを生成（後方互換性）
        
        Args:
            graph: RequestExecutionGraph
            
        Returns:
            CompositeRequest: 順次実行用のコンポジットリクエスト
        """
        return GraphToCompositeAdapter.to_composite_request(graph)
    
    def _build_graph_from_steps(self, steps: List[Step]) -> RequestExecutionGraph:
        """
        Stepリストから実行グラフを構築
        
        Args:
            steps: ステップのリスト
            
        Returns:
            RequestExecutionGraph: 構築されたグラフ
        """
        graph = RequestExecutionGraph()
        node_map: Dict[int, RequestNode] = {}
        
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
        """
        StepからRequestを生成
        
        Args:
            step: 変換するステップ
            
        Returns:
            生成されたリクエスト、または None
        """
        from src.env.factory.request_factory_selector import RequestFactorySelector
        
        # ファクトリセレクタを使用してリクエストを生成
        try:
            factory = RequestFactorySelector.get_factory_for_step_type(
                step.type.value, 
                self.controller, 
                self.operations
            )
            return factory.create_request(step)
        except KeyError:
            # 未知のステップタイプの場合はNoneを返す
            return None
    
    def _extract_resource_info_from_step(
        self, 
        step: Step
    ) -> Tuple[set, set, set, set]:
        """
        ステップからリソース情報を抽出
        
        Returns:
            (creates_files, creates_dirs, reads_files, requires_dirs)
        """
        creates_files = set()
        creates_dirs = set()
        reads_files = set()
        requires_dirs = set()
        
        if step.type == StepType.MKDIR:
            creates_dirs.add(step.cmd[0])
        
        elif step.type == StepType.TOUCH:
            creates_files.add(step.cmd[0])
            # touchは親ディレクトリも必要
            parent = str(Path(step.cmd[0]).parent)
            if parent != '.':
                requires_dirs.add(parent)
        
        elif step.type in [StepType.COPY, StepType.MOVE]:
            if len(step.cmd) >= 2:
                reads_files.add(step.cmd[0])
                creates_files.add(step.cmd[1])
                # 宛先の親ディレクトリが必要
                parent = str(Path(step.cmd[1]).parent)
                if parent != '.':
                    requires_dirs.add(parent)
        
        elif step.type == StepType.MOVETREE:
            if len(step.cmd) >= 2:
                reads_files.add(step.cmd[0])  # ソースディレクトリ
                creates_dirs.add(step.cmd[1])  # 宛先ディレクトリ
        
        elif step.type in [StepType.REMOVE, StepType.RMTREE]:
            reads_files.add(step.cmd[0])  # 削除対象
        
        elif step.type == StepType.BUILD:
            # ビルドコマンドは特定のディレクトリで実行される可能性
            if len(step.cmd) > 0:
                requires_dirs.add(step.cmd[0])
        
        return creates_files, creates_dirs, reads_files, requires_dirs
    
    def _build_dependencies(
        self, 
        graph: RequestExecutionGraph, 
        nodes: List[RequestNode]
    ) -> None:
        """
        ノード間の依存関係を構築
        
        Args:
            graph: 依存関係を追加するグラフ
            nodes: ノードのリスト
        """
        # リソースベースの依存関係を検出
        for i, from_node in enumerate(nodes):
            for j, to_node in enumerate(nodes):
                if i >= j:
                    continue
                
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
                    
                    # ディレクトリ内のファイル作成依存
                    for file_path in to_node.creates_files:
                        if self._is_parent_directory(dir_path, file_path):
                            edge = DependencyEdge(
                                from_node=from_node.id,
                                to_node=to_node.id,
                                dependency_type=DependencyType.DIRECTORY_CREATION,
                                resource_path=dir_path,
                                description=f"Directory {dir_path} must exist for file {file_path}"
                            )
                            graph.add_dependency(edge)
        
        # 明示的な順序依存を追加（依存関係がないノード間）
        # これにより、元の順序をある程度保持
        for i in range(len(nodes) - 1):
            from_node = nodes[i]
            to_node = nodes[i + 1]
            
            # すでに依存関係がある場合はスキップ
            if to_node.id in graph.adjacency_list.get(from_node.id, set()):
                continue
            
            # 逆方向の依存関係がある場合もスキップ
            if from_node.id in graph.adjacency_list.get(to_node.id, set()):
                continue
            
            # リソースの競合がない場合は順序依存を追加
            if not self._has_resource_conflict(from_node, to_node):
                continue
            
            edge = DependencyEdge(
                from_node=from_node.id,
                to_node=to_node.id,
                dependency_type=DependencyType.EXECUTION_ORDER,
                description="Preserve original execution order"
            )
            graph.add_dependency(edge)
    
    def _is_parent_directory(self, parent_path: str, child_path: str) -> bool:
        """
        parent_pathがchild_pathの親ディレクトリかどうかを判定
        """
        try:
            parent = Path(parent_path).resolve()
            child = Path(child_path).resolve()
            return parent in child.parents
        except:
            # パスの解決に失敗した場合は文字列で判定
            return child_path.startswith(parent_path + '/')
    
    def _has_resource_conflict(
        self, 
        node1: RequestNode, 
        node2: RequestNode
    ) -> bool:
        """
        2つのノード間でリソースの競合があるかどうかを判定
        
        Args:
            node1: 最初のノード
            node2: 2番目のノード
            
        Returns:
            bool: 競合がある場合True
        """
        # 同じファイルへの書き込み
        if node1.creates_files & node2.creates_files:
            return True
        
        # 同じディレクトリの作成
        if node1.creates_dirs & node2.creates_dirs:
            return True
        
        # 一方が作成し、他方が削除するファイル
        if (node1.creates_files & node2.reads_files) or \
           (node2.creates_files & node1.reads_files):
            return True
        
        return False
    
    def validate_graph(
        self, 
        graph: RequestExecutionGraph
    ) -> Tuple[bool, List[str]]:
        """
        グラフの妥当性を検証
        
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
            messages.append(f"Failed to determine execution groups: {str(e)}")
        
        return is_valid, messages