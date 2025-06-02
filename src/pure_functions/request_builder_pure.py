"""
リクエスト構築の純粋関数
StepからRequestへの変換ロジックを純粋関数として実装
"""
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from pathlib import Path
from src.env_core.step.step import Step, StepType, StepContext


@dataclass(frozen=True)
class RequestData:
    """リクエストデータの不変データクラス"""
    request_type: str
    operation_type: str
    command: List[str]
    parameters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            object.__setattr__(self, 'parameters', {})
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class ResourceInfo:
    """リソース情報の不変データクラス"""
    creates_files: Set[str]
    creates_dirs: Set[str] 
    reads_files: Set[str]
    requires_dirs: Set[str]
    
    def __post_init__(self):
        # Setのデフォルト値処理
        if self.creates_files is None:
            object.__setattr__(self, 'creates_files', set())
        if self.creates_dirs is None:
            object.__setattr__(self, 'creates_dirs', set())
        if self.reads_files is None:
            object.__setattr__(self, 'reads_files', set())
        if self.requires_dirs is None:
            object.__setattr__(self, 'requires_dirs', set())


@dataclass(frozen=True)
class RequestBuildResult:
    """リクエスト構築結果"""
    request_data: Optional[RequestData]
    resource_info: ResourceInfo
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


def extract_resource_info_pure(step: Step) -> ResourceInfo:
    """
    ステップからリソース情報を抽出する純粋関数
    
    Args:
        step: 分析対象のステップ
        
    Returns:
        ResourceInfo: 抽出されたリソース情報
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
        # ビルドは特定のディレクトリで実行される
        if step.cmd:
            build_dir = step.cmd[0] if step.cmd[0] else "./workspace"
            requires_dirs.add(build_dir)
    
    elif step.type == StepType.TEST:
        # TESTステップは実行対象ファイルを読み取る
        if len(step.cmd) >= 2:
            target_file = step.cmd[1]
            reads_files.add(target_file)
            
            # 実行ファイルの親ディレクトリも必要
            parent = str(Path(target_file).parent)
            if parent != '.':
                requires_dirs.add(parent)
    
    elif step.type == StepType.PYTHON:
        # Pythonスクリプト実行
        if step.cmd:
            script_content = step.cmd[0]
            # スクリプト内容に基づくリソース分析は複雑なので基本のみ
            requires_dirs.add("./workspace")
    
    elif step.type == StepType.SHELL:
        # シェルコマンドの基本的な分析
        if step.cmd:
            # 基本的なワークスペースディレクトリを要求
            requires_dirs.add("./workspace")
    
    elif step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
        # Dockerコマンドは基本的にワークスペースを使用
        requires_dirs.add("./workspace")
    
    return ResourceInfo(
        creates_files=creates_files,
        creates_dirs=creates_dirs,
        reads_files=reads_files,
        requires_dirs=requires_dirs
    )


def step_to_request_data_pure(step: Step, context: Optional[StepContext] = None) -> RequestBuildResult:
    """
    ステップからリクエストデータを作成する純粋関数
    
    Args:
        step: 変換対象のステップ
        context: ステップコンテキスト（オプション）
        
    Returns:
        RequestBuildResult: 構築結果
    """
    errors = []
    warnings = []
    
    # 基本的なバリデーション
    if not step or not step.type:
        errors.append("Invalid step: missing type")
        return RequestBuildResult(
            request_data=None,
            resource_info=ResourceInfo(set(), set(), set(), set()),
            errors=errors,
            warnings=warnings
        )
    
    if not step.cmd:
        errors.append(f"Invalid step: {step.type.value} requires command")
        return RequestBuildResult(
            request_data=None,
            resource_info=ResourceInfo(set(), set(), set(), set()),
            errors=errors,
            warnings=warnings
        )
    
    # リソース情報を抽出
    resource_info = extract_resource_info_pure(step)
    
    # ステップタイプ別のリクエストデータ作成
    request_data = None
    
    if step.type == StepType.SHELL:
        request_data = RequestData(
            request_type="shell",
            operation_type="SHELL",
            command=step.cmd,
            parameters={
                "allow_failure": getattr(step, 'allow_failure', False),
                "show_output": getattr(step, 'show_output', True),
                "timeout": getattr(step, 'timeout', None)
            },
            metadata={
                "step_type": step.type.value,
                "original_cmd": step.cmd
            }
        )
    
    elif step.type == StepType.PYTHON:
        request_data = RequestData(
            request_type="python",
            operation_type="PYTHON",
            command=step.cmd,
            parameters={
                "script_content": step.cmd[0] if step.cmd else "",
                "allow_failure": getattr(step, 'allow_failure', False)
            },
            metadata={
                "step_type": step.type.value,
                "interpreter": "python3"
            }
        )
    
    elif step.type in [StepType.COPY, StepType.MOVE, StepType.MKDIR, StepType.TOUCH, 
                       StepType.REMOVE, StepType.RMTREE, StepType.MOVETREE]:
        request_data = RequestData(
            request_type="file",
            operation_type="FILE",
            command=step.cmd,
            parameters={
                "operation": step.type.value,
                "recursive": step.type in [StepType.RMTREE, StepType.MOVETREE]
            },
            metadata={
                "step_type": step.type.value,
                "file_operation": step.type.value
            }
        )
    
    elif step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
        request_data = RequestData(
            request_type="docker",
            operation_type="DOCKER",
            command=step.cmd,
            parameters={
                "docker_operation": step.type.value,
                "container_name": _extract_container_name_pure(step, context)
            },
            metadata={
                "step_type": step.type.value,
                "requires_docker": True
            }
        )
    
    elif step.type in [StepType.BUILD, StepType.TEST]:
        request_data = RequestData(
            request_type="composite",
            operation_type="COMPOSITE", 
            command=step.cmd,
            parameters={
                "build_type": step.type.value,
                "target_directory": step.cmd[0] if step.cmd else "./workspace"
            },
            metadata={
                "step_type": step.type.value,
                "composite_operation": True
            }
        )
    
    elif step.type == StepType.OJ:
        request_data = RequestData(
            request_type="oj",
            operation_type="OJ",
            command=step.cmd,
            parameters={
                "oj_command": " ".join(step.cmd)
            },
            metadata={
                "step_type": step.type.value,
                "requires_oj": True
            }
        )
    
    else:
        errors.append(f"Unsupported step type: {step.type.value}")
    
    return RequestBuildResult(
        request_data=request_data,
        resource_info=resource_info,
        errors=errors,
        warnings=warnings
    )


def _extract_container_name_pure(step: Step, context: Optional[StepContext]) -> str:
    """
    ステップとコンテキストからコンテナ名を抽出する純粋関数
    
    Args:
        step: ステップ
        context: コンテキスト
        
    Returns:
        コンテナ名
    """
    if context:
        # コンテキストから命名規則に基づいてコンテナ名を生成
        return f"cph_{context.contest_name}_{context.problem_name}_{context.language}_container"
    else:
        # デフォルトコンテナ名
        return "cph_default_container"


def validate_step_command_pure(step: Step) -> List[str]:
    """
    ステップコマンドの妥当性を検証する純粋関数
    
    Args:
        step: 検証対象のステップ
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    if not step.cmd:
        errors.append(f"Step {step.type.value} requires a command")
        return errors
    
    # ステップタイプ別の検証
    if step.type == StepType.COPY or step.type == StepType.MOVE:
        if len(step.cmd) < 2:
            errors.append(f"{step.type.value} requires source and destination")
    
    elif step.type == StepType.MKDIR or step.type == StepType.TOUCH:
        if len(step.cmd) < 1:
            errors.append(f"{step.type.value} requires a path")
    
    elif step.type == StepType.PYTHON:
        if len(step.cmd) < 1:
            errors.append("Python step requires script content")
    
    elif step.type == StepType.SHELL:
        if len(step.cmd) < 1:
            errors.append("Shell step requires a command")
    
    elif step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC]:
        if len(step.cmd) < 1:
            errors.append(f"{step.type.value} requires docker command")
    
    return errors


def optimize_request_sequence_pure(results: List[RequestBuildResult]) -> List[RequestBuildResult]:
    """
    リクエストシーケンスを最適化する純粋関数
    
    Args:
        results: リクエスト構築結果のリスト
        
    Returns:
        最適化されたリクエスト構築結果のリスト
    """
    # エラーを持つリクエストを除外
    valid_results = [result for result in results if result.request_data is not None]
    
    # 重複する操作を検出・統合
    optimized_results = []
    seen_operations = set()
    
    for result in valid_results:
        operation_key = (
            result.request_data.request_type,
            result.request_data.operation_type,
            tuple(result.request_data.command)
        )
        
        if operation_key not in seen_operations:
            optimized_results.append(result)
            seen_operations.add(operation_key)
    
    return optimized_results


def analyze_request_dependencies_pure(results: List[RequestBuildResult]) -> List[Tuple[int, int]]:
    """
    リクエスト間の依存関係を分析する純粋関数
    
    Args:
        results: リクエスト構築結果のリスト
        
    Returns:
        依存関係のタプルリスト (from_index, to_index)
    """
    dependencies = []
    
    for i, result_i in enumerate(results):
        if not result_i.request_data:
            continue
            
        for j, result_j in enumerate(results):
            if i >= j or not result_j.request_data:
                continue
            
            # ファイル作成 -> 読み取り依存
            if (result_i.resource_info.creates_files & 
                result_j.resource_info.reads_files):
                dependencies.append((i, j))
            
            # ディレクトリ作成 -> 要求依存
            if (result_i.resource_info.creates_dirs & 
                result_j.resource_info.requires_dirs):
                dependencies.append((i, j))
    
    return dependencies


def calculate_request_metrics_pure(results: List[RequestBuildResult]) -> Dict[str, Any]:
    """
    リクエスト構築のメトリクスを計算する純粋関数
    
    Args:
        results: リクエスト構築結果のリスト
        
    Returns:
        メトリクス辞書
    """
    total_requests = len(results)
    valid_requests = len([r for r in results if r.request_data is not None])
    error_count = len([r for r in results if r.errors])
    warning_count = len([r for r in results if r.warnings])
    
    # リクエストタイプ別の統計
    request_types = {}
    for result in results:
        if result.request_data:
            req_type = result.request_data.request_type
            request_types[req_type] = request_types.get(req_type, 0) + 1
    
    # リソース統計
    total_files_created = sum(len(r.resource_info.creates_files) for r in results)
    total_dirs_created = sum(len(r.resource_info.creates_dirs) for r in results)
    total_files_read = sum(len(r.resource_info.reads_files) for r in results)
    
    return {
        "total_requests": total_requests,
        "valid_requests": valid_requests,
        "error_count": error_count,
        "warning_count": warning_count,
        "success_rate": valid_requests / total_requests if total_requests > 0 else 0,
        "request_types": request_types,
        "total_files_created": total_files_created,
        "total_dirs_created": total_dirs_created,
        "total_files_read": total_files_read
    }