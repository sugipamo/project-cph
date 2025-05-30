"""
グラフベースのリクエスト実行システム（実験実装）

将来的なグラフベース管理への移行のためのプロトタイプ
現在のリストベースシステムとの互換性を保ちながら段階的に導入
"""
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import networkx as nx
from .step import Step, StepType


class DependencyType(Enum):
    """依存関係の種類"""
    FILE_CREATION = "file_creation"      # ファイル作成依存
    DIRECTORY_CREATION = "dir_creation"  # ディレクトリ作成依存
    RESOURCE_ACCESS = "resource_access"  # リソースアクセス依存
    EXECUTION_ORDER = "exec_order"       # 実行順序依存


@dataclass(frozen=True)
class RequestNode:
    """リクエストノード（グラフの頂点）"""
    id: str
    request: object  # BaseRequest
    step: Optional[Step] = None
    
    # 実行情報
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[object] = None
    
    # リソース情報
    creates_files: Set[str] = field(default_factory=set)
    creates_dirs: Set[str] = field(default_factory=set)
    reads_files: Set[str] = field(default_factory=set)
    requires_dirs: Set[str] = field(default_factory=set)


@dataclass(frozen=True)
class DependencyEdge:
    """依存関係エッジ（グラフの辺）"""
    from_node: str
    to_node: str
    dependency_type: DependencyType
    resource_path: Optional[str] = None
    description: str = ""


class RequestExecutionGraph:
    """リクエスト実行グラフ"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, RequestNode] = {}
        self.edges: List[DependencyEdge] = []
    
    def add_request_node(self, node: RequestNode) -> None:
        """リクエストノードを追加"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, data=node)
    
    def add_dependency(self, edge: DependencyEdge) -> None:
        """依存関係を追加"""
        self.edges.append(edge)
        self.graph.add_edge(edge.from_node, edge.to_node, data=edge)
    
    def detect_cycles(self) -> List[List[str]]:
        """循環依存を検出"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXError:
            return []
    
    def get_execution_order(self) -> List[str]:
        """トポロジカルソートによる実行順序を取得"""
        if self.detect_cycles():
            raise ValueError("Circular dependency detected")
        
        return list(nx.topological_sort(self.graph))
    
    def get_parallel_groups(self) -> List[List[str]]:
        """並行実行可能なノードグループを取得"""
        execution_order = self.get_execution_order()
        groups = []
        remaining = set(execution_order)
        
        while remaining:
            # 依存関係のないノードを見つける
            ready_nodes = []
            for node_id in remaining:
                predecessors = set(self.graph.predecessors(node_id))
                if not predecessors.intersection(remaining):
                    ready_nodes.append(node_id)
            
            if not ready_nodes:
                raise ValueError("Unable to find executable nodes - possible deadlock")
            
            groups.append(ready_nodes)
            remaining -= set(ready_nodes)
        
        return groups
    
    def execute_sequential(self, driver=None) -> List[object]:
        """順次実行（既存システムとの互換性）"""
        execution_order = self.get_execution_order()
        results = []
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            result = node.request.execute(driver=driver)
            results.append(result)
            
            # ノードの状態を更新
            updated_node = RequestNode(
                id=node.id,
                request=node.request,
                step=node.step,
                status="completed" if getattr(result, 'success', True) else "failed",
                result=result,
                creates_files=node.creates_files,
                creates_dirs=node.creates_dirs,
                reads_files=node.reads_files,
                requires_dirs=node.requires_dirs
            )
            self.nodes[node_id] = updated_node
        
        return results
    
    def execute_parallel(self, driver=None, max_workers: int = 4) -> List[object]:
        """並行実行"""
        parallel_groups = self.get_parallel_groups()
        all_results = {}
        
        for group in parallel_groups:
            if len(group) == 1:
                # 単一ノードは直接実行
                node_id = group[0]
                node = self.nodes[node_id]
                result = node.request.execute(driver=driver)
                all_results[node_id] = result
            else:
                # 複数ノードは並行実行
                with ThreadPoolExecutor(max_workers=min(max_workers, len(group))) as executor:
                    futures = {}
                    
                    for node_id in group:
                        node = self.nodes[node_id]
                        future = executor.submit(node.request.execute, driver=driver)
                        futures[future] = node_id
                    
                    for future in as_completed(futures):
                        node_id = futures[future]
                        result = future.result()
                        all_results[node_id] = result
        
        # 実行順序に従って結果を並べ替え
        execution_order = self.get_execution_order()
        return [all_results[node_id] for node_id in execution_order]


def build_execution_graph_from_steps(steps: List[Step]) -> RequestExecutionGraph:
    """Stepリストから実行グラフを構築"""
    from .request_converter import step_to_request
    
    graph = RequestExecutionGraph()
    
    # ノードを作成
    for i, step in enumerate(steps):
        request = step_to_request(step)
        if not request:
            continue
        
        # ステップからリソース情報を抽出
        creates_files, creates_dirs, reads_files, requires_dirs = extract_resource_info(step)
        
        node = RequestNode(
            id=f"step_{i}",
            request=request,
            step=step,
            creates_files=creates_files,
            creates_dirs=creates_dirs,
            reads_files=reads_files,
            requires_dirs=requires_dirs
        )
        
        graph.add_request_node(node)
    
    # 依存関係を構築
    node_ids = list(graph.nodes.keys())
    for i, from_id in enumerate(node_ids):
        for j, to_id in enumerate(node_ids[i+1:], i+1):
            from_node = graph.nodes[from_id]
            to_node = graph.nodes[to_id]
            
            # 依存関係を検出
            dependencies = detect_dependencies(from_node, to_node)
            for dep in dependencies:
                graph.add_dependency(dep)
    
    return graph


def extract_resource_info(step: Step) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """ステップからリソース情報を抽出"""
    creates_files = set()
    creates_dirs = set()
    reads_files = set()
    requires_dirs = set()
    
    if step.type == StepType.MKDIR:
        creates_dirs.add(step.cmd[0])
    
    elif step.type == StepType.TOUCH:
        creates_files.add(step.cmd[0])
        # touchは親ディレクトリも必要
        from pathlib import Path
        parent = str(Path(step.cmd[0]).parent)
        if parent != '.':
            requires_dirs.add(parent)
    
    elif step.type in [StepType.COPY, StepType.MOVE]:
        reads_files.add(step.cmd[0])
        creates_files.add(step.cmd[1])
        # 宛先の親ディレクトリが必要
        from pathlib import Path
        parent = str(Path(step.cmd[1]).parent)
        if parent != '.':
            requires_dirs.add(parent)
    
    elif step.type == StepType.MOVETREE:
        reads_files.add(step.cmd[0])  # ソースディレクトリ
        creates_dirs.add(step.cmd[1])  # 宛先ディレクトリ
    
    elif step.type in [StepType.REMOVE, StepType.RMTREE]:
        reads_files.add(step.cmd[0])  # 削除対象
    
    return creates_files, creates_dirs, reads_files, requires_dirs


def detect_dependencies(from_node: RequestNode, to_node: RequestNode) -> List[DependencyEdge]:
    """2つのノード間の依存関係を検出"""
    dependencies = []
    
    # ファイル作成依存
    for file_path in from_node.creates_files:
        if file_path in to_node.reads_files:
            dependencies.append(DependencyEdge(
                from_node=from_node.id,
                to_node=to_node.id,
                dependency_type=DependencyType.FILE_CREATION,
                resource_path=file_path,
                description=f"File {file_path} must be created before being read"
            ))
    
    # ディレクトリ作成依存
    for dir_path in from_node.creates_dirs:
        if dir_path in to_node.requires_dirs:
            dependencies.append(DependencyEdge(
                from_node=from_node.id,
                to_node=to_node.id,
                dependency_type=DependencyType.DIRECTORY_CREATION,
                resource_path=dir_path,
                description=f"Directory {dir_path} must be created before being used"
            ))
    
    return dependencies


def compare_execution_strategies(steps: List[Step]) -> Dict[str, object]:
    """リストベースとグラフベースの実行戦略を比較"""
    from .request_converter import steps_to_requests
    from unittest.mock import Mock
    
    # モックのoperations
    mock_operations = Mock()
    mock_operations.resolve.return_value = Mock()
    
    # リストベース実行
    list_based_requests = steps_to_requests(steps, mock_operations)
    
    # グラフベース実行
    graph = build_execution_graph_from_steps(steps)
    
    return {
        'list_based': {
            'request_count': len(list_based_requests.requests),
            'execution_type': 'sequential',
            'parallelizable': False
        },
        'graph_based': {
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
            'parallel_groups': graph.get_parallel_groups(),
            'has_cycles': bool(graph.detect_cycles()),
            'execution_order': graph.get_execution_order()
        }
    }