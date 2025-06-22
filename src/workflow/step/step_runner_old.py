"""シンプルなステップ実行システム

設計原則:
1. 純粋関数でテストしやすく
2. when条件は実行時に1stepずつ評価
3. 明確なエラーハンドリング
4. 最小限の依存関係
"""
import copy
import glob
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# 新設定システムとの統合
from .step import Step, StepType


@dataclass
class ExecutionContext:
    """実行に必要な最小限の情報"""
    # 基本情報
    contest_name: str
    problem_name: str
    language: str

    # パス情報
    local_workspace_path: str
    contest_current_path: str
    contest_stock_path: str = ""
    contest_template_path: str = ""

    # ファイル情報
    source_file_name: str = ""
    language_id: str = ""
    run_command: str = ""

    # 前回値（バックアップ用）
    old_contest_name: str = ""
    old_problem_name: str = ""

    # その他
    file_patterns: Dict[str, List[str]] = None

    def to_dict(self) -> Dict[str, str]:
        """文字列置換用の辞書を返す"""
        result = {
            'contest_name': self.contest_name,
            'problem_name': self.problem_name,
            'old_contest_name': self.old_contest_name,
            'old_problem_name': self.old_problem_name,
            'language': self.language,
            'language_name': self.language,  # エイリアス
            'local_workspace_path': self.local_workspace_path,
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
                    # 最初のパターンを使用
                    pattern = patterns[0]
                    if pattern_name == 'test_files' and '/' in pattern:
                        # "test/*.in" -> "test" (ディレクトリ部分のみ)
                        result[pattern_name] = pattern.split('/')[0]
                    else:
                        # contest_filesなどはそのまま使用
                        result[pattern_name] = pattern

        return result


@dataclass
class StepResult:
    """ステップ実行結果"""
    success: bool
    step: Step
    skipped: bool = False
    error_message: str = ""


def run_steps(json_steps: List[Dict[str, Any]], context, os_provider, json_provider) -> List[StepResult]:
    """JSONステップを順次実行する（メイン関数）

    Args:
        json_steps: 実行するステップのJSONリスト
        context: 実行コンテキスト
        os_provider: OSプロバイダー（依存性注入用）
        json_provider: JSONプロバイダー（依存性注入用）

    Returns:
        List[StepResult]: 各ステップの実行結果
    """
    if os_provider is None:
        raise ValueError("os_provider parameter is required")

    results = []

    for i, json_step in enumerate(json_steps):
        try:
            # ファイルパターンを含むステップを展開
            expanded_steps = expand_step_with_file_patterns(json_step, context, json_provider, os_provider)

            for step_json in expanded_steps:
                # ステップを作成
                step = create_step(step_json, context)

                # when条件をチェック
                should_run, check_error = check_when_condition(step.when, context, os_provider)

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


def create_step(json_step: Dict[str, Any], context) -> Step:
    """JSONからStepオブジェクトを作成する"""
    step_type = StepType(json_step['type'])

    # コマンドを展開
    raw_cmd = json_step['cmd']
    expanded_cmd = [expand_template(arg, context) for arg in raw_cmd]

    # ファイルパターンがある場合は展開
    if context.file_patterns and step_type in [StepType.COPY, StepType.COPYTREE, StepType.MOVE, StepType.MOVETREE]:
        expanded_cmd = expand_file_patterns_in_cmd(expanded_cmd, context.file_patterns, step_type)

    # cwdを展開
    cwd = None
    if 'cwd' in json_step:
        cwd = expand_template(json_step['cwd'], context)

    # オプショナルフィールドの安全な取得（.get()使用禁止のため条件分岐）
    allow_failure = False
    if 'allow_failure' in json_step:
        allow_failure = json_step['allow_failure']

    show_output = False
    if 'show_output' in json_step:
        show_output = json_step['show_output']

    when_condition = None
    if 'when' in json_step:
        when_condition = json_step['when']

    name = f"Step {step_type.value}"
    if 'name' in json_step:
        name = json_step['name']

    return Step(
        type=step_type,
        cmd=expanded_cmd,
        allow_failure=allow_failure,
        show_output=show_output,
        cwd=cwd,
        when=when_condition,  # 展開せずそのまま保持
        name=expand_template(name, context)
    )


def check_when_condition(when_clause: Optional[str], context, os_provider) -> Tuple[bool, Optional[str]]:
    """when条件をチェックする"""
    if not when_clause:
        return True, None

    # テンプレート変数を展開
    expanded = expand_template(when_clause, context)

    # ファイルパターンを展開
    if context.file_patterns:
        expanded = expand_file_patterns_in_when(expanded, context.file_patterns)

    # test条件を評価
    return evaluate_test_condition(expanded, os_provider)


def _contains_template_variables(text: str) -> bool:
    """テンプレート変数（{variable}）が含まれているかチェック"""
    import re
    return bool(re.search(r'\{[^}]+\}', text))


def expand_template(template: str, context) -> str:
    """テンプレート文字列の{variable}を置換する

    新設定システムと旧システムの両方に対応
    解決済みテンプレートの再解決を防ぐ
    """
    if not template:
        return ""

    # 解決済みマーカーがある場合は再解決をスキップ
    resolved_marker = "$$RESOLVED$$"
    if resolved_marker in template:
        return template.replace(resolved_marker, "")

    # TypeSafeConfigNodeManagerで展開（最優先）
    if hasattr(context, 'resolve_formatted_string'):
        try:
            result = context.resolve_formatted_string(template)
            # テンプレート変数が含まれていない場合のみマーカー追加
            if not _contains_template_variables(result):
                result = f"{resolved_marker}{result}"
            # 最終結果でマーカーを除去
            return result.replace(resolved_marker, "")
        except Exception as e:
            raise ValueError(f"テンプレート解決エラー (resolve_formatted_string): {e}") from e

    # ExecutionContextAdapterの場合（新設定システムアダプター）
    if hasattr(context, 'format_string'):
        try:
            result = context.format_string(template)
            # テンプレート変数が含まれていない場合のみマーカー追加
            if not _contains_template_variables(result):
                result = f"{resolved_marker}{result}"
            return result
        except Exception as e:
            raise ValueError(f"テンプレート解決エラー (format_string): {e}") from e

    # SimpleExecutionContext（step_runner.py内のExecutionContext）の場合
    if hasattr(context, 'to_dict'):
        result = template
        for key, value in context.to_dict().items():
            # Pathオブジェクトも文字列に変換
            if value is None:
                raise ValueError(f"Value for key '{key}' is None")
            str_value = str(value)
            result = result.replace(f'{{{key}}}', str_value)
        # テンプレート変数が含まれていない場合のみマーカー追加
        if not _contains_template_variables(result):
            result = f"{resolved_marker}{result}"
        return result

    # その他のコンテキストタイプの場合（基本的な属性ベース展開）
    result = template
    context_dict = {}

    # 共通属性を取得（ファイルパターン変数を追加）
    common_attrs = ['contest_name', 'problem_name', 'language', 'env_type', 'command_type',
                   'local_workspace_path', 'contest_current_path', 'contest_stock_path',
                   'contest_template_path', 'source_file_name', 'language_id', 'run_command',
                   'contest_files', 'test_files', 'build_files']

    for attr in common_attrs:
        if hasattr(context, attr):
            value = getattr(context, attr)
            if value is None:
                raise ValueError(f"Value for attribute '{attr}' is None")

            # ファイルパターン変数の特殊処理
            if attr in ['contest_files', 'test_files', 'build_files'] and isinstance(value, list):
                # ファイルパターン配列の場合は最初のパターンを使用
                context_dict[attr] = str(value[0]) if value else ""
            else:
                context_dict[attr] = str(value)

    # テンプレート置換
    for key, value in context_dict.items():
        result = result.replace(f'{{{key}}}', value)

    # テンプレート変数が含まれていない場合のみマーカー追加
    if not _contains_template_variables(result):
        result = f"{resolved_marker}{result}"
    
    return result


def expand_step_with_file_patterns(json_step: Dict[str, Any], context, json_provider, os_provider) -> List[Dict[str, Any]]:
    """ファイルパターンを含むステップを個別ステップに展開

    Args:
        json_step: 展開するステップのJSON
        context: 実行コンテキスト
        json_provider: JSONプロバイダー
        os_provider: OSプロバイダー

    Returns:
        List[Dict[str, Any]]: 展開されたステップのJSONリスト
    """
    cmd = json_step['cmd']
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)

    # ファイルパターン変数をチェック
    file_pattern_vars = ['{contest_files}', '{test_files}', '{build_files}']
    found_pattern_var = None

    for pattern_var in file_pattern_vars:
        if pattern_var in cmd_str:
            found_pattern_var = pattern_var
            break

    if not found_pattern_var:
        return [json_step]

    # ファイルパターンを取得
    pattern_name = found_pattern_var.strip('{}')
    file_patterns = get_file_patterns_from_context(context, pattern_name, json_provider)

    if not file_patterns:
        return [json_step]

    # ファイルリストを展開
    base_path = get_base_path_for_pattern(json_step, context, found_pattern_var)
    expanded_files = expand_file_patterns_to_files(file_patterns, base_path, os_provider)

    if not expanded_files:
        return [json_step]

    # 各ファイルに対して個別ステップを生成
    expanded_steps = []
    for file_name in expanded_files:
        new_step = copy.deepcopy(json_step)
        new_step['cmd'] = [arg.replace(found_pattern_var, file_name) for arg in new_step['cmd']]

        # ステップ名を更新
        if 'name' in new_step:
            new_step['name'] = f"{new_step['name']} - {file_name}"

        expanded_steps.append(new_step)

    return expanded_steps


def get_file_patterns_from_context(context, pattern_name: str, json_provider) -> List[str]:
    """コンテキストからファイルパターンを取得"""
    if hasattr(context, 'file_patterns') and context.file_patterns:
        if pattern_name not in context.file_patterns:
            raise ValueError(f"Required pattern '{pattern_name}' not found in file_patterns")
        return context.file_patterns[pattern_name]

    # 属性から直接取得を試みる
    if hasattr(context, pattern_name):
        value = getattr(context, pattern_name)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed_json = json_provider.loads(value)
                return parsed_json
            except (ValueError, TypeError) as e:
                # エラーログを出力してエラーを再発生
                from infrastructure.logger import Logger
                logger = Logger()
                logger.error(f"Failed to parse JSON value: {value}, error: {e}")
                raise
        else:
            raise ValueError(f"Pattern '{pattern_name}' found but has unsupported type: {type(value)}")

    raise ValueError(f"Required pattern '{pattern_name}' not found in context")


def get_base_path_for_pattern(json_step: Dict[str, Any], context, pattern_var: str) -> str:
    """ファイルパターンのベースパスを取得"""
    cmd = json_step['cmd']

    # コマンドからパターンが使われている引数を探す
    for arg in cmd:
        if pattern_var in arg:
            # パターン変数を除いたパス部分を抽出
            path_part = arg.replace(pattern_var, '').rstrip('/')
            if path_part:
                return expand_template(path_part, context)

    # デフォルトはカレントパス
    return getattr(context, 'contest_current_path', '.')


def expand_file_patterns_to_files(patterns: List[str], base_path: str, os_provider) -> List[str]:
    """ファイルパターンを実際のファイルリストに展開"""
    expanded_files = []

    for pattern in patterns:
        if '*' in pattern or '?' in pattern:
            # グロブパターンでマッチング
            full_pattern = os_provider.path_join(base_path, pattern)
            matches = glob.glob(full_pattern)
            for match in matches:
                if os_provider.path_isfile(match):
                    expanded_files.append(os_provider.path_basename(match))
        else:
            # 直接ファイル指定
            full_path = os_provider.path_join(base_path, pattern)
            if os_provider.path_exists(full_path) or not os_provider.path_exists(base_path):
                # ファイルが存在するか、ベースパスが存在しない場合は含める
                expanded_files.append(pattern)

    # 重複を除去して順序を保持
    seen = set()
    result = []
    for f in expanded_files:
        if f not in seen:
            seen.add(f)
            result.append(f)

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


def expand_template_with_new_system(template: str, new_config, operation_type: Optional[str]) -> str:
    """新設定システムを使用したテンプレート展開

    Args:
        template: 展開するテンプレート
        new_config: 新設定システムの設定
        operation_type: 操作タイプ（ファイルパターン展開用）

    Returns:
        展開された文字列
    """
    # TypeSafeConfigNodeManagerで展開
    if hasattr(new_config, 'resolve_formatted_string'):
        return new_config.resolve_formatted_string(template)
    # 他の場合はそのまま返す
    return template


def evaluate_test_condition(test_command: str, os_provider) -> Tuple[bool, Optional[str]]:
    """test条件を評価する（複合条件もサポート）"""
    if os_provider is None:
        raise ValueError("os_provider parameter is required")

    # 複合条件（&&）をサポート
    if ' && ' in test_command:
        conditions = test_command.split(' && ')
        for condition in conditions:
            result, error = evaluate_test_condition(condition.strip(), os_provider)
            if error:
                return False, error
            if not result:
                return False, None
        return True, None

    if not test_command.startswith('test '):
        return False, "Condition must start with 'test'"

    parts = test_command.split()
    if len(parts) < 3:
        return False, "Invalid test command format"

    # 'test'を除去
    args = parts[1:]

    # 否定チェック
    negate = False
    if args[0] == '!' or args[0] == '\\!':
        negate = True
        args = args[1:]

    # 文字列比較の場合: test 'string1' operator 'string2'
    if len(args) >= 3 and args[1] in ['=', '!=', '==']:
        try:
            left = args[0].strip("'\"")
            operator = args[1]
            right = args[2].strip("'\"")

            if operator in ['=', '==']:
                result = left == right
            elif operator == '!=':
                result = left != right
            else:
                return False, f"Unsupported string operator: {operator}"

            # 否定適用
            final_result = not result if negate else result
            return final_result, None
        except Exception as e:
            # フォールバック処理は禁止、必要なエラーを見逃すことになる
            raise ValueError(f"Error evaluating string condition: {e}") from e

    if len(args) < 2:
        return False, "Missing test arguments"

    flag, value = args[0], args[1]

    try:
        # 条件評価
        if flag == '-d':
            result = os_provider.path_isdir(value)
        elif flag == '-f':
            result = os_provider.path_isfile(value)
        elif flag == '-e':
            result = os_provider.path_exists(value)
        elif flag == '-n':
            # 文字列が非空かチェック
            # シングルクォートを除去
            clean_value = value.strip("'\"")
            result = clean_value != ""
        else:
            return False, f"Unsupported test flag: {flag}"

        # 否定適用
        final_result = not result if negate else result
        return final_result, None

    except Exception as e:
        # フォールバック処理は禁止、必要なエラーを見逃すことになる
        raise ValueError(f"Error evaluating condition: {e}") from e


def execute_step_mock(step: Step) -> Tuple[bool, str]:
    """ステップ実行のモック（テスト用）"""
    # TODO: 実際の実行ロジックに置き換える
    return True, ""
