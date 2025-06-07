"""
グラフベースのワークフロービルダー

ConfigNodeからRequestExecutionGraphを生成し、
依存関係を考慮した実行計画を構築する
"""
from typing import List, Dict, Any, Tuple, Optional
from src.context.resolver.config_node import ConfigNode
from .request_execution_graph import (
    RequestExecutionGraph,
    RequestNode,
    DependencyEdge,
    DependencyType
)
# from .graph_to_composite_adapter import GraphToCompositeAdapter  # Temporarily disabled
from src.domain.requests.composite.composite_request import CompositeRequest
from src.workflow.step.step import Step, StepType, StepContext
from src.workflow.step.core import generate_steps_from_json
from src.workflow.step.dependency import resolve_dependencies
from src.workflow.step.workflow import (
    create_step_context_from_env_context,
    optimize_workflow_steps
)
from pathlib import Path


class GraphBasedWorkflowBuilder:
    """グラフベースのワークフロー生成器"""
    
    def __init__(self, context: Optional[Any] = None):
        """
        純粋なワークフロービルダー
        
        Args:
            context: StepContextまたは環境情報（オプション）
        """
        self.context = context
    
    @classmethod
    def from_context(cls, context: Any) -> 'GraphBasedWorkflowBuilder':
        """
        コンテキストからGraphBasedWorkflowBuilderを生成
        
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
        """
        controller(既存互換性のため保持)
        """
        # controllerからcontextを抽出
        from src.workflow.step.workflow import create_step_context_from_env_context
        context = create_step_context_from_env_context(controller.env_context)
        return cls(context)
    
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
        # デバッグ設定を取得
        debug_config = None
        if self.context and hasattr(self.context, 'env_json') and self.context.env_json:
            language_config = self.context.env_json.get(self.context.language, {})
            debug_config = language_config.get('debug')
        
        graph = RequestExecutionGraph(debug_config)
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
        StepからRequestを生成（統一ファクトリー版）
        
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
    ) -> Tuple[set, set, set, set]:
        """
        ステップからリソース情報を抽出（純粋関数版使用）
        
        Returns:
            (creates_files, creates_dirs, reads_files, requires_dirs)
        """
        from src.workflow.workflow.graph_builder_utils import extract_node_resource_info_pure
        return extract_node_resource_info_pure(step)
    
    def _build_dependencies(
        self, 
        graph: RequestExecutionGraph, 
        nodes: List[RequestNode]
    ) -> None:
        """
        ノード間の依存関係を構築（最適化版）
        
        Args:
            graph: 依存関係を追加するグラフ
            nodes: ノードのリスト
        """
        from collections import defaultdict
        
        # リソースからノードへのインデックスを構築（O(n)）
        file_creators = defaultdict(list)  # file_path -> [(node_idx, node)]
        dir_creators = defaultdict(list)   # dir_path -> [(node_idx, node)]
        file_readers = defaultdict(list)   # file_path -> [(node_idx, node)]
        dir_requirers = defaultdict(list)  # dir_path -> [(node_idx, node)]
        
        for idx, node in enumerate(nodes):
            for file_path in node.creates_files:
                file_creators[file_path].append((idx, node))
            for dir_path in node.creates_dirs:
                dir_creators[dir_path].append((idx, node))
            for file_path in node.reads_files:
                file_readers[file_path].append((idx, node))
            for dir_path in node.requires_dirs:
                dir_requirers[dir_path].append((idx, node))
        
        # ファイル作成依存を検出（O(m)、mは依存関係数）
        for file_path, creators in file_creators.items():
            if file_path in file_readers:
                for creator_idx, creator in creators:
                    for reader_idx, reader in file_readers[file_path]:
                        if creator_idx < reader_idx:  # 順序を保持
                            edge = DependencyEdge(
                                from_node=creator.id,
                                to_node=reader.id,
                                dependency_type=DependencyType.FILE_CREATION,
                                resource_path=file_path,
                                description=f"File {file_path} must be created before being read"
                            )
                            graph.add_dependency(edge)
        
        # ディレクトリ作成依存を検出
        for dir_path, creators in dir_creators.items():
            if dir_path in dir_requirers:
                for creator_idx, creator in creators:
                    for requirer_idx, requirer in dir_requirers[dir_path]:
                        if creator_idx < requirer_idx:
                            edge = DependencyEdge(
                                from_node=creator.id,
                                to_node=requirer.id,
                                dependency_type=DependencyType.DIRECTORY_CREATION,
                                resource_path=dir_path,
                                description=f"Directory {dir_path} must be created before being used"
                            )
                            graph.add_dependency(edge)
        
        # ディレクトリ内のファイル作成依存（最適化：必要な場合のみチェック）
        for idx, node in enumerate(nodes):
            if node.creates_files:
                # このノードが作成するファイルの親ディレクトリを収集
                parent_dirs = set()
                for file_path in node.creates_files:
                    parent = str(Path(file_path).parent)
                    if parent != '.':
                        parent_dirs.add(parent)
                
                # 必要な親ディレクトリを作成するノードを検索
                for parent_dir in parent_dirs:
                    # 完全一致または親ディレクトリを作成するノードを探す
                    for check_dir, creators in dir_creators.items():
                        if self._is_parent_directory(check_dir, parent_dir) or check_dir == parent_dir:
                            for creator_idx, creator in creators:
                                if creator_idx < idx:
                                    edge = DependencyEdge(
                                        from_node=creator.id,
                                        to_node=node.id,
                                        dependency_type=DependencyType.DIRECTORY_CREATION,
                                        resource_path=check_dir,
                                        description=f"Directory {check_dir} must exist for files in {parent_dir}"
                                    )
                                    graph.add_dependency(edge)
                                    break  # 同じディレクトリに対して複数の依存を追加しない
        
        # 明示的な順序依存を追加（競合がある場合のみ）
        for i in range(len(nodes) - 1):
            from_node = nodes[i]
            to_node = nodes[i + 1]
            
            # すでに依存関係がある場合はスキップ
            if to_node.id in graph.adjacency_list.get(from_node.id, set()):
                continue
            
            # 逆方向の依存関係がある場合もスキップ
            if from_node.id in graph.adjacency_list.get(to_node.id, set()):
                continue
            
            # リソースの競合がある場合のみ順序依存を追加
            if self._has_resource_conflict(from_node, to_node):
                edge = DependencyEdge(
                    from_node=from_node.id,
                    to_node=to_node.id,
                    dependency_type=DependencyType.EXECUTION_ORDER,
                    description="Preserve original execution order due to resource conflict"
                )
                graph.add_dependency(edge)
    
    def _is_parent_directory(self, parent_path: str, child_path: str) -> bool:
        """
        parent_pathがchild_pathの親ディレクトリかどうかを判定（純粋関数版使用）
        """
        from src.workflow.workflow.graph_builder_utils import is_parent_directory_pure
        return is_parent_directory_pure(parent_path, child_path)
    
    def _has_resource_conflict(
        self, 
        node1: RequestNode, 
        node2: RequestNode
    ) -> bool:
        """
        2つのノード間でリソースの競合があるかどうかを判定（純粋関数版使用）
        
        Args:
            node1: 最初のノード
            node2: 2番目のノード
            
        Returns:
            bool: 競合がある場合True
        """
        from src.workflow.workflow.graph_builder_utils import NodeInfo, has_resource_conflict_pure
        
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
        
        return has_resource_conflict_pure(node_info1, node_info2)
    
    def build_graph_pure(
        self,
        steps: List[Step]
    ) -> Tuple[RequestExecutionGraph, List[str], List[str]]:
        """
        純粋関数を使用したグラフ構築
        
        Args:
            steps: ステップのリスト
            
        Returns:
            Tuple[RequestExecutionGraph, List[str], List[str]]: 
                (実行グラフ, エラーリスト, 警告リスト)
        """
        from src.workflow.workflow.graph_builder_utils import build_execution_graph_pure
        
        # 純粋関数でグラフ構築結果を取得
        result = build_execution_graph_pure(steps, self.context)
        
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