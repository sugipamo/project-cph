"""ステップの依存関係を解析し、必要な準備ステップを挿入する純粋関数群
"""
from pathlib import Path

from .step import Step, StepContext, StepType


def resolve_dependencies(steps: list[Step], context: StepContext) -> list[Step]:
    """ステップリストの依存関係を解決し、必要な準備ステップを挿入する純粋関数

    Args:
        steps: 元のステップリスト
        context: ステップ実行コンテキスト

    Returns:
        List[Step]: 依存関係を解決済みのステップリスト
    """
    resolved_steps = []
    existing_dirs = set()  # 作成済みディレクトリを追跡
    existing_files = set()  # 存在確認済みファイルを追跡

    for step in steps:
        # when条件があるステップはスキップされる可能性があるため、準備ステップも条件付きで追加
        should_generate_prep = True
        if step.when:
            # when条件がある場合は、条件が満たされる可能性が低い場合は準備ステップをスキップ
            # TODO: より精密な条件評価が必要だが、暫定的に無効なパス（///）を含む場合はスキップ
            from src.workflow.step.step_generation_service import execution_context_to_simple_context
            from src.workflow.step.step_runner import expand_template
            try:
                simple_context = execution_context_to_simple_context(context)
                expanded_cmd = [expand_template(arg, simple_context) for arg in step.cmd]
                # 無効なパス（連続スラッシュや不正なパス）を含む場合は準備ステップをスキップ
                invalid_paths = [str(arg) for arg in expanded_cmd if '//' in str(arg) or str(arg).endswith('/.')]
                if invalid_paths:
                    should_generate_prep = False
            except Exception:
                pass  # エラーが発生した場合は通常通り処理

        prep_steps = []
        if should_generate_prep:
            # 現在のステップに必要な準備ステップを生成
            prep_steps = generate_preparation_steps(step, existing_dirs, existing_files, context)
            # 準備ステップを追加
            resolved_steps.extend(prep_steps)

        # 準備ステップで作成されたディレクトリ/ファイルを記録
        for prep_step in prep_steps:
            if prep_step.type == StepType.MKDIR:
                existing_dirs.add(prep_step.cmd[0])
            elif prep_step.type == StepType.TOUCH:
                existing_files.add(prep_step.cmd[0])

        # 元のステップを追加
        resolved_steps.append(step)

        # 元のステップで作成/変更されるリソースを記録
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

    # ファイル操作系のステップに対する依存解決
    if step.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE]:
        if len(step.cmd) >= 2:
            dst_path = step.cmd[1]

            # 宛先ディレクトリの作成が必要かチェック
            dst_dir = str(Path(dst_path).parent)
            if dst_dir != '.' and dst_dir not in existing_dirs:
                mkdir_step = Step(
                    type=StepType.MKDIR,
                    cmd=[dst_dir],
                    allow_failure=True,  # ディレクトリが既に存在する場合は失敗を許可
                    auto_generated=True  # fitting/依存関係解決で自動生成されたステップ
                )
                prep_steps.append(mkdir_step)

    elif step.type == StepType.TOUCH and len(step.cmd) >= 1:
        file_path = step.cmd[0]

        # ファイルの親ディレクトリ作成が必要かチェック
        parent_dir = str(Path(file_path).parent)
        if parent_dir != '.' and parent_dir not in existing_dirs:
            mkdir_step = Step(
                type=StepType.MKDIR,
                cmd=[parent_dir],
                allow_failure=True,
                auto_generated=True  # fitting/依存関係解決で自動生成されたステップ
            )
            prep_steps.append(mkdir_step)

    # 作業ディレクトリの存在チェック
    if step.cwd and step.cwd not in existing_dirs:
        # 作業ディレクトリが存在しない場合は作成
        mkdir_step = Step(
            type=StepType.MKDIR,
            cmd=[step.cwd],
            allow_failure=True,
            auto_generated=True  # fitting/依存関係解決で自動生成されたステップ
        )
        prep_steps.append(mkdir_step)

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
        # touchはファイルの親ディレクトリも作成する
        parent_dir = str(Path(step.cmd[0]).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)

    elif step.type in [StepType.COPY, StepType.MOVE] and len(step.cmd) >= 2:
        dst_path = step.cmd[1]
        existing_files.add(dst_path)
        # 宛先の親ディレクトリも作成される
        parent_dir = str(Path(dst_path).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)

    elif step.type == StepType.MOVETREE and len(step.cmd) >= 2:
        dst_path = step.cmd[1]
        existing_dirs.add(dst_path)
        # 宛先の親ディレクトリも作成される
        parent_dir = str(Path(dst_path).parent)
        if parent_dir != '.':
            existing_dirs.add(parent_dir)

    elif step.type in [StepType.REMOVE, StepType.RMTREE] and len(step.cmd) >= 1:
        # ファイル/ディレクトリが削除される
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

            # このファイルを作成するステップを探す
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
        # シェルコマンドは出力ファイルを作成する可能性があるが、
        # 静的解析では判断できないため保守的にFalseを返す
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
            # 連続するmkdirステップを収集
            mkdir_paths = [step.cmd[0]]
            j = i + 1

            # 同じ属性を持つmkdirステップのみをマージ
            while (j < len(steps) and
                   steps[j].type == StepType.MKDIR and
                   steps[j].allow_failure == step.allow_failure and
                   steps[j].show_output == step.show_output):
                mkdir_paths.append(steps[j].cmd[0])
                j += 1

            # 重複を除去（順序は保持）
            unique_paths = list(dict.fromkeys(mkdir_paths))

            # 最適化されたmkdirステップを追加
            for path in unique_paths:
                optimized.append(Step(
                    type=StepType.MKDIR,
                    cmd=[path],
                    allow_failure=step.allow_failure,
                    show_output=step.show_output,
                    cwd=step.cwd,
                    force_env_type=step.force_env_type
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
    seen_operations = set()  # (type, src, dst) のタプルを記録

    for step in steps:
        if step.type in [StepType.COPY, StepType.MOVE, StepType.COPYTREE, StepType.MOVETREE]:
            if len(step.cmd) >= 2:
                # シンプルな文字列比較で重複チェック
                operation_key = (step.type, step.cmd[0], step.cmd[1])

                # 同じ操作が既に記録されているかチェック
                if operation_key not in seen_operations:
                    seen_operations.add(operation_key)
                    optimized.append(step)
                # 重複している場合は、より厳しい制約を持つものを優先
                else:
                    # 既存のステップを検索して比較
                    for i, existing_step in enumerate(optimized):
                        if (existing_step.type == step.type and
                            len(existing_step.cmd) >= 2 and
                            existing_step.cmd[0] == step.cmd[0] and
                            existing_step.cmd[1] == step.cmd[1]):
                            # より厳しい制約（allow_failure=False）を優先
                            if not step.allow_failure and existing_step.allow_failure:
                                optimized[i] = step
                            break
            else:
                # cmdが不正な場合はそのまま追加
                optimized.append(step)
        else:
            # コピー系以外のステップはそのまま追加
            optimized.append(step)

    return optimized
