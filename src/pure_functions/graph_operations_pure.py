"""
グラフ操作の純粋関数
request_execution_graphの中核ロジックを純粋関数として実装
"""
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict, deque


class DependencyType(Enum):
    """依存関係の種類"""
    FILE_CREATION = "file_creation"
    DIRECTORY_CREATION = "dir_creation"
    RESOURCE_ACCESS = "resource_access"
    EXECUTION_ORDER = "exec_order"


@dataclass(frozen=True)
class GraphNode:
    """グラフノードの不変データクラス"""
    id: str
    creates_files: Set[str] = None
    creates_dirs: Set[str] = None
    reads_files: Set[str] = None
    requires_dirs: Set[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        # Setのデフォルト値をセット
        if self.creates_files is None:
            object.__setattr__(self, 'creates_files', set())
        if self.creates_dirs is None:
            object.__setattr__(self, 'creates_dirs', set())
        if self.reads_files is None:
            object.__setattr__(self, 'reads_files', set())
        if self.requires_dirs is None:
            object.__setattr__(self, 'requires_dirs', set())
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class GraphEdge:
    """グラフエッジの不変データクラス"""
    from_node: str
    to_node: str
    dependency_type: DependencyType
    resource_path: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class GraphData:
    """グラフデータの不変データクラス"""
    nodes: Dict[str, GraphNode]
    edges: List[GraphEdge]
    adjacency_list: Dict[str, Set[str]] = None
    reverse_adjacency_list: Dict[str, Set[str]] = None
    
    def __post_init__(self):
        if self.adjacency_list is None:
            object.__setattr__(self, 'adjacency_list', defaultdict(set))
        if self.reverse_adjacency_list is None:
            object.__setattr__(self, 'reverse_adjacency_list', defaultdict(set))


@dataclass(frozen=True)
class TopologicalSortResult:
    """トポロジカルソート結果"""
    sorted_nodes: List[str]
    is_valid: bool
    cycles: List[List[str]] = None
    
    def __post_init__(self):
        if self.cycles is None:
            object.__setattr__(self, 'cycles', [])


@dataclass(frozen=True)
class ParallelGroup:
    """並列実行グループ"""
    level: int
    node_ids: Set[str]


def create_adjacency_lists_pure(
    nodes: Dict[str, GraphNode], 
    edges: List[GraphEdge]
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    ノードとエッジから隣接リストを作成する純粋関数
    
    Args:
        nodes: ノード辞書
        edges: エッジリスト
        
    Returns:
        Tuple[forward_adjacency, reverse_adjacency]
    """
    forward_adj = defaultdict(set)
    reverse_adj = defaultdict(set)
    
    # 全ノードを初期化
    for node_id in nodes.keys():
        forward_adj[node_id] = set()
        reverse_adj[node_id] = set()
    
    # エッジから隣接リストを構築
    for edge in edges:
        forward_adj[edge.from_node].add(edge.to_node)
        reverse_adj[edge.to_node].add(edge.from_node)
    
    return dict(forward_adj), dict(reverse_adj)


def detect_cycles_pure(adjacency_list: Dict[str, Set[str]]) -> List[List[str]]:
    """
    グラフの循環依存を検出する純粋関数
    
    Args:
        adjacency_list: 隣接リスト
        
    Returns:
        検出された循環のリスト
    """
    # DFSベースの循環検出
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in adjacency_list.keys()}
    cycles = []
    
    def dfs(node, path):
        if node not in color:
            # 存在しないノードは無視
            return
            
        if color[node] == GRAY:
            # 循環を発見
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if color[node] == BLACK:
            return
        
        color[node] = GRAY
        for neighbor in adjacency_list.get(node, set()):
            dfs(neighbor, path + [node])
        color[node] = BLACK
    
    for node in adjacency_list.keys():
        if color[node] == WHITE:
            dfs(node, [])
    
    return cycles


def topological_sort_pure(
    nodes: Dict[str, GraphNode], 
    edges: List[GraphEdge]
) -> TopologicalSortResult:
    """
    トポロジカルソートを行う純粋関数
    
    Args:
        nodes: ノード辞書
        edges: エッジリスト
        
    Returns:
        TopologicalSortResult: ソート結果
    """
    # 隣接リストを作成
    forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
    
    # 循環検出
    cycles = detect_cycles_pure(forward_adj)
    if cycles:
        return TopologicalSortResult(
            sorted_nodes=[],
            is_valid=False,
            cycles=cycles
        )
    
    # Kahn's algorithmでトポロジカルソート
    in_degree = {node_id: len(reverse_adj[node_id]) for node_id in nodes.keys()}
    queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
    sorted_nodes = []
    
    while queue:
        current = queue.popleft()
        sorted_nodes.append(current)
        
        for neighbor in forward_adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # 全ノードがソートされたかチェック
    is_valid = len(sorted_nodes) == len(nodes)
    
    return TopologicalSortResult(
        sorted_nodes=sorted_nodes,
        is_valid=is_valid,
        cycles=[] if is_valid else [list(nodes.keys())]
    )


def get_parallel_groups_pure(
    nodes: Dict[str, GraphNode], 
    edges: List[GraphEdge]
) -> List[ParallelGroup]:
    """
    並列実行可能なグループを取得する純粋関数
    
    Args:
        nodes: ノード辞書
        edges: エッジリスト
        
    Returns:
        並列実行グループのリスト
    """
    # トポロジカルソート実行
    sort_result = topological_sort_pure(nodes, edges)
    if not sort_result.is_valid:
        return []
    
    # 隣接リストを作成
    forward_adj, reverse_adj = create_adjacency_lists_pure(nodes, edges)
    
    # レベル別グループ分け
    level_map = {}
    groups = []
    
    for node_id in sort_result.sorted_nodes:
        # このノードの依存関係の最大レベルを計算
        max_dep_level = -1
        for dep_id in reverse_adj[node_id]:
            if dep_id in level_map:
                max_dep_level = max(max_dep_level, level_map[dep_id])
        
        # このノードのレベル
        node_level = max_dep_level + 1
        level_map[node_id] = node_level
        
        # グループに追加
        while len(groups) <= node_level:
            groups.append(ParallelGroup(level=len(groups), node_ids=set()))
        
        groups[node_level].node_ids.add(node_id)
    
    return groups


def analyze_resource_dependencies_pure(
    nodes: Dict[str, GraphNode]
) -> List[GraphEdge]:
    """
    リソース依存関係を分析してエッジを生成する純粋関数
    
    Args:
        nodes: ノード辞書
        
    Returns:
        リソース依存関係のエッジリスト
    """
    edges = []
    
    # ファイル作成 -> ファイル読み取り依存
    file_creators = defaultdict(list)
    file_readers = defaultdict(list)
    
    for node_id, node in nodes.items():
        for file_path in node.creates_files:
            file_creators[file_path].append(node_id)
        for file_path in node.reads_files:
            file_readers[file_path].append(node_id)
    
    for file_path in file_creators.keys():
        if file_path in file_readers:
            for creator in file_creators[file_path]:
                for reader in file_readers[file_path]:
                    if creator != reader:
                        edges.append(GraphEdge(
                            from_node=creator,
                            to_node=reader,
                            dependency_type=DependencyType.FILE_CREATION,
                            resource_path=file_path,
                            description=f"File {file_path} must be created before being read"
                        ))
    
    # ディレクトリ作成 -> ディレクトリ必要依存
    dir_creators = defaultdict(list)
    dir_requirers = defaultdict(list)
    
    for node_id, node in nodes.items():
        for dir_path in node.creates_dirs:
            dir_creators[dir_path].append(node_id)
        for dir_path in node.requires_dirs:
            dir_requirers[dir_path].append(node_id)
    
    for dir_path in dir_creators.keys():
        if dir_path in dir_requirers:
            for creator in dir_creators[dir_path]:
                for requirer in dir_requirers[dir_path]:
                    if creator != requirer:
                        edges.append(GraphEdge(
                            from_node=creator,
                            to_node=requirer,
                            dependency_type=DependencyType.DIRECTORY_CREATION,
                            resource_path=dir_path,
                            description=f"Directory {dir_path} must be created before being used"
                        ))
    
    return edges


def validate_graph_pure(graph_data: GraphData) -> Tuple[bool, List[str]]:
    """
    グラフの妥当性を検証する純粋関数
    
    Args:
        graph_data: グラフデータ
        
    Returns:
        Tuple[is_valid, error_messages]
    """
    errors = []
    
    # ノードが空でないかチェック
    if not graph_data.nodes:
        errors.append("Graph has no nodes")
        return False, errors
    
    # エッジの整合性をチェック
    for edge in graph_data.edges:
        if edge.from_node not in graph_data.nodes:
            errors.append(f"Edge references non-existent from_node: {edge.from_node}")
        if edge.to_node not in graph_data.nodes:
            errors.append(f"Edge references non-existent to_node: {edge.to_node}")
    
    # 循環依存をチェック
    cycles = detect_cycles_pure(graph_data.adjacency_list)
    if cycles:
        errors.append(f"Circular dependencies detected: {cycles}")
    
    # 並列実行グループを検証
    try:
        groups = get_parallel_groups_pure(graph_data.nodes, graph_data.edges)
        if not groups:
            errors.append("Failed to create execution groups")
    except Exception as e:
        errors.append(f"Error creating execution groups: {str(e)}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def optimize_graph_pure(graph_data: GraphData) -> GraphData:
    """
    グラフを最適化する純粋関数
    
    Args:
        graph_data: 最適化前のグラフデータ
        
    Returns:
        最適化されたグラフデータ
    """
    # 重複エッジの除去
    unique_edges = []
    seen_edges = set()
    
    for edge in graph_data.edges:
        edge_key = (edge.from_node, edge.to_node, edge.dependency_type)
        if edge_key not in seen_edges:
            unique_edges.append(edge)
            seen_edges.add(edge_key)
    
    # 推移的縮約（オプション：パフォーマンス要件に応じて）
    # より複雑な最適化は必要に応じて実装
    
    # 隣接リストを再構築
    forward_adj, reverse_adj = create_adjacency_lists_pure(graph_data.nodes, unique_edges)
    
    return GraphData(
        nodes=graph_data.nodes,
        edges=unique_edges,
        adjacency_list=forward_adj,
        reverse_adjacency_list=reverse_adj
    )


def calculate_graph_metrics_pure(graph_data: GraphData) -> Dict[str, Any]:
    """
    グラフのメトリクスを計算する純粋関数
    
    Args:
        graph_data: グラフデータ
        
    Returns:
        メトリクス辞書
    """
    metrics = {
        'node_count': len(graph_data.nodes),
        'edge_count': len(graph_data.edges),
        'max_in_degree': 0,
        'max_out_degree': 0,
        'parallel_groups_count': 0,
        'has_cycles': False
    }
    
    # 次数の計算
    for node_id in graph_data.nodes.keys():
        in_degree = len(graph_data.reverse_adjacency_list.get(node_id, set()))
        out_degree = len(graph_data.adjacency_list.get(node_id, set()))
        
        metrics['max_in_degree'] = max(metrics['max_in_degree'], in_degree)
        metrics['max_out_degree'] = max(metrics['max_out_degree'], out_degree)
    
    # 並列グループ数
    groups = get_parallel_groups_pure(graph_data.nodes, graph_data.edges)
    metrics['parallel_groups_count'] = len(groups)
    
    # 循環依存の有無
    cycles = detect_cycles_pure(graph_data.adjacency_list)
    metrics['has_cycles'] = len(cycles) > 0
    
    return metrics