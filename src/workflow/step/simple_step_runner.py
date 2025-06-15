"""シンプルなステップ実行システム

設計原則:
1. 純粋関数でテストしやすく
2. when条件は実行時に1stepずつ評価
3. 明確なエラーハンドリング
4. 最小限の依存関係
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# 新設定システムとの統合
from src.configuration import ExecutionConfiguration as NewExecutionConfiguration
from src.configuration.expansion.template_expander import TemplateExpander

from .step import Step, StepType


@dataclass
class ExecutionContext:
    """実行に必要な最小限の情報"""
    # 基本情報
    contest_name: str
    problem_name: str
    language: str

    # パス情報
    workspace_path: str
    contest_current_path: str
    contest_stock_path: str = ""
    contest_template_path: str = ""

    # ファイル情報
    source_file_name: str = ""
    language_id: str = ""
    run_command: str = ""

    # その他
    file_patterns: Dict[str, List[str]] = None

    def to_dict(self) -> Dict[str, str]:
        """文字列置換用の辞書を返す"""
        result = {
            'contest_name': self.contest_name,
            'problem_name': self.problem_name,
            'language': self.language,
            'language_name': self.language,  # エイリアス
            'workspace_path': self.workspace_path,
            'contest_current_path': self.contest_current_path,
            'contest_stock_path': self.contest_stock_path,
            'contest_template_path': self.contest_template_path,
            'source_file_name': self.source_file_name,
            'language_id': self.language_id,
            'run_command': self.run_command,
        }

        # ファイルパターンをテンプレート変数として追加
        if self.file_patterns:
            for pattern_name, patterns in self.file_patterns.items():
                if patterns:
                    # 最初のパターンを使用（ディレクトリ部分を抽出）
                    pattern = patterns[0]
                    if '/' in pattern:
                        # "test/*.in" -> "test"
                        result[pattern_name] = pattern.split('/')[0]
                    else:
                        result[pattern_name] = pattern

        return result


@dataclass
class StepResult:
    """ステップ実行結果"""
    success: bool
    step: Step
    skipped: bool = False
    error_message: str = ""


def run_steps(json_steps: List[Dict[str, Any]], context: ExecutionContext) -> List[StepResult]:
    """JSONステップを順次実行する（メイン関数）

    Args:
        json_steps: 実行するステップのJSONリスト
        context: 実行コンテキスト

    Returns:
        List[StepResult]: 各ステップの実行結果
    """
    results = []

    for i, json_step in enumerate(json_steps):
        try:
            # ステップを作成
            step = create_step(json_step, context)

            # when条件をチェック
            should_run, check_error = check_when_condition(step.when, context)

            if check_error:
                results.append(StepResult(False, step, False, f"When condition error: {check_error}"))
                continue

            if not should_run:
                results.append(StepResult(True, step, True, "Skipped by when condition"))
                continue

            # ステップ実行（実際の実行は別途実装）
            success, error = execute_step_mock(step)  # TODO: 実際の実行ロジックに置き換え
            results.append(StepResult(success, step, False, error))

        except Exception as e:
            # エラーの場合は空のステップを作成
            error_step = Step(StepType.SHELL, ["error"], name=f"Step {i}")
            results.append(StepResult(False, error_step, False, str(e)))

    return results


def create_step(json_step: Dict[str, Any], context: ExecutionContext) -> Step:
    """JSONからStepオブジェクトを作成する"""
    step_type = StepType(json_step['type'])

    # コマンドを展開
    raw_cmd = json_step.get('cmd', [])
    expanded_cmd = [expand_template(arg, context) for arg in raw_cmd]

    # ファイルパターンがある場合は展開
    if context.file_patterns and step_type in [StepType.COPY, StepType.COPYTREE, StepType.MOVE, StepType.MOVETREE]:
        expanded_cmd = expand_file_patterns_in_cmd(expanded_cmd, context.file_patterns, step_type)

    # cwdを展開
    cwd = json_step.get('cwd')
    if cwd:
        cwd = expand_template(cwd, context)

    return Step(
        type=step_type,
        cmd=expanded_cmd,
        allow_failure=json_step.get('allow_failure', False),
        show_output=json_step.get('show_output', False),
        cwd=cwd,
        when=json_step.get('when'),  # 展開せずそのまま保持
        name=expand_template(json_step.get('name', ''), context)
    )


def check_when_condition(when_clause: Optional[str], context: ExecutionContext) -> Tuple[bool, Optional[str]]:
    """when条件をチェックする"""
    if not when_clause:
        return True, None

    # テンプレート変数を展開
    expanded = expand_template(when_clause, context)

    # ファイルパターンを展開
    if context.file_patterns:
        expanded = expand_file_patterns_in_when(expanded, context.file_patterns)

    # test条件を評価
    return evaluate_test_condition(expanded)


def expand_template(template: str, context: ExecutionContext) -> str:
    """テンプレート文字列の{variable}を置換する

    新設定システムと旧システムの両方に対応
    """
    if not template:
        return ""

    # 新設定システム（NewExecutionConfiguration）の場合
    if isinstance(context, NewExecutionConfiguration):
        expander = TemplateExpander(context)
        return expander.expand_all(template)

    # ExecutionContextAdapterの場合（新設定システムアダプター）
    if hasattr(context, 'format_string'):
        return context.format_string(template)

    # 従来システム（ExecutionContext）の場合
    result = template
    for key, value in context.to_dict().items():
        # Pathオブジェクトも文字列に変換
        str_value = str(value) if value is not None else ""
        result = result.replace(f'{{{key}}}', str_value)

    return result


def expand_file_patterns_in_cmd(cmd: List[str], file_patterns: Dict[str, List[str]], step_type: StepType) -> List[str]:
    """コマンド内のファイルパターンを展開する"""
    result = []
    for arg in cmd:
        expanded = expand_file_patterns_in_text(arg, file_patterns, step_type)
        result.append(expanded)
    return result


def expand_file_patterns_in_when(when_text: str, file_patterns: Dict[str, List[str]]) -> str:
    """when条件内のファイルパターンを展開する"""
    return expand_file_patterns_in_text(when_text, file_patterns, None)


def expand_file_patterns_in_text(text: str, file_patterns: Dict[str, List[str]], step_type: Optional[StepType]) -> str:
    """テキスト内のファイルパターンを展開する

    新設定システムに対応したファイルパターン展開
    """
    result = text

    for pattern_name, patterns in file_patterns.items():
        placeholder = f'{{{pattern_name}}}'
        if placeholder in result and patterns:
            pattern = patterns[0]  # 最初のパターンを使用

            # ディレクトリ操作の場合はディレクトリ部分のみ
            if step_type in [StepType.MOVETREE, StepType.COPYTREE] and '/' in pattern:
                pattern = pattern.split('/')[0]

            result = result.replace(placeholder, pattern)

    return result


def expand_template_with_new_system(template: str, new_config: NewExecutionConfiguration, operation_type: Optional[str] = None) -> str:
    """新設定システムを使用したテンプレート展開

    Args:
        template: 展開するテンプレート
        new_config: 新設定システムの設定
        operation_type: 操作タイプ（ファイルパターン展開用）

    Returns:
        展開された文字列
    """
    expander = TemplateExpander(new_config)
    return expander.expand_all(template, operation_type)


def evaluate_test_condition(test_command: str) -> Tuple[bool, Optional[str]]:
    """test条件を評価する"""
    import os

    if not test_command.startswith('test '):
        return False, "Condition must start with 'test'"

    parts = test_command.split()
    if len(parts) < 3:
        return False, "Invalid test command format"

    # 'test'を除去
    args = parts[1:]

    # 否定チェック
    negate = False
    if args[0] == '!':
        negate = True
        args = args[1:]

    if len(args) < 2:
        return False, "Missing test arguments"

    flag, path = args[0], args[1]

    try:
        # 条件評価
        if flag == '-d':
            result = os.path.isdir(path)
        elif flag == '-f':
            result = os.path.isfile(path)
        elif flag == '-e':
            result = os.path.exists(path)
        else:
            return False, f"Unsupported test flag: {flag}"

        # 否定適用
        final_result = not result if negate else result
        return final_result, None

    except Exception as e:
        return False, f"Error evaluating condition: {e}"


def execute_step_mock(step: Step) -> Tuple[bool, str]:
    """ステップ実行のモック（テスト用）"""
    # TODO: 実際の実行ロジックに置き換える
    print(f"Executing: {step.name or step.type.value} - {' '.join(step.cmd)}")
    return True, ""
