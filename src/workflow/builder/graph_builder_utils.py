"""グラフベースワークフロービルダーの純粋関数実装
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.workflow.step.step import Step, StepContext, StepType

# Note: request_builder_pure removed - using direct implementation


@dataclass(frozen=True)
class NodeInfo:
    """ノード情報の不変データクラス"""
    id: str
    step: Step
    creates_files: set[str]
    creates_dirs: set[str]
    reads_files: set[str]
    requires_dirs: set[str]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DependencyInfo:
    """依存関係情報の不変データクラス"""
    from_node_id: str
    to_node_id: str
    dependency_type: str
    resource_path: str
    description: str


@dataclass(frozen=True)
class GraphBuildResult:
    """グラフ構築結果の不変データクラス"""
    nodes: list[NodeInfo]
    dependencies: list[DependencyInfo]
    errors: list[str]
    warnings: list[str]


# extract_node_resource_info関数は resource_analysis モジュールに移動されました
from .resource_analysis.step_resource_extractor import extract_node_resource_info
from .resource_analysis.resource_mapper import build_resource_mappings
from .resource_analysis.dependency_detector import (
    detect_file_creation_dependencies,
    detect_directory_creation_dependencies,
    detect_parent_directory_dependencies
)


def build_node_info_list(steps: list[Step], context: Optional[StepContext] = None) -> list[NodeInfo]:
    """ステップリストからノード情報リストを構築する純粋関数

    Args:
        steps: ステップのリスト
        context: ステップコンテキスト（オプション）

    Returns:
        ノード情報のリスト
    """
    node_infos = []

    for i, step in enumerate(steps):
        # リソース情報を抽出
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info(step)

        # メタデータを作成
        metadata = {
            'step_type': step.type.value,
            'step_cmd': step.cmd,
            'original_index': i
        }

        node_info = NodeInfo(
            id=f"step_{i}",
            step=step,
            creates_files=creates_files,
            creates_dirs=creates_dirs,
            reads_files=reads_files,
            requires_dirs=requires_dirs,
            metadata=metadata
        )

        node_infos.append(node_info)

    return node_infos


def analyze_node_dependencies(node_infos: list[NodeInfo]) -> list[DependencyInfo]:
    """ノード間の依存関係を分析する純粋関数

    Args:
        node_infos: ノード情報のリスト

    Returns:
        依存関係情報のリスト
    """
    # リソースマッピングを構築
    resource_mappings = build_resource_mappings(node_infos)
    
    # 各種依存関係を検出
    dependencies = []
    dependencies.extend(detect_file_creation_dependencies(resource_mappings))
    dependencies.extend(detect_directory_creation_dependencies(resource_mappings))
    dependencies.extend(detect_parent_directory_dependencies(node_infos, resource_mappings))
    dependencies.extend(detect_execution_order_dependencies(node_infos, dependencies))
    
    return dependencies


# build_resource_mappings関数は resource_analysis.resource_mapper モジュールに移動されました


# detect_file_creation_dependencies と detect_directory_creation_dependencies は
# resource_analysis.dependency_detector モジュールに移動されました


# detect_parent_directory_dependencies関数は resource_analysis.dependency_detector モジュールに移動されました


def detect_execution_order_dependencies(node_infos: list[NodeInfo], 
                                       existing_dependencies: list[DependencyInfo]) -> list[DependencyInfo]:
    """実行順序依存関係を検出する純粋関数
    
    Args:
        node_infos: ノード情報のリスト
        existing_dependencies: 既存の依存関係リスト
        
    Returns:
        実行順序依存関係のリスト
    """
    dependencies = []
    
    for i in range(len(node_infos) - 1):
        from_node = node_infos[i]
        to_node = node_infos[i + 1]

        # すでに依存関係がある場合はスキップ
        existing_deps = [d for d in existing_dependencies
                        if (d.from_node_id == from_node.id and d.to_node_id == to_node.id) or
                           (d.from_node_id == to_node.id and d.to_node_id == from_node.id)]
        if existing_deps:
            continue

        # リソースの競合がある場合のみ順序依存を追加
        if has_resource_conflict(from_node, to_node):
            dependency = DependencyInfo(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                dependency_type="EXECUTION_ORDER",
                resource_path="",
                description="Preserve original execution order due to resource conflict"
            )
            dependencies.append(dependency)
    
    return dependencies


def is_parent_directory(parent_path: str, child_path: str) -> bool:
    """parent_pathがchild_pathの親ディレクトリかどうかを判定する純粋関数

    Args:
        parent_path: 親ディレクトリパス
        child_path: 子ディレクトリパス

    Returns:
        親ディレクトリの場合True
    """
    try:
        parent = Path(parent_path).resolve()
        child = Path(child_path).resolve()
        return parent in child.parents
    except Exception:
        # パスの解決に失敗した場合は文字列で判定
        return child_path.startswith(parent_path + '/')


def has_resource_conflict(node1: NodeInfo, node2: NodeInfo) -> bool:
    """2つのノード間でリソースの競合があるかどうかを判定する純粋関数

    Args:
        node1: 最初のノード
        node2: 2番目のノード

    Returns:
        競合がある場合True
    """
    # 同じファイルへの書き込み
    if node1.creates_files & node2.creates_files:
        return True

    # 同じディレクトリの作成
    if node1.creates_dirs & node2.creates_dirs:
        return True

    # 一方が作成し、他方が削除するファイル
    return bool(node1.creates_files & node2.reads_files or node2.creates_files & node1.reads_files)


def build_execution_graph(steps: list[Step], context: Optional[StepContext] = None) -> GraphBuildResult:
    """ステップリストから実行グラフを構築する純粋関数

    Args:
        steps: ステップのリスト
        context: ステップコンテキスト（オプション）

    Returns:
        グラフ構築結果
    """
    errors = []
    warnings = []

    # 基本的なバリデーション
    if not steps:
        errors.append("No steps provided for graph building")
        return GraphBuildResult([], [], errors, warnings)

    # ノード情報を構築
    node_infos = build_node_info_list(steps, context)

    # 依存関係を分析
    dependencies = analyze_node_dependencies(node_infos)

    # バリデーション
    validation_errors = validate_graph_structure(node_infos, dependencies)
    errors.extend(validation_errors)

    return GraphBuildResult(
        nodes=node_infos,
        dependencies=dependencies,
        errors=errors,
        warnings=warnings
    )


def validate_graph_structure(nodes: list[NodeInfo], dependencies: list[DependencyInfo]) -> list[str]:
    """グラフ構造の妥当性を検証する純粋関数

    Args:
        nodes: ノード情報のリスト
        dependencies: 依存関係情報のリスト

    Returns:
        エラーメッセージのリスト
    """
    errors = []

    # ノードIDの重複チェック
    node_ids = [node.id for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append("Duplicate node IDs found in graph")

    # 依存関係の妥当性チェック
    node_id_set = set(node_ids)
    for dep in dependencies:
        if dep.from_node_id not in node_id_set:
            errors.append(f"Dependency references unknown from_node: {dep.from_node_id}")
        if dep.to_node_id not in node_id_set:
            errors.append(f"Dependency references unknown to_node: {dep.to_node_id}")

    # 循環依存の簡易チェック（完全な検出は複雑なので基本のみ）
    direct_cycles = []
    for dep in dependencies:
        reverse_dep = next((d for d in dependencies
                           if d.from_node_id == dep.to_node_id and d.to_node_id == dep.from_node_id), None)
        if reverse_dep:
            cycle = f"{dep.from_node_id} <-> {dep.to_node_id}"
            if cycle not in direct_cycles:
                direct_cycles.append(cycle)

    if direct_cycles:
        errors.append(f"Direct circular dependencies detected: {direct_cycles}")

    return errors


def calculate_graph_metrics(result: GraphBuildResult) -> dict[str, Any]:
    """グラフ構築結果のメトリクスを計算する純粋関数

    Args:
        result: グラフ構築結果

    Returns:
        メトリクス辞書
    """
    node_count = len(result.nodes)
    dependency_count = len(result.dependencies)
    error_count = len(result.errors)
    warning_count = len(result.warnings)

    # ステップタイプ別の統計
    step_types = {}
    for node in result.nodes:
        step_type = node.step.type.value
        step_types[step_type] = step_types.get(step_type, 0) + 1

    # 依存関係タイプ別の統計
    dependency_types = {}
    for dep in result.dependencies:
        dep_type = dep.dependency_type
        dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1

    # リソース統計
    total_files_created = sum(len(node.creates_files) for node in result.nodes)
    total_dirs_created = sum(len(node.creates_dirs) for node in result.nodes)
    total_files_read = sum(len(node.reads_files) for node in result.nodes)

    return {
        "node_count": node_count,
        "dependency_count": dependency_count,
        "error_count": error_count,
        "warning_count": warning_count,
        "success_rate": (node_count - error_count) / node_count if node_count > 0 else 0,
        "step_types": step_types,
        "dependency_types": dependency_types,
        "total_files_created": total_files_created,
        "total_dirs_created": total_dirs_created,
        "total_files_read": total_files_read,
        "complexity_score": dependency_count / node_count if node_count > 0 else 0
    }


