"""純粋関数ベースのステップ生成の核となる関数群
"""
from typing import Any

from .step import Step, StepContext, StepGenerationResult, StepType


def create_step_context_from_execution_context(execution_context) -> StepContext:
    """ExecutionContextからStepContextを作成するヘルパー関数

    Args:
        execution_context: ExecutionContextオブジェクト

    Returns:
        StepContext: ステップ生成用コンテキスト
    """
    # ExecutionContextからfile_patternsを取得
    file_patterns = None
    if hasattr(execution_context, 'env_json') and execution_context.env_json:
        language_config = execution_context.env_json.get(execution_context.language, {})
        file_patterns = language_config.get('file_patterns', {})

    return StepContext(
        contest_name=execution_context.contest_name,
        problem_name=execution_context.problem_name,
        language=execution_context.language,
        env_type=execution_context.env_type,
        command_type=execution_context.command_type,
        workspace_path=getattr(execution_context, 'workspace_path', ''),
        contest_current_path=getattr(execution_context, 'contest_current_path', ''),
        contest_stock_path=getattr(execution_context, 'contest_stock_path', None),
        contest_template_path=getattr(execution_context, 'contest_template_path', None),
        contest_temp_path=getattr(execution_context, 'contest_temp_path', None),
        source_file_name=getattr(execution_context, 'source_file_name', None),
        language_id=getattr(execution_context, 'language_id', None),
        file_patterns=file_patterns
    )


def generate_steps_from_json(
    json_steps: list[dict[str, Any]],
    context
) -> StepGenerationResult:
    """JSONステップリストから実行可能ステップを生成する純粋関数

    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報（StepContextまたはExecutionContext）

    Returns:
        StepGenerationResult: 生成されたステップとエラー/警告情報
    """
    # ExecutionContextの場合はStepContextに変換
    if not isinstance(context, StepContext):
        context = create_step_context_from_execution_context(context)
    steps = []
    errors = []
    warnings = []

    for i, json_step in enumerate(json_steps):
        try:
            step = create_step_from_json(json_step, context)
            steps.append(step)
        except ValueError as e:
            errors.append(f"Step {i}: {e!s}")
        except Exception as e:
            errors.append(f"Step {i}: Unexpected error - {e!s}")

    return StepGenerationResult(steps, errors, warnings)


def create_step_from_json(json_step: dict[str, Any], context: StepContext) -> Step:
    """単一のJSONステップから実行可能ステップを生成する純粋関数

    Args:
        json_step: JSONステップの辞書
        context: ステップ生成コンテキスト

    Returns:
        Step: 生成されたステップ

    Raises:
        ValueError: 無効なステップ定義の場合
    """
    step_type_str = json_step.get('type')
    if not step_type_str:
        raise ValueError("Step must have 'type' field")

    try:
        step_type = StepType(step_type_str)
    except ValueError as e:
        raise ValueError(f"Unknown step type: {step_type_str}") from e

    raw_cmd = json_step.get('cmd', [])
    if not isinstance(raw_cmd, list):
        raise ValueError("Step 'cmd' must be a list")

    # ファイル操作ステップの場合はパターン展開を適用
    if step_type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE] and len(raw_cmd) >= 2:
        # ソースとデスティネーションでパターン展開
        formatted_cmd = [
            expand_file_patterns(raw_cmd[0], context, step_type),
            expand_file_patterns(raw_cmd[1], context, step_type)
        ]
        # 残りの引数は通常のフォーマット
        formatted_cmd.extend([format_template(arg, context) for arg in raw_cmd[2:]])
    else:
        # コマンドの文字列フォーマット
        formatted_cmd = [format_template(arg, context) for arg in raw_cmd]

    # オプション属性の処理
    allow_failure = json_step.get('allow_failure', False)
    show_output = json_step.get('show_output', False)

    cwd = format_template(json_step.get('cwd'), context) if json_step.get('cwd') else None
    force_env_type = json_step.get('force_env_type')
    format_options = json_step.get('format_options')
    output_format = json_step.get('output_format')
    format_preset = json_step.get('format_preset')

    # Handle file_preparation specific attributes
    step_kwargs = {
        'type': step_type,
        'cmd': formatted_cmd,
        'allow_failure': allow_failure,
        'show_output': show_output,
        'cwd': cwd,
        'force_env_type': force_env_type,
        'format_options': format_options,
        'output_format': output_format,
        'format_preset': format_preset
    }

    return Step(**step_kwargs)


def format_template(template: Any, context: StepContext) -> str:
    """テンプレート文字列をコンテキスト情報でフォーマットする純粋関数

    Args:
        template: フォーマット対象の値
        context: フォーマット用のコンテキスト

    Returns:
        str: フォーマット済みの文字列
    """
    if not isinstance(template, str):
        return str(template) if template is not None else ""

    format_dict = context.to_format_dict()

    result = template
    for key, value in format_dict.items():
        placeholder = f'{{{key}}}'
        if placeholder in result:
            result = result.replace(placeholder, str(value))

    return result


def expand_file_patterns(template: str, context: StepContext, step_type: StepType = None) -> str:
    """ファイルパターンを展開して文字列を返す純粋関数

    Args:
        template: パターンを含むテンプレート文字列
        context: ステップ生成コンテキスト
        step_type: ステップタイプ（ディレクトリ操作の判定用）

    Returns:
        str: 展開されたパターン文字列（ワイルドカード形式）
    """
    if not context.file_patterns:
        return format_template(template, context)

    # ファイルパターンプレースホルダーを検出
    for pattern_name, patterns in context.file_patterns.items():
        placeholder = f'{{{pattern_name}}}'
        if placeholder in template and patterns:
            pattern = patterns[0]  # 最初のパターンを使用

            # ディレクトリ操作（movetree, copytree, rmtree）の場合は、ディレクトリ部分のみを抽出
            if step_type in [StepType.MOVETREE, StepType.RMTREE] and '/' in pattern:
                # パターンからディレクトリ部分を抽出 (例: "test/*.in" -> "test")
                directory_part = pattern.split('/')[0]
                result = template.replace(placeholder, directory_part)
                return format_template(result, context)

            # 通常のファイル操作やその他の場合は元のパターンを使用
            result = template.replace(placeholder, pattern)
            return format_template(result, context)

    # パターンプレースホルダーがない場合は通常のフォーマット
    return format_template(template, context)


def validate_step_sequence(steps: list[Step]) -> list[str]:
    """ステップシーケンスの妥当性を検証する純粋関数

    Args:
        steps: 検証対象のステップリスト

    Returns:
        List[str]: 検証エラーのリスト（空の場合は妥当）
    """
    errors = []

    for i, step in enumerate(steps):
        # 各ステップの基本検証
        step_errors = validate_single_step(step)
        for error in step_errors:
            errors.append(f"Step {i} ({step.type.value}): {error}")

    return errors


def validate_single_step(step: Step) -> list[str]:
    """単一ステップの妥当性を検証する純粋関数

    Args:
        step: 検証対象のステップ

    Returns:
        List[str]: 検証エラーのリスト
    """
    errors = []

    # コマンドの空チェック
    if not step.cmd:
        errors.append("Command cannot be empty")
        return errors

    # 各ステップタイプ固有の検証
    if step.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE]:
        if len(step.cmd) < 2:
            errors.append(f"Requires at least 2 arguments (src, dst), got {len(step.cmd)}")
        elif not step.cmd[0] or not step.cmd[1]:
            errors.append("Source and destination paths cannot be empty")

    elif step.type in [StepType.MKDIR, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE]:
        if len(step.cmd) < 1:
            errors.append("Requires at least 1 argument (path)")
        elif not step.cmd[0]:
            errors.append("Path cannot be empty")

    elif step.type in [StepType.SHELL, StepType.PYTHON, StepType.OJ, StepType.TEST, StepType.BUILD] and not step.cmd[0]:
            errors.append("Command cannot be empty")

    return errors


def optimize_step_sequence(steps: list[Step]) -> list[Step]:
    """ステップシーケンスを最適化する純粋関数

    Args:
        steps: 最適化対象のステップリスト

    Returns:
        List[Step]: 最適化されたステップリスト
    """
    # 連続する同じディレクトリのmkdirを統合
    optimized = []
    i = 0

    while i < len(steps):
        step = steps[i]

        if step.type == StepType.MKDIR:
            # 連続するmkdirステップを収集
            mkdir_paths = [step.cmd[0]]
            j = i + 1

            while j < len(steps) and steps[j].type == StepType.MKDIR:
                mkdir_paths.append(steps[j].cmd[0])
                j += 1

            # 重複を除去して追加
            unique_paths = list(dict.fromkeys(mkdir_paths))  # 順序を保持して重複除去
            for path in unique_paths:
                optimized.append(Step(
                    type=StepType.MKDIR,
                    cmd=[path],
                    allow_failure=step.allow_failure,
                    show_output=step.show_output
                ))

            i = j
        else:
            optimized.append(step)
            i += 1

    return optimized
