"""循環依存検出の純粋関数"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from .dependency_mapping import DependencyGraph


@dataclass(frozen=True)
class CycleInfo:
    """循環依存情報（不変データ構造）"""
    cycle_nodes: List[str]
    cycle_edges: List[Tuple[str, str]]
    cycle_length: int

    @property
    def has_cycle(self) -> bool:
        """循環があるかどうか（純粋関数）"""
        return len(self.cycle_nodes) > 0

    def format_cycle_description(self) -> str:
        """循環の説明をフォーマット（純粋関数）"""
        if not self.has_cycle:
            return "No cycles detected"

        cycle_path = " -> ".join([*self.cycle_nodes, self.cycle_nodes[0]])
        return f"Cycle detected: {cycle_path} (length: {self.cycle_length})"


def validate_no_circular_dependencies(graph: DependencyGraph) -> DependencyGraph:
    """循環依存をチェック、エラー時は例外（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        検証済みグラフ（循環がない場合）

    Raises:
        ValueError: 循環依存が検出された場合
    """
    cycle_info = detect_cycles(graph)

    if cycle_info.has_cycle:
        error_message = _format_cycle_error(cycle_info, graph)
        raise ValueError(f"Circular dependency detected: {error_message}")

    return graph


def detect_cycles(graph: DependencyGraph) -> CycleInfo:
    """循環依存を検出（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        循環依存情報
    """
    adj = graph.adjacency_dict
    all_nodes = list(graph.node_ids)

    # DFS based cycle detection
    visited = set()
    rec_stack = set()

    for node in all_nodes:
        if node not in visited:
            cycle_path = _dfs_detect_cycle(node, adj, visited, rec_stack, [])
            if cycle_path:
                cycle_edges = _extract_cycle_edges(cycle_path)
                return CycleInfo(
                    cycle_nodes=cycle_path,
                    cycle_edges=cycle_edges,
                    cycle_length=len(cycle_path) - 1
                )

    # 循環なし
    return CycleInfo(cycle_nodes=[], cycle_edges=[], cycle_length=0)


def _dfs_detect_cycle(node: str, adj: Dict[str, Set[str]], visited: Set[str],
                     rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
    """DFSによる循環検出（純粋関数）"""
    visited.add(node)
    rec_stack.add(node)
    path.append(node)

    for neighbor in adj.get(node, set()):
        if neighbor not in visited:
            result = _dfs_detect_cycle(neighbor, adj, visited, rec_stack, path.copy())
            if result:
                return result
        elif neighbor in rec_stack:
            # 循環を発見 - 循環部分のパスを抽出
            cycle_start_idx = path.index(neighbor)
            return path[cycle_start_idx:] + [neighbor]

    rec_stack.remove(node)
    return None


def _extract_cycle_edges(cycle_path: List[str]) -> List[Tuple[str, str]]:
    """循環パスからエッジを抽出（純粋関数）"""
    edges = []
    for i in range(len(cycle_path) - 1):
        edges.append((cycle_path[i], cycle_path[i + 1]))
    return edges


def find_all_cycles(graph: DependencyGraph) -> List[CycleInfo]:
    """すべての循環を検出（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        すべての循環情報のリスト
    """
    adj = graph.adjacency_dict
    all_nodes = list(graph.node_ids)
    cycles = []
    visited_global = set()

    for node in all_nodes:
        if node not in visited_global:
            node_cycles = _find_cycles_from_node(node, adj, visited_global)
            cycles.extend(node_cycles)

    return cycles


def _find_cycles_from_node(start_node: str, adj: Dict[str, Set[str]],
                          visited_global: Set[str]) -> List[CycleInfo]:
    """特定ノードから開始する循環を検出（純粋関数）"""
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]):
        if node in visited_global:
            return

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # 循環発見
                cycle_start_idx = path.index(neighbor)
                cycle_path = path[cycle_start_idx:] + [neighbor]
                cycle_edges = _extract_cycle_edges(cycle_path)
                cycle_info = CycleInfo(
                    cycle_nodes=cycle_path,
                    cycle_edges=cycle_edges,
                    cycle_length=len(cycle_path) - 1
                )
                cycles.append(cycle_info)

        rec_stack.remove(node)

    dfs(start_node, [])
    visited_global.update(visited)
    return cycles


def break_cycles_by_priority(graph: DependencyGraph,
                           priority_order: List[str]) -> DependencyGraph:
    """優先度に基づいて循環を解消（純粋関数）

    Args:
        graph: 依存関係グラフ
        priority_order: ノードの優先度順序（高優先度が先頭）

    Returns:
        循環を解消したグラフ
    """
    current_graph = graph
    max_iterations = len(graph.mappings)  # 無限ループ防止

    for _ in range(max_iterations):
        cycle_info = detect_cycles(current_graph)
        if not cycle_info.has_cycle:
            break

        # 優先度の低いエッジを削除
        edge_to_remove = _select_edge_to_remove(cycle_info, priority_order)
        current_graph = _remove_edge_from_graph(current_graph, edge_to_remove)

    return current_graph


def _select_edge_to_remove(cycle_info: CycleInfo, priority_order: List[str]) -> Tuple[str, str]:
    """削除するエッジを選択（純粋関数）"""
    # 優先度マップを作成
    priority_map = {node: i for i, node in enumerate(priority_order)}

    # 循環内で最も優先度の低いノードから出るエッジを選択
    worst_priority = -1
    edge_to_remove = cycle_info.cycle_edges[0]

    for from_node, to_node in cycle_info.cycle_edges:
        from_priority = priority_map.get(from_node, len(priority_order))
        if from_priority > worst_priority:
            worst_priority = from_priority
            edge_to_remove = (from_node, to_node)

    return edge_to_remove


def _remove_edge_from_graph(graph: DependencyGraph, edge: Tuple[str, str]) -> DependencyGraph:
    """グラフからエッジを削除（純粋関数）"""
    from_node, to_node = edge
    filtered_mappings = [
        mapping for mapping in graph.mappings
        if not (mapping.from_node_id == from_node and mapping.to_node_id == to_node)
    ]
    return DependencyGraph(filtered_mappings)


def is_acyclic(graph: DependencyGraph) -> bool:
    """グラフが非循環かどうかをチェック（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        非循環の場合True
    """
    cycle_info = detect_cycles(graph)
    return not cycle_info.has_cycle


def topological_sort(graph: DependencyGraph) -> Optional[List[str]]:
    """トポロジカルソート（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        トポロジカル順序（循環がある場合はNone）
    """
    if not is_acyclic(graph):
        return None

    adj = graph.adjacency_dict
    reverse_adj = graph.reverse_adjacency_dict
    all_nodes = list(graph.node_ids)

    # Kahn's algorithm
    in_degree = {node: len(reverse_adj.get(node, set())) for node in all_nodes}
    queue = [node for node in all_nodes if in_degree[node] == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        for neighbor in adj.get(node, set()):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result if len(result) == len(all_nodes) else None


def _format_cycle_error(cycle_info: CycleInfo, graph: DependencyGraph) -> str:
    """循環エラーメッセージをフォーマット（純粋関数）"""
    lines = [cycle_info.format_cycle_description()]

    # 循環に関わる依存関係の詳細を追加
    cycle_edges_set = set(cycle_info.cycle_edges)
    lines.append("\nDependency details in cycle:")

    for mapping in graph.mappings:
        edge = (mapping.from_node_id, mapping.to_node_id)
        if edge in cycle_edges_set:
            lines.append(f"  {mapping.from_node_id} -> {mapping.to_node_id} "
                        f"({mapping.dependency_type.value}): {mapping.description}")

    return "\n".join(lines)
