"""Step実行のためのユーティリティ関数とExecutionContextクラス

このモジュールはワークフローステップの実行に必要な機能を提供する。
主な機能:
- テンプレート文字列の展開
- ExecutionContextの定義
- テスト条件の評価
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import glob
import json
import re




@dataclass
class ExecutionContext:
    """ステップ実行時のコンテキスト情報"""
    contest_name: str
    problem_name: str
    language: str
    local_workspace_path: str
    contest_current_path: str
    contest_stock_path: Optional[str] = None
    contest_template_path: Optional[str] = None
    env_type: Optional[str] = None
    source_file_name: Optional[str] = None
    language_id: Optional[str] = None
    run_command: Optional[str] = None
    contest_files: Optional[List[str]] = None
    test_files: Optional[List[str]] = None
    build_files: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result


def _contains_template_variables(text: str) -> bool:
    """テンプレート変数（{variable}）が含まれているかチェック"""
    return bool(re.search(r'\{[^}]+\}', text))


def expand_template(template: str, context) -> str:
    """テンプレート文字列の{variable}を置換する

    新設定システムと旧システムの両方に対応
    単純で予測可能な実装
    """
    if not template:
        return ""

    # TypeSafeConfigNodeManagerで展開（最優先）
    if hasattr(context, 'resolve_formatted_string'):
        try:
            return context.resolve_formatted_string(template)
        except Exception as e:
            raise ValueError(f"テンプレート解決エラー (resolve_formatted_string): {e}") from e

    # ExecutionContextAdapterの場合（新設定システムアダプター）
    if hasattr(context, 'format_string'):
        try:
            return context.format_string(template)
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
            # ファイルパターン変数の特殊処理
            if attr in ['contest_files', 'test_files', 'build_files'] and isinstance(value, list):
                # ファイルパターン配列の場合は最初のパターンを使用
                context_dict[attr] = str(value[0]) if value else ""
            else:
                context_dict[attr] = str(value)

    # テンプレート置換
    for key, value in context_dict.items():
        result = result.replace(f'{{{key}}}', value)

    return result


def evaluate_test_condition(condition: str, os_provider) -> bool:
    """test条件を評価する

    Args:
        condition: 評価するtest条件文字列
        os_provider: OSプロバイダー

    Returns:
        bool: 条件が真の場合True

    Raises:
        ValueError: test条件の評価に失敗した場合
    """
    if not condition.strip():
        return True

    try:
        # test コマンドとして実行
        if hasattr(os_provider, 'run_command'):
            result = os_provider.run_command(['test'] + condition.split())
            return result.return_code == 0
        else:
            # fallback: subprocess使用
            result = subprocess.run(['test'] + condition.split(), 
                                  capture_output=True, text=True)
            return result.returncode == 0
    except Exception as e:
        raise ValueError(f"test条件の評価に失敗: {condition}, エラー: {e}") from e


def expand_when_condition(when_condition: str, context, os_provider) -> bool:
    """when条件を展開・評価する

    Args:
        when_condition: 評価するwhen条件文字列
        context: テンプレート展開用のコンテキスト
        os_provider: OSプロバイダー

    Returns:
        bool: 条件が真の場合True
    """
    if not when_condition:
        return True

    # テンプレート展開
    expanded = expand_template(when_condition, context)

    # test条件を評価
    return evaluate_test_condition(expanded, os_provider)


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

    # ファイルパターンを実際のファイルリストに展開
    actual_files = expand_file_patterns_to_files(file_patterns, os_provider)

    if not actual_files:
        return [json_step]

    # 各ファイルに対してステップを生成
    expanded_steps = []
    for file_path in actual_files:
        step_copy = json_step.copy()
        
        # cmdの各要素でパターン変数を実際のファイルパスに置換
        if isinstance(step_copy['cmd'], list):
            step_copy['cmd'] = [arg.replace(found_pattern_var, file_path) for arg in step_copy['cmd']]
        else:
            step_copy['cmd'] = step_copy['cmd'].replace(found_pattern_var, file_path)
        
        expanded_steps.append(step_copy)

    return expanded_steps


def get_file_patterns_from_context(context, pattern_name: str, json_provider) -> List[str]:
    """コンテキストからファイルパターン配列を取得

    Args:
        context: 実行コンテキスト
        pattern_name: パターン名 ('contest_files', 'test_files', 'build_files')
        json_provider: JSONプロバイダー

    Returns:
        List[str]: ファイルパターンのリスト
    """
    # コンテキストから直接取得を試行
    if hasattr(context, pattern_name):
        patterns = getattr(context, pattern_name)
        if isinstance(patterns, list):
            return patterns
        elif isinstance(patterns, str):
            return [patterns]

    # TypeSafeConfigNodeManagerからの取得を試行
    if hasattr(context, '_root_node') and context._root_node:
        try:
            from src.context.resolver.config_resolver import resolve_config_value
            patterns = resolve_config_value(['files', pattern_name], context._root_node)
            if isinstance(patterns, list):
                return patterns
            elif isinstance(patterns, str):
                return [patterns]
        except Exception:
            pass

    # デフォルトパターンを返す
    default_patterns = {
        'contest_files': ['main.py', '*.py'],
        'test_files': ['test_*.txt', 'sample_*.txt'],
        'build_files': ['*.py', '*.cpp', '*.java']
    }
    return default_patterns.get(pattern_name, [])


def expand_file_patterns_to_files(patterns: List[str], os_provider) -> List[str]:
    """ファイルパターンを実際のファイルリストに展開

    Args:
        patterns: ファイルパターンのリスト
        os_provider: OSプロバイダー

    Returns:
        List[str]: 実際のファイルパスのリスト
    """
    files = []
    
    for pattern in patterns:
        if '*' in pattern or '?' in pattern:
            # グロブパターンの場合
            if hasattr(os_provider, 'glob'):
                matched_files = os_provider.glob(pattern)
            else:
                # fallback: 標準glob使用
                matched_files = glob.glob(pattern)
            files.extend(matched_files)
        else:
            # 通常のファイル名の場合
            files.append(pattern)
    
    # 重複を除去し、ソート
    return sorted(list(set(files)))


def create_step(json_step: Dict[str, Any], context) -> 'Step':
    """JSONからStepオブジェクトを作成

    Args:
        json_step: ステップのJSON定義
        context: 実行コンテキスト

    Returns:
        Step: 作成されたStepオブジェクト

    Raises:
        ValueError: 必須フィールドが不足している場合
    """
    from src.workflow.step.step import Step
    
    # 必須フィールドのチェック
    if 'cmd' not in json_step:
        raise ValueError("'cmd'フィールドが必須です")
    
    if 'type' not in json_step:
        raise ValueError("'type'フィールドが必須です")

    # コマンドを展開
    raw_cmd = json_step['cmd']
    expanded_cmd = [expand_template(arg, context) for arg in raw_cmd]
    
    # Stepオブジェクトを作成
    return Step.create_without_validation(
        step_type=json_step['type'],
        cmd=expanded_cmd,
        name=json_step.get('name', ''),
        allow_failure=json_step.get('allow_failure', False),
        show_output=json_step.get('show_output', True),
        max_workers=json_step.get('max_workers', 1),
        cwd=json_step.get('cwd'),
        when=json_step.get('when'),
        output_format=json_step.get('output_format'),
        format_preset=json_step.get('format_preset')
    )


def expand_file_patterns_in_text(text: str, file_patterns: Dict[str, List[str]], step_type) -> str:
    """テキスト内のファイルパターンを展開する

    新設定システムに対応したファイルパターン展開
    """
    result = text

    for pattern_name, patterns in file_patterns.items():
        placeholder = f'{{{pattern_name}}}'
        if placeholder in result and patterns:
            pattern = patterns[0]  # 最初のパターンを使用

            # ディレクトリ操作の場合はディレクトリ部分のみ
            if hasattr(step_type, 'MOVETREE') and step_type in [step_type.MOVETREE, step_type.COPYTREE] and '/' in pattern:
                pattern = pattern.split('/')[0]

            result = result.replace(placeholder, pattern)

    return result


def check_when_condition(when_condition: str, context, os_provider) -> bool:
    """when条件をチェックする（互換性のため）
    
    expand_when_conditionのエイリアス
    """
    return expand_when_condition(when_condition, context, os_provider)


def run_steps(steps_data: List[Dict[str, Any]], context, json_provider, os_provider) -> List:
    """ステップリストを実行する

    Args:
        steps_data: ステップのJSONデータリスト
        context: 実行コンテキスト
        json_provider: JSONプロバイダー
        os_provider: OSプロバイダー

    Returns:
        List[Step]: 実行されたStepオブジェクトのリスト
    """
    steps = []
    for step_data in steps_data:
        # ファイルパターンを含むステップを展開
        expanded_steps_data = expand_step_with_file_patterns(step_data, context, json_provider, os_provider)
        
        for expanded_step_data in expanded_steps_data:
            step = create_step(expanded_step_data, context)
            steps.append(step)
    
    return steps


