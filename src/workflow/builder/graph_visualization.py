"""グラフ可視化の純粋関数 - RequestExecutionGraphから分離"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass(frozen=True)
class VisualizationConfig:
    """可視化設定（不変データ構造）"""
    show_node_details: bool = True
    show_edge_details: bool = True
    show_execution_groups: bool = True
    show_statistics: bool = True
    max_nodes_per_line: int = 5
    include_metadata: bool = False


def create_graph_visualization(nodes: Dict[str, Any],
                             edges: List[Any],
                             execution_groups: Optional[List[List[str]]] = None,
                             config: Optional[VisualizationConfig] = None) -> str:
    """グラフの可視化文字列を生成（純粋関数）

    Args:
        nodes: ノード辞書
        edges: エッジリスト
        execution_groups: 実行グループ（オプション）
        config: 可視化設定

    Returns:
        可視化文字列
    """
    if config is None:
        config = VisualizationConfig()

    lines = ["Request Execution Graph:"]

    # 基本統計
    if config.show_statistics:
        lines.extend(_format_basic_statistics(nodes, edges))

    # ノード詳細
    if config.show_node_details:
        lines.extend(_format_node_details(nodes, config))

    # エッジ詳細
    if config.show_edge_details:
        lines.extend(_format_edge_details(edges))

    # 実行グループ
    if config.show_execution_groups and execution_groups:
        lines.extend(_format_execution_groups(execution_groups))

    return '\n'.join(lines)


def _format_basic_statistics(nodes: Dict[str, Any], edges: List[Any]) -> List[str]:
    """基本統計情報をフォーマット（純粋関数）"""
    return [
        f"Nodes: {len(nodes)}",
        f"Edges: {len(edges)}",
        ""
    ]


def _format_node_details(nodes: Dict[str, Any], config: VisualizationConfig) -> List[str]:
    """ノード詳細をフォーマット（純粋関数）"""
    lines = ["Nodes:"]

    for node_id, node in nodes.items():
        node_info = format_node_info(node, config.include_metadata)
        lines.append(f"  {node_id}: {node_info}")

    lines.append("")
    return lines


def _format_edge_details(edges: List[Any]) -> List[str]:
    """エッジ詳細をフォーマット（純粋関数）"""
    lines = ["Dependencies:"]

    for edge in edges:
        edge_info = format_edge_info(edge)
        lines.append(f"  {edge_info}")

    lines.append("")
    return lines


def _format_execution_groups(execution_groups: List[List[str]]) -> List[str]:
    """実行グループをフォーマット（純粋関数）"""
    lines = ["Parallel Execution Groups:"]

    for i, group in enumerate(execution_groups):
        group_info = format_execution_group(i + 1, group)
        lines.append(f"  {group_info}")

    return lines


def format_node_info(node: Any, include_metadata: bool = False) -> str:
    """ノード情報をフォーマット（純粋関数）

    Args:
        node: ノードオブジェクト
        include_metadata: メタデータを含むかどうか

    Returns:
        フォーマット済みノード情報
    """
    # 基本情報
    class_name = getattr(node.request, '__class__', type(node.request)).__name__ if hasattr(node, 'request') else "Unknown"
    status = getattr(node, 'status', 'unknown')

    info_parts = [f"{class_name} (status: {status})"]

    # リソース情報
    resource_info = []
    if hasattr(node, 'creates_files') and node.creates_files:
        resource_info.append(f"creates: {len(node.creates_files)} files")
    if hasattr(node, 'creates_dirs') and node.creates_dirs:
        resource_info.append(f"creates: {len(node.creates_dirs)} dirs")
    if hasattr(node, 'reads_files') and node.reads_files:
        resource_info.append(f"reads: {len(node.reads_files)} files")
    if hasattr(node, 'requires_dirs') and node.requires_dirs:
        resource_info.append(f"requires: {len(node.requires_dirs)} dirs")

    if resource_info:
        info_parts.append(f"[{', '.join(resource_info)}]")

    # メタデータ
    if include_metadata and hasattr(node, 'metadata') and node.metadata:
        metadata_str = ', '.join(f"{k}={v}" for k, v in node.metadata.items())
        info_parts.append(f"metadata: {{{metadata_str}}}")

    return ' '.join(info_parts)


def format_edge_info(edge: Any) -> str:
    """エッジ情報をフォーマット（純粋関数）

    Args:
        edge: エッジオブジェクト

    Returns:
        フォーマット済みエッジ情報
    """
    from_node = getattr(edge, 'from_node', 'unknown')
    to_node = getattr(edge, 'to_node', 'unknown')
    dependency_type = getattr(edge, 'dependency_type', 'unknown')

    # 依存関係タイプの値を取得
    if hasattr(dependency_type, 'value'):
        dep_type_str = dependency_type.value
    else:
        dep_type_str = str(dependency_type)

    edge_info = f"{from_node} -> {to_node} ({dep_type_str})"

    # リソースパス
    if hasattr(edge, 'resource_path') and edge.resource_path:
        edge_info += f" [resource: {edge.resource_path}]"

    # 説明
    if hasattr(edge, 'description') and edge.description:
        edge_info += f" - {edge.description}"

    return edge_info


def format_execution_group(group_index: int, group: List[str]) -> str:
    """実行グループをフォーマット（純粋関数）

    Args:
        group_index: グループインデックス
        group: ノードIDリスト

    Returns:
        フォーマット済みグループ情報
    """
    node_list = ', '.join(group)
    return f"Group {group_index}: {node_list} ({len(group)} nodes can run in parallel)"


def create_dependency_matrix(nodes: Dict[str, Any],
                           adjacency_list: Dict[str, Set[str]]) -> List[List[str]]:
    """依存関係マトリックスを作成（純粋関数）

    Args:
        nodes: ノード辞書
        adjacency_list: 隣接リスト

    Returns:
        依存関係マトリックス（文字列の2次元リスト）
    """
    node_ids = sorted(nodes.keys())
    matrix = []

    # ヘッダー行
    header = ["", *node_ids]
    matrix.append(header)

    # 各行を作成
    for from_node in node_ids:
        row = [from_node]
        for to_node in node_ids:
            if to_node in adjacency_list.get(from_node, set()):
                row.append("✓")
            else:
                row.append("-")
        matrix.append(row)

    return matrix


def format_dependency_matrix(matrix: List[List[str]]) -> str:
    """依存関係マトリックスをフォーマット（純粋関数）

    Args:
        matrix: 依存関係マトリックス

    Returns:
        フォーマット済みマトリックス文字列
    """
    if not matrix:
        return "Empty dependency matrix"

    # 各列の最大幅を計算
    col_widths = []
    for col_idx in range(len(matrix[0])):
        max_width = max(len(str(row[col_idx])) for row in matrix)
        col_widths.append(max_width)

    # マトリックスをフォーマット
    lines = []
    for row_idx, row in enumerate(matrix):
        formatted_cells = []
        for col_idx, cell in enumerate(row):
            formatted_cell = str(cell).ljust(col_widths[col_idx])
            formatted_cells.append(formatted_cell)

        line = " | ".join(formatted_cells)
        lines.append(line)

        # ヘッダー行の後に区切り線を追加
        if row_idx == 0:
            separator = "-" * len(line)
            lines.append(separator)

    return "\n".join(lines)


def create_graph_summary(nodes: Dict[str, Any],
                        edges: List[Any],
                        execution_groups: Optional[List[List[str]]] = None) -> Dict[str, Any]:
    """グラフのサマリー情報を作成（純粋関数）

    Args:
        nodes: ノード辞書
        edges: エッジリスト
        execution_groups: 実行グループ

    Returns:
        サマリー情報辞書
    """
    summary = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'node_types': _count_node_types(nodes),
        'edge_types': _count_edge_types(edges),
    }

    if execution_groups:
        summary.update({
            'execution_groups': len(execution_groups),
            'max_parallelism': max(len(group) for group in execution_groups) if execution_groups else 0,
            'avg_parallelism': sum(len(group) for group in execution_groups) / len(execution_groups) if execution_groups else 0
        })

    return summary


def _count_node_types(nodes: Dict[str, Any]) -> Dict[str, int]:
    """ノードタイプ別カウント（純粋関数）"""
    type_counts = {}

    for node in nodes.values():
        if hasattr(node, 'request') and hasattr(node.request, 'request_type'):
            node_type = node.request.request_type.short_name
        else:
            node_type = "Unknown"

        type_counts[node_type] = type_counts.get(node_type, 0) + 1

    return type_counts


def _count_edge_types(edges: List[Any]) -> Dict[str, int]:
    """エッジタイプ別カウント（純粋関数）"""
    type_counts = {}

    for edge in edges:
        if hasattr(edge, 'dependency_type'):
            if hasattr(edge.dependency_type, 'value'):
                edge_type = edge.dependency_type.value
            else:
                edge_type = str(edge.dependency_type)
        else:
            edge_type = "unknown"

        type_counts[edge_type] = type_counts.get(edge_type, 0) + 1

    return type_counts


def generate_dot_format(nodes: Dict[str, Any], edges: List[Any]) -> str:
    """Graphviz DOT形式の文字列を生成（純粋関数）

    Args:
        nodes: ノード辞書
        edges: エッジリスト

    Returns:
        DOT形式文字列
    """
    lines = ["digraph RequestExecutionGraph {"]
    lines.append("  rankdir=LR;")
    lines.append("  node [shape=box];")
    lines.append("")

    # ノードを定義
    for node_id, node in nodes.items():
        label = _create_dot_node_label(node)
        lines.append(f'  "{node_id}" [label="{label}"];')

    lines.append("")

    # エッジを定義
    for edge in edges:
        from_node = getattr(edge, 'from_node', 'unknown')
        to_node = getattr(edge, 'to_node', 'unknown')
        label = _create_dot_edge_label(edge)
        lines.append(f'  "{from_node}" -> "{to_node}" [label="{label}"];')

    lines.append("}")
    return "\n".join(lines)


def _create_dot_node_label(node: Any) -> str:
    """DOT形式用ノードラベルを作成（純粋関数）"""
    if hasattr(node, 'request') and hasattr(node.request, 'request_type'):
        class_name = node.request.request_type.short_name
    else:
        class_name = "Unknown"

    status = getattr(node, 'status', 'unknown')
    return f"{class_name}\\n({status})"


def _create_dot_edge_label(edge: Any) -> str:
    """DOT形式用エッジラベルを作成（純粋関数）"""
    if hasattr(edge, 'dependency_type'):
        if hasattr(edge.dependency_type, 'value'):
            return edge.dependency_type.value
        return str(edge.dependency_type)
    return "unknown"
