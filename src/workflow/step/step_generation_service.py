"""ステップ生成・実行の核となる関数群（新しいシンプル設計）"""
from typing import Any, Dict, List, Union

from .step import Step, StepContext, StepGenerationResult, StepType
from .step_runner import ExecutionContext, expand_template, run_steps
from .step_runner import create_step as create_step_simple

# 新設定システムをサポート
try:
    from src.configuration.config_manager import TypedExecutionConfiguration
except ImportError:
    TypedExecutionConfiguration = None


def create_step_context_from_execution_context(execution_context: Union['TypedExecutionConfiguration', Any]) -> StepContext:
    """実行コンテキストからStepContextを作成するヘルパー関数（新旧システム対応）"""
    # TypedExecutionConfigurationの場合
    if TypedExecutionConfiguration and isinstance(execution_context, TypedExecutionConfiguration):
        # 新設定システムから直接値を取得
        file_patterns = getattr(execution_context, 'file_patterns', {})

        return StepContext(
            contest_name=execution_context.contest_name,
            problem_name=execution_context.problem_name,
            language=execution_context.language,
            env_type=execution_context.env_type,
            command_type=execution_context.command_type,
            local_workspace_path=str(execution_context.local_workspace_path),
            contest_current_path=str(execution_context.contest_current_path),
            contest_stock_path=str(getattr(execution_context, 'contest_stock_path', '')),
            contest_template_path=str(getattr(execution_context, 'contest_template_path', '')),
            contest_temp_path=str(getattr(execution_context, 'contest_temp_path', '')),
            source_file_name=execution_context.source_file_name,
            language_id=execution_context.language_id,
            file_patterns=file_patterns
        )

    # 従来のExecutionContextの場合
    # ExecutionContextからfile_patternsを取得
    file_patterns = None

    # ExecutionContextAdapterの場合、直接file_patternsプロパティから取得
    if hasattr(execution_context, 'file_patterns'):
        file_patterns = execution_context.file_patterns
    elif hasattr(execution_context, 'env_json') and execution_context.env_json:
        # ConfigurationLoaderを使用している場合はマージ済み設定なので直接アクセス
        if execution_context.language in execution_context.env_json:
            # 従来形式（言語がトップレベルキー）
            language_config = execution_context.env_json[execution_context.language]
        else:
            # ConfigurationLoader形式（マージ済み設定）
            language_config = execution_context.env_json

        if 'file_patterns' in language_config:
            raw_patterns = language_config['file_patterns']

            # ConfigurationLoaderの形式からシンプルな形式に変換（必要な場合）
            file_patterns = {}
            for pattern_name, pattern_data in raw_patterns.items():
                if isinstance(pattern_data, dict):
                    # {"workspace": ["patterns"], ...} の形式の場合
                    for location in ['workspace', 'contest_current', 'contest_stock']:
                        if location in pattern_data:
                            file_patterns[pattern_name] = pattern_data[location]
                            break
                else:
                    # 既にシンプルな形式の場合
                    file_patterns[pattern_name] = pattern_data

    return StepContext(
        contest_name=execution_context.contest_name,
        problem_name=execution_context.problem_name,
        language=execution_context.language,
        env_type=execution_context.env_type,
        command_type=execution_context.command_type,
        local_workspace_path=getattr(execution_context, 'local_workspace_path', ''),
        contest_current_path=getattr(execution_context, 'contest_current_path', ''),
        contest_stock_path=getattr(execution_context, 'contest_stock_path', None),
        contest_template_path=getattr(execution_context, 'contest_template_path', None),
        contest_temp_path=getattr(execution_context, 'contest_temp_path', None),
        source_file_name=getattr(execution_context, 'source_file_name', None),
        language_id=getattr(execution_context, 'language_id', None),
        file_patterns=file_patterns
    )


def execution_context_to_simple_context(execution_context: Union['TypedExecutionConfiguration', Any]) -> ExecutionContext:
    """実行コンテキストをSimpleExecutionContextに変換（新旧システム対応）"""
    # TypedExecutionConfigurationの場合
    if TypedExecutionConfiguration and isinstance(execution_context, TypedExecutionConfiguration):
        # 新設定システムから直接値を取得
        file_patterns = getattr(execution_context, 'file_patterns', {})

        return ExecutionContext(
            contest_name=execution_context.contest_name,
            problem_name=execution_context.problem_name,
            old_contest_name=getattr(execution_context, 'old_contest_name', ''),
            old_problem_name=getattr(execution_context, 'old_problem_name', ''),
            language=execution_context.language,
            local_workspace_path=str(execution_context.local_workspace_path),
            contest_current_path=str(execution_context.contest_current_path),
            contest_stock_path=str(getattr(execution_context, 'contest_stock_path', '')),
            contest_template_path=str(getattr(execution_context, 'contest_template_path', '')),
            source_file_name=execution_context.source_file_name,
            language_id=execution_context.language_id,
            run_command=execution_context.run_command,
            file_patterns=file_patterns
        )

    # 従来のExecutionContextの場合
    file_patterns = {}
    language_config = {}

    # ExecutionContextAdapterの場合、直接file_patternsプロパティから取得
    if hasattr(execution_context, 'file_patterns'):
        file_patterns = execution_context.file_patterns
    elif hasattr(execution_context, 'env_json') and execution_context.env_json:
        # ConfigurationLoaderを使用している場合はマージ済み設定なので直接アクセス
        if execution_context.language in execution_context.env_json:
            # 従来形式（言語がトップレベルキー）
            language_config = execution_context.env_json[execution_context.language]
        else:
            # ConfigurationLoader形式（マージ済み設定）
            language_config = execution_context.env_json

        if 'file_patterns' in language_config:
            raw_patterns = language_config['file_patterns']

            # ConfigurationLoaderの形式からシンプルな形式に変換（必要な場合）
            file_patterns = {}
            for pattern_name, pattern_data in raw_patterns.items():
                if isinstance(pattern_data, dict):
                    # {"workspace": ["patterns"], ...} の形式の場合
                    for location in ['workspace', 'contest_current', 'contest_stock']:
                        if location in pattern_data:
                            file_patterns[pattern_name] = pattern_data[location]
                            break
                else:
                    # 既にシンプルな形式の場合
                    file_patterns[pattern_name] = pattern_data

    # デバッグ: run_commandの値を確認
    run_command = language_config.get('run_command', '')
    if not run_command:
        # ExecutionContextAdapterの場合、runtime_configから取得を試行
        if hasattr(execution_context, 'config') and hasattr(execution_context.config, 'runtime_config'):
            run_command = execution_context.config.runtime_config.run_command
        elif hasattr(execution_context, 'run_command'):
            run_command = execution_context.run_command

        # run_commandは必須 - env.jsonで設定されている必要がある

    return ExecutionContext(
        contest_name=execution_context.contest_name,
        problem_name=execution_context.problem_name,
        old_contest_name=getattr(execution_context, 'old_contest_name', ''),
        old_problem_name=getattr(execution_context, 'old_problem_name', ''),
        language=execution_context.language,
        local_workspace_path=getattr(execution_context, 'local_workspace_path', ''),
        contest_current_path=getattr(execution_context, 'contest_current_path', ''),
        contest_stock_path=getattr(execution_context, 'contest_stock_path', ''),
        contest_template_path=getattr(execution_context, 'contest_template_path', ''),
        source_file_name=getattr(execution_context, 'source_file_name', ''),
        language_id=getattr(execution_context, 'language_id', ''),
        run_command=run_command,
        file_patterns=file_patterns
    )


def generate_steps_from_json(json_steps: List[Dict[str, Any]], context: Union['TypedExecutionConfiguration', Any]) -> StepGenerationResult:
    """JSONステップリストから実行可能ステップを生成する（新設計使用）

    Args:
        json_steps: JSONから読み込んだステップのリスト
        context: ステップ生成に必要なコンテキスト情報

    Returns:
        StepGenerationResult: 生成されたステップとエラー/警告情報
    """
    # 新しいシンプル設計を使用
    simple_context = execution_context_to_simple_context(context)
    step_results = run_steps(json_steps, simple_context)

    # 結果を旧形式に変換
    steps = []
    errors = []
    executed_steps = []

    for i, result in enumerate(step_results):
        if not result.success and result.error_message:
            errors.append(f"Step {i}: {result.error_message}")
        elif not result.skipped:
            executed_steps.append(result.step)

        # when条件でスキップされていないステップは全て含める（後方互換性）
        steps.append(result.step)

    return StepGenerationResult(steps, errors, [])


def create_step_from_json(json_step: Dict[str, Any], context: Union['TypedExecutionConfiguration', Any]) -> Step:
    """単一のJSONステップから実行可能ステップを生成する（後方互換性）"""
    simple_context = execution_context_to_simple_context(context)
    return create_step_simple(json_step, simple_context)


# 後方互換性のための関数（旧APIのエミュレーション）
def format_template(template: Any, context: Union['TypedExecutionConfiguration', Any]) -> str:
    """テンプレート文字列をフォーマットする（後方互換性）"""
    if not isinstance(template, str):
        return str(template) if template is not None else ""

    simple_context = execution_context_to_simple_context(context)
    return expand_template(template, simple_context)


def expand_file_patterns(template: str, context: Union['TypedExecutionConfiguration', Any], step_type=None) -> str:
    """ファイルパターンを展開する（後方互換性）"""
    # TypedExecutionConfigurationの場合は直接テンプレート展開を使用
    if TypedExecutionConfiguration and isinstance(context, TypedExecutionConfiguration):
        if hasattr(context, 'resolve_formatted_string'):
            try:
                return context.resolve_formatted_string(template)
            except Exception:
                pass  # フォールバック

    # 従来のシステム用
    from .step_runner import expand_file_patterns_in_text

    simple_context = execution_context_to_simple_context(context)

    # まずテンプレート変数を展開
    expanded = expand_template(template, simple_context)

    # ファイルパターンを展開
    if simple_context.file_patterns:
        expanded = expand_file_patterns_in_text(expanded, simple_context.file_patterns, step_type)

    return expanded


def validate_step_sequence(steps: List[Step]) -> List[str]:
    """ステップシーケンスの妥当性を検証する（後方互換性）"""
    errors = []
    for i, step in enumerate(steps):
        step_errors = validate_single_step(step)
        for error in step_errors:
            errors.append(f"Step {i} ({step.type.value}): {error}")
    return errors


def validate_single_step(step: Step) -> List[str]:
    """単一ステップの妥当性を検証する（後方互換性）"""
    errors = []

    if not step.cmd:
        errors.append("Command cannot be empty")
        return errors

    # 各ステップタイプ固有の検証
    if step.type in [StepType.COPY, StepType.COPYTREE, StepType.MOVE, StepType.MOVETREE]:
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


def optimize_step_sequence(steps: List[Step]) -> List[Step]:
    """ステップシーケンスを最適化する（後方互換性）"""
    # 簡単な最適化: 連続するmkdirを統合
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
            unique_paths = list(dict.fromkeys(mkdir_paths))
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
