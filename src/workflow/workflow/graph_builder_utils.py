"""
グラフベースワークフロービルダーの純粋関数実装
"""
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple, Any
from pathlib import Path
from src.workflow.step.step import Step, StepType, StepContext
from src.workflow.workflow.request_execution_graph import RequestExecutionGraph, RequestNode, DependencyEdge, DependencyType
# Note: request_builder_pure removed - using direct implementation


@dataclass(frozen=True)
class NodeInfo:
    """ノード情報の不変データクラス"""
    id: str
    step: Step
    creates_files: Set[str]
    creates_dirs: Set[str]
    reads_files: Set[str]
    requires_dirs: Set[str]
    metadata: Dict[str, Any]


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
    nodes: List[NodeInfo]
    dependencies: List[DependencyInfo]
    errors: List[str]
    warnings: List[str]


def extract_node_resource_info_pure(step: Step) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """
    ステップからリソース情報を抽出する純粋関数
    
    Args:
        step: 分析対象のステップ
        
    Returns:
        Tuple[creates_files, creates_dirs, reads_files, requires_dirs]
    """
    creates_files = set()
    creates_dirs = set()
    reads_files = set()
    requires_dirs = set()
    
    if step.type == StepType.MKDIR:
        if step.cmd:
            creates_dirs.add(step.cmd[0])
    
    elif step.type == StepType.TOUCH:
        if step.cmd:
            file_path = step.cmd[0]
            creates_files.add(file_path)
            # 親ディレクトリが必要
            parent = str(Path(file_path).parent)
            if parent != '.':
                requires_dirs.add(parent)
    
    elif step.type in [StepType.COPY, StepType.MOVE]:
        if len(step.cmd) >= 2:
            source_path = step.cmd[0]
            dest_path = step.cmd[1]
            
            reads_files.add(source_path)
            creates_files.add(dest_path)
            
            # 宛先の親ディレクトリが必要
            dest_parent = str(Path(dest_path).parent)
            if dest_parent != '.':
                requires_dirs.add(dest_parent)
    
    elif step.type == StepType.MOVETREE:
        if len(step.cmd) >= 2:
            source_dir = step.cmd[0]
            dest_dir = step.cmd[1]
            
            reads_files.add(source_dir)  # ソースディレクトリ
            creates_dirs.add(dest_dir)   # 宛先ディレクトリ
    
    elif step.type in [StepType.REMOVE, StepType.RMTREE]:
        if step.cmd:
            target_path = step.cmd[0]
            reads_files.add(target_path)  # 削除対象
    
    elif step.type == StepType.BUILD:
        # ビルドコマンドは特定のディレクトリで実行される可能性
        if step.cmd and step.cmd[0]:
            requires_dirs.add(step.cmd[0])
        else:
            requires_dirs.add("./workspace")
    
    elif step.type == StepType.TEST:
        # TESTステップは実行対象ファイルを読み取る
        if len(step.cmd) >= 2:
            target_file = step.cmd[1]
            reads_files.add(target_file)
            # 実行ファイルの親ディレクトリも必要
            parent = str(Path(target_file).parent)
            if parent != '.':
                requires_dirs.add(parent)
    
    elif step.type in [StepType.PYTHON, StepType.SHELL]:
        # 基本的なワークスペースディレクトリを要求
        requires_dirs.add("./workspace")
    
    elif step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
        # Dockerコマンドは基本的にワークスペースを使用
        requires_dirs.add("./workspace")
    
    return creates_files, creates_dirs, reads_files, requires_dirs


def build_node_info_list_pure(steps: List[Step], context: Optional[StepContext] = None) -> List[NodeInfo]:
    """
    ステップリストからノード情報リストを構築する純粋関数
    
    Args:
        steps: ステップのリスト
        context: ステップコンテキスト（オプション）
        
    Returns:
        ノード情報のリスト
    """
    node_infos = []
    
    for i, step in enumerate(steps):
        # リソース情報を抽出
        creates_files, creates_dirs, reads_files, requires_dirs = extract_node_resource_info_pure(step)
        
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


def analyze_node_dependencies_pure(node_infos: List[NodeInfo]) -> List[DependencyInfo]:
    """
    ノード間の依存関係を分析する純粋関数
    
    Args:
        node_infos: ノード情報のリスト
        
    Returns:
        依存関係情報のリスト
    """
    dependencies = []
    
    # インデックスによる効率的な検索用マッピング
    file_creators = {}  # file_path -> [(index, node_info)]
    dir_creators = {}   # dir_path -> [(index, node_info)]
    file_readers = {}   # file_path -> [(index, node_info)]
    dir_requirers = {}  # dir_path -> [(index, node_info)]
    
    for idx, node_info in enumerate(node_infos):
        for file_path in node_info.creates_files:
            if file_path not in file_creators:
                file_creators[file_path] = []
            file_creators[file_path].append((idx, node_info))
        
        for dir_path in node_info.creates_dirs:
            if dir_path not in dir_creators:
                dir_creators[dir_path] = []
            dir_creators[dir_path].append((idx, node_info))
        
        for file_path in node_info.reads_files:
            if file_path not in file_readers:
                file_readers[file_path] = []
            file_readers[file_path].append((idx, node_info))
        
        for dir_path in node_info.requires_dirs:
            if dir_path not in dir_requirers:
                dir_requirers[dir_path] = []
            dir_requirers[dir_path].append((idx, node_info))
    
    # ファイル作成依存を検出
    for file_path, creators in file_creators.items():
        if file_path in file_readers:
            for creator_idx, creator_info in creators:
                for reader_idx, reader_info in file_readers[file_path]:
                    if creator_idx < reader_idx:  # 順序を保持
                        dependency = DependencyInfo(
                            from_node_id=creator_info.id,
                            to_node_id=reader_info.id,
                            dependency_type="FILE_CREATION",
                            resource_path=file_path,
                            description=f"File {file_path} must be created before being read"
                        )
                        dependencies.append(dependency)
    
    # ディレクトリ作成依存を検出
    for dir_path, creators in dir_creators.items():
        if dir_path in dir_requirers:
            for creator_idx, creator_info in creators:
                for requirer_idx, requirer_info in dir_requirers[dir_path]:
                    if creator_idx < requirer_idx:
                        dependency = DependencyInfo(
                            from_node_id=creator_info.id,
                            to_node_id=requirer_info.id,
                            dependency_type="DIRECTORY_CREATION",
                            resource_path=dir_path,
                            description=f"Directory {dir_path} must be created before being used"
                        )
                        dependencies.append(dependency)
    
    # ディレクトリ内のファイル作成依存
    for idx, node_info in enumerate(node_infos):
        if node_info.creates_files:
            # このノードが作成するファイルの親ディレクトリを収集
            parent_dirs = set()
            for file_path in node_info.creates_files:
                parent = str(Path(file_path).parent)
                if parent != '.':
                    parent_dirs.add(parent)
            
            # 必要な親ディレクトリを作成するノードを検索
            for parent_dir in parent_dirs:
                for check_dir, creators in dir_creators.items():
                    if is_parent_directory_pure(check_dir, parent_dir) or check_dir == parent_dir:
                        for creator_idx, creator_info in creators:
                            if creator_idx < idx:
                                dependency = DependencyInfo(
                                    from_node_id=creator_info.id,
                                    to_node_id=node_info.id,
                                    dependency_type="DIRECTORY_CREATION",
                                    resource_path=check_dir,
                                    description=f"Directory {check_dir} must exist for files in {parent_dir}"
                                )
                                dependencies.append(dependency)
                                break  # 同じディレクトリに対して複数の依存を追加しない
    
    # リソース競合による順序依存
    for i in range(len(node_infos) - 1):
        from_node = node_infos[i]
        to_node = node_infos[i + 1]
        
        # すでに依存関係がある場合はスキップ
        existing_deps = [d for d in dependencies 
                        if (d.from_node_id == from_node.id and d.to_node_id == to_node.id) or
                           (d.from_node_id == to_node.id and d.to_node_id == from_node.id)]
        if existing_deps:
            continue
        
        # リソースの競合がある場合のみ順序依存を追加
        if has_resource_conflict_pure(from_node, to_node):
            dependency = DependencyInfo(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                dependency_type="EXECUTION_ORDER",
                resource_path="",
                description="Preserve original execution order due to resource conflict"
            )
            dependencies.append(dependency)
    
    return dependencies


def is_parent_directory_pure(parent_path: str, child_path: str) -> bool:
    """
    parent_pathがchild_pathの親ディレクトリかどうかを判定する純粋関数
    
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
    except:
        # パスの解決に失敗した場合は文字列で判定
        return child_path.startswith(parent_path + '/')


def has_resource_conflict_pure(node1: NodeInfo, node2: NodeInfo) -> bool:
    """
    2つのノード間でリソースの競合があるかどうかを判定する純粋関数
    
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
    if (node1.creates_files & node2.reads_files) or \
       (node2.creates_files & node1.reads_files):
        return True
    
    return False


def build_execution_graph_pure(steps: List[Step], context: Optional[StepContext] = None) -> GraphBuildResult:
    """
    ステップリストから実行グラフを構築する純粋関数
    
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
    node_infos = build_node_info_list_pure(steps, context)
    
    # 依存関係を分析
    dependencies = analyze_node_dependencies_pure(node_infos)
    
    # バリデーション
    validation_errors = validate_graph_structure_pure(node_infos, dependencies)
    errors.extend(validation_errors)
    
    return GraphBuildResult(
        nodes=node_infos,
        dependencies=dependencies,
        errors=errors,
        warnings=warnings
    )


def validate_graph_structure_pure(nodes: List[NodeInfo], dependencies: List[DependencyInfo]) -> List[str]:
    """
    グラフ構造の妥当性を検証する純粋関数
    
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


def calculate_graph_metrics_pure(result: GraphBuildResult) -> Dict[str, Any]:
    """
    グラフ構築結果のメトリクスを計算する純粋関数
    
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