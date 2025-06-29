"""ステップの依存関係を解析し、必要な準備ステップを挿入する純粋関数群
"""
from pathlib import Path
from typing import Optional, Dict, Any

from src.domain.services.step_generation_service import execution_context_to_simple_context
from src.domain.step import Step, StepContext, StepType
from src.domain.step_runner import expand_template


def create_mkdir_step(path: str, cwd: Optional[str] = None) -> Step:
    """MKDIRステップを作成するファクトリー関数
    
    Args:
        path: 作成するディレクトリのパス
        cwd: 作業ディレクトリ（オプション）
        
    Returns:
        Step: 必要なフィールドを持つMKDIRステップ
    """
    return Step(
        type=StepType.MKDIR,
        cmd=[path],
        allow_failure=True,
        show_output=False,
        cwd=cwd,
        force_env_type=None,
        format_options=None,
        output_format=None,
        format_preset=None,
        when=None,
        name=None,
        auto_generated=True,
        max_workers=1
    )


def resolve_dependencies(steps: list[Step], context: StepContext) -> list[Step]:
    """ステップリストの依存関係を解決し、必要な準備ステップを挿入する純粋関数

    Args:
        steps: 元のステップリスト
        context: ステップ実行コンテキスト

    Returns:
        List[Step]: 依存関係を解決済みのステップリスト
    """
    resolved_steps = []
    existing_dirs = set()
    existing_files = set()
    for step in steps:
        should_generate_prep = True
        if step.when:
            try:
                simple_context = execution_context_to_simple_context(context)
                expanded_cmd = [expand_template(arg, simple_context) for arg in step.cmd]
                invalid_paths = [str(arg) for arg in expanded_cmd if '//' in str(arg) or str(arg).endswith('/.')]
                if invalid_paths:
                    should_generate_prep = False
            except Exception:
                pass
        prep_steps = []
        if should_generate_prep:
            prep_steps = generate_preparation_steps(step, existing_dirs, existing_files, context)
            resolved_steps.extend(prep_steps)
        for prep_step in prep_steps:
            if prep_step.type == StepType.MKDIR:
                existing_dirs.add(prep_step.cmd[0])
            elif prep_step.type == StepType.TOUCH:
                existing_files.add(prep_step.cmd[0])
        resolved_steps.append(step)
        update_resource_tracking(step, existing_dirs, existing_files)
    return resolved_steps

def generate_preparation_steps(step: Step, existing_dirs: set[str], existing_files: set[str], context: StepContext) -> list[Step]:
    """単一ステップに必要な準備ステップを生成する純粋関数

    Args:
        step: 対象ステップ
        existing_dirs: 既に作成済みのディレクトリセット
        existing_files: 既に確認済みのファイルセット
        context: ステップ実行コンテキスト

    Returns:
        List[Step]: 必要な準備ステップのリスト
    """
    prep_steps = []
    if step.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE]:
        if len(step.cmd) >= 2:
            dst_path = step.cmd[1]
            dst_dir = str(Path(dst_path).parent)
            if dst_dir != '.' and dst_dir not in existing_dirs:
                prep_steps.append(create_mkdir_step(dst_dir))
    elif step.type == StepType.TOUCH and len(step.cmd) >= 1:
        file_path = step.cmd[0]
        parent_dir = str(Path(file_path).parent)
        if parent_dir != '.' and parent_dir not in existing_dirs:
            prep_steps.append(create_mkdir_step(parent_dir))
    if step.cwd and step.cwd not in existing_dirs:
        prep_steps.append(create_mkdir_step(step.cwd, cwd=step.cwd))
    return prep_steps

def update_resource_tracking(step: Step, existing_dirs: set[str], existing_files: set[str]) -> None:
    """ステップ実行後のリソース状態を追跡情報に反映する純粋関数

    Args:
        step: 実行されるステップ
        existing_dirs: 既存ディレクトリセット（更新される）
        existing_files: 既存ファイルセット（更新される）
    """
    if step.type == StepType.MKDIR and len(step.cmd) >= 1:
        existing_dirs.add(step.cmd[0])
    elif step.type == StepType.TOUCH and len(step.cmd) >= 1:
        existing_files.add(step.cmd[0])
        parent_dir = str(Path(step.cmd[0]).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)
    elif step.type in [StepType.COPY, StepType.MOVE] and len(step.cmd) >= 2:
        dst_path = step.cmd[1]
        existing_files.add(dst_path)
        parent_dir = str(Path(dst_path).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)
    elif step.type == StepType.MOVETREE and len(step.cmd) >= 2:
        dst_path = step.cmd[1]
        existing_dirs.add(dst_path)
        parent_dir = str(Path(dst_path).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)
    elif step.type in [StepType.REMOVE, StepType.RMTREE] and len(step.cmd) >= 1:
        removed_path = step.cmd[0]
        existing_files.discard(removed_path)
        existing_dirs.discard(removed_path)

def analyze_step_dependencies(steps: list[Step]) -> dict[int, list[int]]:
    """ステップ間の依存関係を分析する純粋関数

    Args:
        steps: 分析対象のステップリスト

    Returns:
        Dict[int, List[int]]: ステップインデックスから依存するステップインデックスのリストへのマップ
    """
    dependencies = {}
    for i, step in enumerate(steps):
        deps = []
        if step.type in [StepType.COPY, StepType.MOVE] and len(step.cmd) >= 1:
            src_path = step.cmd[0]
            for j, prev_step in enumerate(steps[:i]):
                if creates_file(prev_step, src_path):
                    deps.append(j)
        dependencies[i] = deps
    return dependencies

def creates_file(step: Step, file_path: str) -> bool:
    """ステップが指定されたファイルを作成するかチェックする純粋関数

    Args:
        step: チェック対象のステップ
        file_path: ファイルパス

    Returns:
        bool: ファイルを作成する場合True
    """
    if step.type == StepType.TOUCH and len(step.cmd) >= 1:
        return step.cmd[0] == file_path
    if step.type in [StepType.COPY, StepType.MOVE] and len(step.cmd) >= 2:
        return step.cmd[1] == file_path
    if step.type in [StepType.SHELL, StepType.PYTHON, StepType.BUILD]:
        return False
    return False

def optimize_mkdir_steps(steps: list[Step]) -> list[Step]:
    """連続するmkdirステップを最適化する純粋関数

    Args:
        steps: 最適化対象のステップリスト

    Returns:
        List[Step]: 最適化されたステップリスト
    """
    if not steps:
        return steps
    optimized = []
    i = 0
    while i < len(steps):
        step = steps[i]
        if step.type == StepType.MKDIR:
            mkdir_paths = [step.cmd[0]]
            j = i + 1
            while j < len(steps) and steps[j].type == StepType.MKDIR and (steps[j].allow_failure == step.allow_failure) and (steps[j].show_output == step.show_output):
                mkdir_paths.append(steps[j].cmd[0])
                j += 1
            unique_paths = list(dict.fromkeys(mkdir_paths))
            for path in unique_paths:
                optimized.append(Step(
                    type=StepType.MKDIR,
                    cmd=[path],
                    allow_failure=step.allow_failure,
                    show_output=step.show_output,
                    cwd=step.cwd,
                    force_env_type=step.force_env_type,
                    format_options=step.format_options,
                    output_format=step.output_format,
                    format_preset=step.format_preset,
                    when=step.when,
                    name=step.name,
                    auto_generated=step.auto_generated,
                    max_workers=step.max_workers
                ))
            i = j
        else:
            optimized.append(step)
            i += 1
    return optimized

def optimize_copy_steps(steps: list[Step]) -> list[Step]:
    """冗長なコピー操作を除去する純粋関数

    Args:
        steps: 最適化対象のステップリスト

    Returns:
        List[Step]: 最適化されたステップリスト
    """
    if not steps:
        return steps
    optimized = []
    seen_operations = set()
    for step in steps:
        if step.type in [StepType.COPY, StepType.MOVE, StepType.COPYTREE, StepType.MOVETREE]:
            if len(step.cmd) >= 2:
                operation_key = (step.type, step.cmd[0], step.cmd[1])
                if operation_key not in seen_operations:
                    seen_operations.add(operation_key)
                    optimized.append(step)
                else:
                    for i, existing_step in enumerate(optimized):
                        if existing_step.type == step.type and len(existing_step.cmd) >= 2 and (existing_step.cmd[0] == step.cmd[0]) and (existing_step.cmd[1] == step.cmd[1]):
                            if not step.allow_failure and existing_step.allow_failure:
                                optimized[i] = step
                            break
            else:
                optimized.append(step)
        else:
            optimized.append(step)
    return optimized
