"""グラフ構築ロジックの純粋関数 - GraphBasedWorkflowBuilderから分離"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass(frozen=True)
class GraphConstructionResult:
    """グラフ構築結果（不変データ構造）"""
    nodes: List[Any]  # RequestNodeのリスト
    dependencies: List[Any]  # DependencyEdgeのリスト
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]

    @property
    def is_success(self) -> bool:
        """構築成功判定（純粋関数）"""
        return not self.errors and len(self.nodes) > 0


@dataclass(frozen=True)
class NodeConstructionInfo:
    """ノード構築情報（不変データ構造）"""
    node_id: str
    request: Any
    creates_files: Set[str]
    creates_dirs: Set[str]
    reads_files: Set[str]
    requires_dirs: Set[str]
    metadata: Dict[str, Any]
    original_index: int


def construct_graph_from_steps(steps: List[Any], context: Optional[Any] = None) -> GraphConstructionResult:
    """ステップからグラフを構築（純粋関数）

    Args:
        steps: ステップリスト
        context: ステップコンテキスト

    Returns:
        グラフ構築結果
    """
    try:
        # ステップからノード情報を生成
        node_infos = create_nodes_from_steps(steps, context)

        # 失敗したノードがある場合はエラーを収集
        errors = []
        warnings = []
        valid_node_infos = []

        for node_info in node_infos:
            if node_info.request is None:
                errors.append(f"Failed to create request for step at index {node_info.original_index}")
            else:
                valid_node_infos.append(node_info)

        if not valid_node_infos:
            return GraphConstructionResult(
                nodes=[],
                dependencies=[],
                metadata={},
                errors=[*errors, "No valid nodes created"],
                warnings=warnings
            )

        # 依存関係を構築
        dependencies = build_node_dependencies(valid_node_infos)

        # メタデータを作成
        metadata = create_graph_metadata(valid_node_infos, dependencies)

        return GraphConstructionResult(
            nodes=valid_node_infos,
            dependencies=dependencies,
            metadata=metadata,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        return GraphConstructionResult(
            nodes=[],
            dependencies=[],
            metadata={},
            errors=[f"Graph construction failed: {e!s}"],
            warnings=[]
        )


def create_nodes_from_steps(steps: List[Any], context: Optional[Any] = None) -> List[NodeConstructionInfo]:
    """ステップからノード情報を作成（純粋関数）

    Args:
        steps: ステップリスト
        context: ステップコンテキスト

    Returns:
        ノード構築情報リスト
    """
    from .step_conversion import convert_step_to_request

    node_infos = []

    for i, step in enumerate(steps):
        # ステップを変換
        conversion_result = convert_step_to_request(step, context)

        # ノード構築情報を作成
        node_info = NodeConstructionInfo(
            node_id=f"step_{i}",
            request=conversion_result.request,
            creates_files=conversion_result.resource_info[0],
            creates_dirs=conversion_result.resource_info[1],
            reads_files=conversion_result.resource_info[2],
            requires_dirs=conversion_result.resource_info[3],
            metadata=conversion_result.metadata,
            original_index=i
        )

        node_infos.append(node_info)

    return node_infos


def build_node_dependencies(node_infos: List[NodeConstructionInfo]) -> List[Any]:
    """ノード間の依存関係を構築（純粋関数）

    Args:
        node_infos: ノード構築情報リスト

    Returns:
        依存関係エッジリスト
    """
    from .functional_utils import pipe
    from .graph_ops.cycle_detection import validate_no_circular_dependencies
    from .graph_ops.dependency_mapping import build_dependency_mapping
    from .graph_ops.graph_optimization import optimize_dependency_order
    from .graph_ops.metadata_extraction import extract_request_metadata

    # ノード情報をRequestMetadata形式に変換
    metadata_list = []
    for node_info in node_infos:
        # RequestMetadata互換のダミーオブジェクトを作成
        dummy_node = type('DummyNode', (), {
            'id': node_info.node_id,
            'creates_files': node_info.creates_files,
            'creates_dirs': node_info.creates_dirs,
            'reads_files': node_info.reads_files,
            'requires_dirs': node_info.requires_dirs
        })()
        metadata_list.append(dummy_node)

    # 関数型パイプライン
    try:
        result = pipe(
            metadata_list,
            extract_request_metadata,           # 純粋関数
            build_dependency_mapping,           # 純粋関数
            validate_no_circular_dependencies,  # 純粋関数
            optimize_dependency_order           # 純粋関数
        )

        # 結果からエッジリストを作成
        if hasattr(result, 'mappings'):
            # DependencyGraphオブジェクトの場合
            return _convert_mappings_to_edges(result.mappings)
        if 'mappings' in result:
            # 辞書形式の場合
            return _convert_mapping_dicts_to_edges(result['mappings'])
        return []

    except Exception:
        # フォールバック: 順序依存のみ作成
        return _create_sequential_dependencies(node_infos)


def _convert_mappings_to_edges(mappings: List[Any]) -> List[Any]:
    """DependencyMappingからDependencyEdgeに変換（純粋関数）"""
    from .request_execution_graph import DependencyEdge

    edges = []
    for mapping in mappings:
        edge = DependencyEdge(
            from_node=mapping.from_node_id,
            to_node=mapping.to_node_id,
            dependency_type=mapping.dependency_type,
            resource_path=mapping.resource_path,
            description=mapping.description
        )
        edges.append(edge)

    return edges


def _convert_mapping_dicts_to_edges(mapping_dicts: List[Dict[str, Any]]) -> List[Any]:
    """マッピング辞書からDependencyEdgeに変換（純粋関数）"""
    from .request_execution_graph import DependencyEdge, DependencyType

    edges = []
    for mapping_dict in mapping_dicts:
        edge = DependencyEdge(
            from_node=mapping_dict['from_node'],
            to_node=mapping_dict['to_node'],
            dependency_type=DependencyType(mapping_dict['type']),
            resource_path=mapping_dict.get('resource', ''),
            description=mapping_dict.get('description', '')
        )
        edges.append(edge)

    return edges


def _create_sequential_dependencies(node_infos: List[NodeConstructionInfo]) -> List[Any]:
    """順次実行依存関係を作成（フォールバック）"""
    from .request_execution_graph import DependencyEdge, DependencyType

    edges = []

    for i in range(len(node_infos) - 1):
        current_node = node_infos[i]
        next_node = node_infos[i + 1]

        # リソース競合がある場合のみ依存関係を追加
        if _has_resource_conflict_between_nodes(current_node, next_node):
            edge = DependencyEdge(
                from_node=current_node.node_id,
                to_node=next_node.node_id,
                dependency_type=DependencyType.EXECUTION_ORDER,
                description="Sequential execution order due to resource conflict"
            )
            edges.append(edge)

    return edges


def _has_resource_conflict_between_nodes(node1: NodeConstructionInfo,
                                       node2: NodeConstructionInfo) -> bool:
    """2つのノード間でリソース競合があるかチェック（純粋関数）"""
    # 同じファイル/ディレクトリの作成競合
    creation_conflict = bool(
        (node1.creates_files & node2.creates_files) |
        (node1.creates_dirs & node2.creates_dirs)
    )

    # 作成と読み取りの競合
    read_write_conflict = bool(
        (node1.creates_files & node2.reads_files) |
        (node1.reads_files & node2.creates_files) |
        (node1.creates_dirs & node2.requires_dirs) |
        (node1.requires_dirs & node2.creates_dirs)
    )

    return creation_conflict or read_write_conflict


def create_graph_metadata(node_infos: List[NodeConstructionInfo],
                         dependencies: List[Any]) -> Dict[str, Any]:
    """グラフメタデータを作成（純粋関数）

    Args:
        node_infos: ノード構築情報リスト
        dependencies: 依存関係リスト

    Returns:
        グラフメタデータ辞書
    """
    # ノードタイプ別統計
    node_types = {}
    for node_info in node_infos:
        if node_info.request is not None:
            node_type = type(node_info.request).__name__
            node_types[node_type] = node_types.get(node_type, 0) + 1

    # 依存関係タイプ別統計
    dependency_types = {}
    for dep in dependencies:
        if hasattr(dep, 'dependency_type'):
            dep_type = getattr(dep.dependency_type, 'value', str(dep.dependency_type))
            dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1

    # リソース統計
    total_creates_files = set()
    total_creates_dirs = set()
    total_reads_files = set()
    total_requires_dirs = set()

    for node_info in node_infos:
        total_creates_files.update(node_info.creates_files)
        total_creates_dirs.update(node_info.creates_dirs)
        total_reads_files.update(node_info.reads_files)
        total_requires_dirs.update(node_info.requires_dirs)

    return {
        'total_nodes': len(node_infos),
        'total_dependencies': len(dependencies),
        'node_types': node_types,
        'dependency_types': dependency_types,
        'resource_stats': {
            'creates_files': len(total_creates_files),
            'creates_dirs': len(total_creates_dirs),
            'reads_files': len(total_reads_files),
            'requires_dirs': len(total_requires_dirs)
        },
        'complexity_score': _calculate_graph_complexity(node_infos, dependencies)
    }


def _calculate_graph_complexity(node_infos: List[NodeConstructionInfo],
                              dependencies: List[Any]) -> float:
    """グラフの複雑度スコアを計算（純粋関数）"""
    if not node_infos:
        return 0.0

    # 基本スコア: ノード数とエッジ数の比率
    base_score = len(dependencies) / len(node_infos) if node_infos else 0

    # リソース複雑度: ユニークリソース数
    unique_resources = set()
    for node_info in node_infos:
        unique_resources.update(node_info.creates_files)
        unique_resources.update(node_info.creates_dirs)
        unique_resources.update(node_info.reads_files)
        unique_resources.update(node_info.requires_dirs)

    resource_score = len(unique_resources) / len(node_infos) if node_infos else 0

    # 総合複雑度スコア
    complexity_score = (base_score + resource_score) / 2

    return round(complexity_score, 2)


def apply_node_dependencies(graph: Any, dependencies: List[Any]) -> None:
    """ノード依存関係をグラフに適用（副作用を含む）

    Args:
        graph: RequestExecutionGraph
        dependencies: 依存関係エッジリスト
    """
    for dependency in dependencies:
        graph.add_dependency(dependency)


def validate_graph_construction(result: GraphConstructionResult) -> List[str]:
    """グラフ構築結果を検証（純粋関数）

    Args:
        result: グラフ構築結果

    Returns:
        検証エラーリスト
    """
    validation_errors = []

    # 基本的な妥当性チェック
    if not result.nodes:
        validation_errors.append("No nodes in constructed graph")

    # ノードの妥当性チェック
    node_ids = set()
    for node in result.nodes:
        if hasattr(node, 'node_id'):
            node_id = node.node_id
        else:
            validation_errors.append("Node missing node_id")
            continue

        if node_id in node_ids:
            validation_errors.append(f"Duplicate node_id: {node_id}")
        node_ids.add(node_id)

        if hasattr(node, 'request') and node.request is None:
            validation_errors.append(f"Node {node_id} has None request")

    # 依存関係の妥当性チェック
    for dep in result.dependencies:
        if hasattr(dep, 'from_node') and hasattr(dep, 'to_node'):
            from_node = dep.from_node
            to_node = dep.to_node

            if from_node not in node_ids:
                validation_errors.append(f"Dependency references unknown from_node: {from_node}")

            if to_node not in node_ids:
                validation_errors.append(f"Dependency references unknown to_node: {to_node}")

            if from_node == to_node:
                validation_errors.append(f"Self-dependency detected: {from_node}")
        else:
            validation_errors.append("Dependency missing from_node or to_node")

    return validation_errors


def optimize_graph_structure(result: GraphConstructionResult) -> GraphConstructionResult:
    """グラフ構造を最適化（純粋関数）

    Args:
        result: 元のグラフ構築結果

    Returns:
        最適化されたグラフ構築結果
    """
    if not result.is_success:
        return result

    # 最適化処理（現在は基本的な処理のみ）
    optimized_dependencies = _remove_redundant_dependencies(result.dependencies)

    # メタデータを更新
    optimized_metadata = result.metadata.copy()
    optimized_metadata['optimized'] = True
    optimized_metadata['original_dependencies'] = len(result.dependencies)
    optimized_metadata['optimized_dependencies'] = len(optimized_dependencies)

    return GraphConstructionResult(
        nodes=result.nodes,
        dependencies=optimized_dependencies,
        metadata=optimized_metadata,
        errors=result.errors,
        warnings=result.warnings
    )


def _remove_redundant_dependencies(dependencies: List[Any]) -> List[Any]:
    """冗長な依存関係を除去（純粋関数）"""
    # 重複する依存関係を除去
    seen_edges = set()
    unique_dependencies = []

    for dep in dependencies:
        if hasattr(dep, 'from_node') and hasattr(dep, 'to_node'):
            edge_key = (dep.from_node, dep.to_node)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_dependencies.append(dep)

    return unique_dependencies
