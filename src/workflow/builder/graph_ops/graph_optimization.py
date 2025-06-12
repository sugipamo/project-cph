"""グラフ最適化の純粋関数"""
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from .dependency_mapping import DependencyGraph, DependencyMapping


@dataclass(frozen=True)
class OptimizationResult:
    """最適化結果（不変データ構造）"""
    optimized_graph: DependencyGraph
    removed_edges: List[DependencyMapping]
    optimization_stats: Dict[str, int]
    
    @property
    def edge_reduction_ratio(self) -> float:
        """エッジ削減率（純粋関数）"""
        original_count = len(self.optimized_graph.mappings) + len(self.removed_edges)
        if original_count == 0:
            return 0.0
        return len(self.removed_edges) / original_count


def optimize_dependency_order(graph: DependencyGraph) -> Dict:
    """実行効率を考慮して依存関係を最適化（純粋関数）
    
    Args:
        graph: 依存関係グラフ
        
    Returns:
        最適化結果辞書（レガシーAPI互換）
    """
    # 最適化パイプライン
    from ..functional_utils import pipe
    
    optimization_result = pipe(
        graph,
        remove_redundant_dependencies,
        lambda g: merge_parallel_paths(g.optimized_graph),
        lambda g: minimize_critical_path(g.optimized_graph),
        lambda g: balance_parallelism(g.optimized_graph)
    )
    
    # レガシーAPI用の辞書形式に変換
    return {
        'adjacency_list': optimization_result.optimized_graph.adjacency_dict,
        'mappings': [m.to_edge_dict() for m in optimization_result.optimized_graph.mappings],
        'stats': optimization_result.optimization_stats
    }


def remove_redundant_dependencies(graph: DependencyGraph) -> OptimizationResult:
    """冗長な依存関係を削除（純粋関数）
    
    Args:
        graph: 元グラフ
        
    Returns:
        最適化結果
    """
    # 推移的依存関係を検出・削除
    adj = graph.adjacency_dict
    all_nodes = list(graph.node_ids)
    
    # 推移的に到達可能なノードペアを計算
    transitive_pairs = _find_transitive_dependencies(adj, all_nodes)
    
    # 推移的依存関係を除去
    filtered_mappings = []
    removed_mappings = []
    
    for mapping in graph.mappings:
        edge = (mapping.from_node_id, mapping.to_node_id)
        if edge in transitive_pairs:
            removed_mappings.append(mapping)
        else:
            filtered_mappings.append(mapping)
    
    optimized_graph = DependencyGraph(filtered_mappings)
    stats = {
        'removed_transitive': len(removed_mappings),
        'remaining_edges': len(filtered_mappings)
    }
    
    return OptimizationResult(optimized_graph, removed_mappings, stats)


def merge_parallel_paths(graph: DependencyGraph) -> OptimizationResult:
    """並列実行可能なパスをマージ（純粋関数）
    
    Args:
        graph: 依存関係グラフ
        
    Returns:
        最適化結果
    """
    # 共通の依存先を持つノード群を特定
    dependency_groups = _group_nodes_by_dependencies(graph)
    
    # マージ可能な依存関係を統合
    merged_mappings = []
    removed_mappings = []
    
    for mapping in graph.mappings:
        # 現在は単純にすべて保持（実装拡張ポイント）
        merged_mappings.append(mapping)
    
    optimized_graph = DependencyGraph(merged_mappings)
    stats = {
        'merged_groups': len(dependency_groups),
        'merged_edges': len(removed_mappings)
    }
    
    return OptimizationResult(optimized_graph, removed_mappings, stats)


def minimize_critical_path(graph: DependencyGraph) -> OptimizationResult:
    """クリティカルパスを最小化（純粋関数）
    
    Args:
        graph: 依存関係グラフ
        
    Returns:
        最適化結果
    """
    # クリティカルパスを計算
    critical_paths = _find_critical_paths(graph)
    
    # 非クリティカルな依存関係の中で削除可能なものを特定
    removable_mappings = _identify_removable_dependencies(graph, critical_paths)
    
    # 削除可能な依存関係を除去
    remaining_mappings = [
        mapping for mapping in graph.mappings 
        if mapping not in removable_mappings
    ]
    
    optimized_graph = DependencyGraph(remaining_mappings)
    stats = {
        'critical_paths': len(critical_paths),
        'removed_non_critical': len(removable_mappings)
    }
    
    return OptimizationResult(optimized_graph, removable_mappings, stats)


def balance_parallelism(graph: DependencyGraph) -> OptimizationResult:
    """並列性のバランスを調整（純粋関数）
    
    Args:
        graph: 依存関係グラフ
        
    Returns:
        最適化結果
    """
    # 現在の並列レベルを分析
    parallel_levels = _analyze_parallel_levels(graph)
    
    # バランス調整（現在は分析のみ、実装拡張ポイント）
    optimized_graph = graph  # 現状は変更なし
    removed_mappings = []
    
    stats = {
        'parallel_levels': len(parallel_levels),
        'max_parallelism': max((len(level) for level in parallel_levels), default=0),
        'avg_parallelism': sum(len(level) for level in parallel_levels) / len(parallel_levels) if parallel_levels else 0
    }
    
    return OptimizationResult(optimized_graph, removed_mappings, stats)


def _find_transitive_dependencies(adj: Dict[str, Set[str]], all_nodes: List[str]) -> Set[Tuple[str, str]]:
    """推移的依存関係を発見（純粋関数）"""
    # Floyd-Warshall風のアルゴリズムで推移的閉包を計算
    reachable = {}
    
    # 初期化：直接の依存関係
    for node in all_nodes:
        reachable[node] = adj.get(node, set()).copy()
    
    # 推移的閉包を計算
    for k in all_nodes:
        for i in all_nodes:
            for j in all_nodes:
                if k in reachable.get(i, set()) and j in reachable.get(k, set()):
                    if i not in reachable:
                        reachable[i] = set()
                    reachable[i].add(j)
    
    # 推移的依存関係を特定
    transitive_pairs = set()
    for from_node in all_nodes:
        for to_node in reachable.get(from_node, set()):
            # 中間ノード経由でアクセス可能かチェック
            for intermediate in all_nodes:
                if (intermediate != from_node and intermediate != to_node and
                    intermediate in adj.get(from_node, set()) and
                    to_node in reachable.get(intermediate, set())):
                    transitive_pairs.add((from_node, to_node))
                    break
    
    return transitive_pairs


def _group_nodes_by_dependencies(graph: DependencyGraph) -> Dict[str, List[str]]:
    """依存関係別にノードをグループ化（純粋関数）"""
    reverse_adj = graph.reverse_adjacency_dict
    groups = {}
    
    for node_id in graph.node_ids:
        deps = frozenset(reverse_adj.get(node_id, set()))
        deps_key = str(sorted(deps))
        
        if deps_key not in groups:
            groups[deps_key] = []
        groups[deps_key].append(node_id)
    
    return groups


def _find_critical_paths(graph: DependencyGraph) -> List[List[str]]:
    """クリティカルパスを発見（純粋関数）"""
    adj = graph.adjacency_dict
    reverse_adj = graph.reverse_adjacency_dict
    
    # ソースノード（依存関係なし）とシンクノード（被依存なし）を特定
    source_nodes = [node for node in graph.node_ids if not reverse_adj.get(node)]
    sink_nodes = [node for node in graph.node_ids if not adj.get(node)]
    
    critical_paths = []
    
    # 各ソースから各シンクへの最長パスを計算
    for source in source_nodes:
        for sink in sink_nodes:
            path = _find_longest_path(source, sink, adj)
            if path:
                critical_paths.append(path)
    
    return critical_paths


def _find_longest_path(start: str, end: str, adj: Dict[str, Set[str]]) -> List[str]:
    """最長パスを発見（純粋関数）"""
    # DFSで最長パスを探索
    def dfs(node: str, target: str, visited: Set[str], path: List[str]) -> List[str]:
        if node == target:
            return path + [node]
        
        visited.add(node)
        longest = []
        
        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                result = dfs(neighbor, target, visited.copy(), path + [node])
                if len(result) > len(longest):
                    longest = result
        
        return longest
    
    return dfs(start, end, set(), [])


def _identify_removable_dependencies(graph: DependencyGraph, critical_paths: List[List[str]]) -> List[DependencyMapping]:
    """削除可能な依存関係を特定（純粋関数）"""
    # クリティカルパス上のエッジを抽出
    critical_edges = set()
    for path in critical_paths:
        for i in range(len(path) - 1):
            critical_edges.add((path[i], path[i + 1]))
    
    # クリティカルでない依存関係を削除候補とする
    removable = []
    for mapping in graph.mappings:
        edge = (mapping.from_node_id, mapping.to_node_id)
        if edge not in critical_edges:
            # 安全性チェック：削除してもグラフの連結性が保たれるか
            if _is_safe_to_remove(edge, graph):
                removable.append(mapping)
    
    return removable


def _is_safe_to_remove(edge: Tuple[str, str], graph: DependencyGraph) -> bool:
    """エッジを安全に削除できるかチェック（純粋関数）"""
    from_node, to_node = edge
    adj = graph.adjacency_dict
    
    # 他のパス経由でアクセス可能かチェック
    # 簡易実装：現在は常にFalse（安全側）
    return False


def _analyze_parallel_levels(graph: DependencyGraph) -> List[List[str]]:
    """並列レベルを分析（純粋関数）"""
    from .cycle_detection import topological_sort
    
    # トポロジカル順序を取得
    topo_order = topological_sort(graph)
    if not topo_order:
        return []
    
    # レベル別にグループ化
    reverse_adj = graph.reverse_adjacency_dict
    levels = []
    level_map = {}
    
    for node in topo_order:
        dependencies = reverse_adj.get(node, set())
        if not dependencies:
            # 依存関係なし（レベル0）
            node_level = 0
        else:
            # 依存ノードの最大レベル + 1
            node_level = max(level_map.get(dep, 0) for dep in dependencies) + 1
        
        level_map[node] = node_level
        
        # レベルリストを拡張
        while len(levels) <= node_level:
            levels.append([])
        
        levels[node_level].append(node)
    
    return levels