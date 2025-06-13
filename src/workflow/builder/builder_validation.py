"""ビルダー検証機能の純粋関数 - GraphBasedWorkflowBuilderから分離"""
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """検証結果（不変データ構造）"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    statistics: Dict[str, Any]
    
    @classmethod
    def success(cls, warnings: List[str] = None, suggestions: List[str] = None, 
               statistics: Dict[str, Any] = None) -> 'ValidationResult':
        """成功結果を作成（純粋関数）"""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )
    
    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] = None, 
               suggestions: List[str] = None, statistics: Dict[str, Any] = None) -> 'ValidationResult':
        """失敗結果を作成（純粋関数）"""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )


def validate_graph_structure(nodes: Dict[str, Any], edges: List[Any]) -> ValidationResult:
    """グラフ構造の妥当性を検証（純粋関数）
    
    Args:
        nodes: ノード辞書
        edges: エッジリスト
        
    Returns:
        検証結果
    """
    errors = []
    warnings = []
    suggestions = []
    
    # 基本的な構造チェック
    if not nodes:
        errors.append("Graph has no nodes")
        return ValidationResult.failure(errors)
    
    # ノードの妥当性チェック
    node_errors = _validate_nodes(nodes)
    errors.extend(node_errors)
    
    # エッジの妥当性チェック
    edge_errors, edge_warnings = _validate_edges(edges, set(nodes.keys()))
    errors.extend(edge_errors)
    warnings.extend(edge_warnings)
    
    # 構造的な問題のチェック
    structure_warnings, structure_suggestions = _check_structural_issues(nodes, edges)
    warnings.extend(structure_warnings)
    suggestions.extend(structure_suggestions)
    
    # 統計情報を計算
    statistics = _calculate_validation_statistics(nodes, edges)
    
    if errors:
        return ValidationResult.failure(errors, warnings, suggestions, statistics)
    else:
        return ValidationResult.success(warnings, suggestions, statistics)


def _validate_nodes(nodes: Dict[str, Any]) -> List[str]:
    """ノードの妥当性をチェック（純粋関数）"""
    errors = []
    
    for node_id, node in nodes.items():
        # ノードIDの妥当性
        if not node_id or not isinstance(node_id, str):
            errors.append(f"Invalid node ID: {node_id}")
        
        # ノードオブジェクトの妥当性
        if node is None:
            errors.append(f"Node {node_id} is None")
            continue
        
        # リクエストの存在チェック
        if hasattr(node, 'request') and node.request is None:
            errors.append(f"Node {node_id} has None request")
        
        # ステータスの妥当性
        if hasattr(node, 'status'):
            valid_statuses = {"pending", "running", "completed", "failed", "skipped"}
            if node.status not in valid_statuses:
                errors.append(f"Node {node_id} has invalid status: {node.status}")
    
    return errors


def _validate_edges(edges: List[Any], valid_node_ids: Set[str]) -> Tuple[List[str], List[str]]:
    """エッジの妥当性をチェック（純粋関数）"""
    errors = []
    warnings = []
    
    seen_edges = set()
    
    for i, edge in enumerate(edges):
        # エッジオブジェクトの妥当性
        if edge is None:
            errors.append(f"Edge at index {i} is None")
            continue
        
        # from_nodeとto_nodeの存在チェック
        if not hasattr(edge, 'from_node') or not hasattr(edge, 'to_node'):
            errors.append(f"Edge at index {i} missing from_node or to_node")
            continue
        
        from_node = edge.from_node
        to_node = edge.to_node
        
        # ノード参照の妥当性
        if from_node not in valid_node_ids:
            errors.append(f"Edge references invalid from_node: {from_node}")
        
        if to_node not in valid_node_ids:
            errors.append(f"Edge references invalid to_node: {to_node}")
        
        # 自己依存のチェック
        if from_node == to_node:
            errors.append(f"Self-dependency detected: {from_node} -> {to_node}")
        
        # 重複エッジのチェック
        edge_key = (from_node, to_node)
        if edge_key in seen_edges:
            warnings.append(f"Duplicate edge detected: {from_node} -> {to_node}")
        seen_edges.add(edge_key)
        
        # 依存関係タイプの妥当性
        if hasattr(edge, 'dependency_type'):
            if not _is_valid_dependency_type(edge.dependency_type):
                warnings.append(f"Unknown dependency type in edge {from_node} -> {to_node}")
    
    return errors, warnings


def _is_valid_dependency_type(dependency_type: Any) -> bool:
    """依存関係タイプの妥当性をチェック（純粋関数）"""
    # DependencyTypeの有効な値をチェック
    valid_types = {"file_creation", "dir_creation", "resource_access", "exec_order"}
    
    if hasattr(dependency_type, 'value'):
        return dependency_type.value in valid_types
    else:
        return str(dependency_type) in valid_types


def _check_structural_issues(nodes: Dict[str, Any], edges: List[Any]) -> Tuple[List[str], List[str]]:
    """構造的な問題をチェック（純粋関数）"""
    warnings = []
    suggestions = []
    
    # 隣接リストを構築
    adjacency_list = {}
    reverse_adjacency_list = {}
    
    for node_id in nodes:
        adjacency_list[node_id] = set()
        reverse_adjacency_list[node_id] = set()
    
    for edge in edges:
        if hasattr(edge, 'from_node') and hasattr(edge, 'to_node'):
            from_node = edge.from_node
            to_node = edge.to_node
            
            if from_node in adjacency_list and to_node in reverse_adjacency_list:
                adjacency_list[from_node].add(to_node)
                reverse_adjacency_list[to_node].add(from_node)
    
    # 孤立ノードのチェック
    isolated_nodes = []
    for node_id in nodes:
        has_incoming = bool(reverse_adjacency_list[node_id])
        has_outgoing = bool(adjacency_list[node_id])
        
        if not has_incoming and not has_outgoing:
            isolated_nodes.append(node_id)
    
    if isolated_nodes:
        warnings.append(f"Isolated nodes detected: {isolated_nodes}")
        suggestions.append("Consider connecting isolated nodes or removing them")
    
    # 終端ノードのチェック
    sink_nodes = [node_id for node_id in nodes if not adjacency_list[node_id]]
    if len(sink_nodes) > 3:
        warnings.append(f"Many sink nodes detected ({len(sink_nodes)})")
        suggestions.append("Consider consolidating final steps")
    
    # 開始ノードのチェック
    source_nodes = [node_id for node_id in nodes if not reverse_adjacency_list[node_id]]
    if len(source_nodes) > 5:
        warnings.append(f"Many source nodes detected ({len(source_nodes)})")
        suggestions.append("Consider consolidating initial steps")
    
    return warnings, suggestions


def _calculate_validation_statistics(nodes: Dict[str, Any], edges: List[Any]) -> Dict[str, Any]:
    """検証統計を計算（純粋関数）"""
    # 基本統計
    stats = {
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'density': len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
    }
    
    # ノードタイプ別統計
    node_types = {}
    for node in nodes.values():
        if hasattr(node, 'request') and node.request is not None:
            node_type = type(node.request).__name__
            node_types[node_type] = node_types.get(node_type, 0) + 1
    stats['node_types'] = node_types
    
    # エッジタイプ別統計
    edge_types = {}
    for edge in edges:
        if hasattr(edge, 'dependency_type'):
            edge_type = getattr(edge.dependency_type, 'value', str(edge.dependency_type))
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    stats['edge_types'] = edge_types
    
    return stats


def check_graph_connectivity(adjacency_list: Dict[str, Set[str]]) -> ValidationResult:
    """グラフの連結性をチェック（純粋関数）
    
    Args:
        adjacency_list: 隣接リスト
        
    Returns:
        検証結果
    """
    if not adjacency_list:
        return ValidationResult.failure(["Empty adjacency list"])
    
    errors = []
    warnings = []
    suggestions = []
    
    # 弱連結性をチェック（無向グラフとして扱った場合）
    undirected_adj = _create_undirected_adjacency(adjacency_list)
    components = _find_connected_components(undirected_adj)
    
    if len(components) > 1:
        warnings.append(f"Graph has {len(components)} disconnected components")
        suggestions.append("Consider adding connections between components")
    
    # 各コンポーネントのサイズをチェック
    component_sizes = [len(comp) for comp in components]
    max_component_size = max(component_sizes) if component_sizes else 0
    min_component_size = min(component_sizes) if component_sizes else 0
    
    if max_component_size > len(adjacency_list) * 0.8:
        suggestions.append("Large connected component detected - consider splitting")
    
    if min_component_size == 1:
        isolated_count = component_sizes.count(1)
        warnings.append(f"{isolated_count} isolated nodes detected")
    
    statistics = {
        'connected_components': len(components),
        'largest_component_size': max_component_size,
        'smallest_component_size': min_component_size,
        'connectivity_ratio': max_component_size / len(adjacency_list) if adjacency_list else 0
    }
    
    if errors:
        return ValidationResult.failure(errors, warnings, suggestions, statistics)
    else:
        return ValidationResult.success(warnings, suggestions, statistics)


def _create_undirected_adjacency(directed_adj: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """有向隣接リストから無向隣接リストを作成（純粋関数）"""
    undirected = {}
    
    for node in directed_adj:
        undirected[node] = set()
    
    for from_node, to_nodes in directed_adj.items():
        for to_node in to_nodes:
            if to_node in undirected:
                undirected[from_node].add(to_node)
                undirected[to_node].add(from_node)
    
    return undirected


def _find_connected_components(adjacency_list: Dict[str, Set[str]]) -> List[Set[str]]:
    """連結成分を探索（純粋関数）"""
    visited = set()
    components = []
    
    for node in adjacency_list:
        if node not in visited:
            component = _dfs_component(node, adjacency_list, visited)
            components.append(component)
    
    return components


def _dfs_component(start_node: str, adjacency_list: Dict[str, Set[str]], 
                  visited: Set[str]) -> Set[str]:
    """DFSで連結成分を探索（純粋関数）"""
    component = set()
    stack = [start_node]
    
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        
        visited.add(node)
        component.add(node)
        
        neighbors = adjacency_list.get(node, set())
        stack.extend(neighbors - visited)
    
    return component


def validate_execution_feasibility(graph: Any) -> ValidationResult:
    """実行可能性を検証（純粋関数）
    
    Args:
        graph: RequestExecutionGraph
        
    Returns:
        検証結果
    """
    errors = []
    warnings = []
    suggestions = []
    
    try:
        # 循環依存のチェック
        cycles = graph.detect_cycles() if hasattr(graph, 'detect_cycles') else []
        if cycles:
            errors.append(f"Circular dependencies detected: {cycles}")
            suggestions.append("Remove circular dependencies to enable execution")
        
        # 実行順序の計算可能性
        try:
            execution_order = graph.get_execution_order() if hasattr(graph, 'get_execution_order') else []
            if not execution_order:
                warnings.append("Cannot determine execution order")
            else:
                suggestions.append(f"Execution order determined with {len(execution_order)} steps")
        except Exception as e:
            errors.append(f"Cannot determine execution order: {str(e)}")
        
        # 並列実行グループの計算可能性
        try:
            parallel_groups = graph.get_parallel_groups() if hasattr(graph, 'get_parallel_groups') else []
            max_parallelism = max(len(group) for group in parallel_groups) if parallel_groups else 0
            
            if max_parallelism == 1:
                warnings.append("No parallelism possible - all steps must run sequentially")
                suggestions.append("Consider reducing dependencies to enable parallelism")
            else:
                suggestions.append(f"Maximum parallelism: {max_parallelism} concurrent steps")
        except Exception as e:
            warnings.append(f"Cannot determine parallel execution groups: {str(e)}")
        
        statistics = {
            'has_cycles': len(cycles) > 0,
            'cycle_count': len(cycles),
            'max_parallelism': max_parallelism if 'max_parallelism' in locals() else 0,
            'execution_groups': len(parallel_groups) if 'parallel_groups' in locals() else 0
        }
        
    except Exception as e:
        errors.append(f"Validation failed with exception: {str(e)}")
        statistics = {}
    
    if errors:
        return ValidationResult.failure(errors, warnings, suggestions, statistics)
    else:
        return ValidationResult.success(warnings, suggestions, statistics)


def create_validation_report(validation_results: List[ValidationResult]) -> str:
    """検証結果レポートを作成（純粋関数）
    
    Args:
        validation_results: 検証結果リスト
        
    Returns:
        検証レポート文字列
    """
    lines = ["Graph Validation Report:", ""]
    
    # 全体サマリー
    total_validations = len(validation_results)
    successful_validations = sum(1 for r in validation_results if r.is_valid)
    
    lines.append(f"Total validations: {total_validations}")
    lines.append(f"Successful: {successful_validations}")
    lines.append(f"Failed: {total_validations - successful_validations}")
    lines.append("")
    
    # 各検証結果の詳細
    for i, result in enumerate(validation_results):
        lines.append(f"Validation {i + 1}: {'PASS' if result.is_valid else 'FAIL'}")
        
        if result.errors:
            lines.append("  Errors:")
            for error in result.errors:
                lines.append(f"    - {error}")
        
        if result.warnings:
            lines.append("  Warnings:")
            for warning in result.warnings:
                lines.append(f"    - {warning}")
        
        if result.suggestions:
            lines.append("  Suggestions:")
            for suggestion in result.suggestions:
                lines.append(f"    - {suggestion}")
        
        lines.append("")
    
    return "\n".join(lines)