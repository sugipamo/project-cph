"""
バリデーション関連のユーティリティ

設定、入力、データの検証を行う純粋関数を提供
"""
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path


def validate_execution_context(
    command_type: str,
    language: str, 
    contest_name: str,
    problem_name: str,
    env_config: dict
) -> Tuple[bool, Optional[str]]:
    """
    実行コンテキストの基本的なバリデーション
    
    Args:
        command_type: コマンドタイプ
        language: プログラミング言語
        contest_name: コンテスト名
        problem_name: 問題名
        env_config: 環境設定辞書
        
    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    # 必須フィールドのチェック
    missing_fields = []
    if not command_type:
        missing_fields.append("コマンドタイプ")
    if not language:
        missing_fields.append("言語")
    if not contest_name:
        missing_fields.append("コンテスト名")
    if not problem_name:
        missing_fields.append("問題名")
        
    if missing_fields:
        return False, f"必須項目が不足: {', '.join(missing_fields)}"
        
    # 環境設定の存在チェック
    if not env_config:
        return False, "環境設定が見つかりません"
        
    # 言語サポートのチェック
    if language not in env_config:
        return False, f"言語 '{language}' は環境設定に含まれていません"

    return True, None


def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    ファイルパスの形式を検証
    
    Args:
        path: 検証するファイルパス
        
    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    if not path:
        return False, "パスが空です"
    
    if path.startswith('/') and '..' in path:
        return False, "絶対パスに '..' を含めることはできません"
    
    # 危険な文字のチェック
    dangerous_chars = ['|', ';', '&', '$', '`']
    if any(char in path for char in dangerous_chars):
        return False, f"危険な文字が含まれています: {path}"
    
    return True, None


def validate_docker_image_name(image_name: str) -> Tuple[bool, Optional[str]]:
    """
    Dockerイメージ名の形式を検証
    
    Args:
        image_name: 検証するイメージ名
        
    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    if not image_name:
        return False, "イメージ名が空です"
    
    # Docker イメージ名の形式チェック
    pattern = r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9._-]+)?$'
    if not re.match(pattern, image_name.lower()):
        return False, f"無効なイメージ名形式: {image_name}"
    
    return True, None


def validate_step_config(step_config: dict) -> Tuple[bool, List[str]]:
    """
    ステップ設定を検証
    
    Args:
        step_config: ステップ設定辞書
        
    Returns:
        Tuple[bool, List[str]]: (有効かどうか, エラーメッセージリスト)
    """
    errors = []
    required_fields = ['type', 'cmd']
    valid_types = ['shell', 'python', 'copy', 'move', 'mkdir', 'rmtree', 'remove', 'touch']
    
    # 必須フィールドのチェック
    for field in required_fields:
        if field not in step_config:
            errors.append(f"必須フィールドが不足: {field}")
    
    # ステップタイプの検証
    if 'type' in step_config and step_config['type'] not in valid_types:
        errors.append(f"無効なステップタイプ: {step_config['type']}. 有効なタイプ: {valid_types}")
    
    # コマンドの検証
    if 'cmd' in step_config and not step_config['cmd']:
        errors.append("コマンドフィールドが空です")
    
    return len(errors) == 0, errors


def validate_config_keys(config: dict, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    設定辞書が必要なキーを含んでいるかチェック
    
    Args:
        config: チェックする設定辞書
        required_keys: 必須キーのリスト
        
    Returns:
        Tuple[bool, List[str]]: (有効かどうか, 不足キーリスト)
    """
    missing_keys = [key for key in required_keys if key not in config]
    return len(missing_keys) == 0, missing_keys


def validate_environment_setup(env_config: dict, language: str, command_type: str) -> Tuple[bool, Optional[str]]:
    """
    環境設定の完全性を検証
    
    Args:
        env_config: 環境設定辞書
        language: 対象言語
        command_type: 対象コマンドタイプ
        
    Returns:
        Tuple[bool, Optional[str]]: (有効かどうか, エラーメッセージ)
    """
    # 言語の存在チェック
    if language not in env_config:
        return False, f"言語 '{language}' の設定が見つかりません"
    
    lang_config = env_config[language]
    
    # コマンドの存在チェック
    if 'commands' not in lang_config:
        return False, f"言語 '{language}' にコマンド設定がありません"
    
    commands = lang_config['commands']
    if command_type not in commands:
        return False, f"言語 '{language}' にコマンド '{command_type}' の設定がありません"
    
    command_config = commands[command_type]
    
    # ステップの存在チェック
    if 'steps' not in command_config:
        return False, f"コマンド '{command_type}' にステップ設定がありません"
    
    steps = command_config['steps']
    if not isinstance(steps, list) or len(steps) == 0:
        return False, f"コマンド '{command_type}' のステップが空です"
    
    return True, None


def is_script_file(file_path: str, script_extensions: List[str] = None) -> bool:
    """
    ファイルがスクリプトファイルかどうかを判定
    
    Args:
        file_path: チェックするファイルパス
        script_extensions: スクリプトファイルの拡張子リスト
        
    Returns:
        スクリプトファイルかどうか
    """
    if script_extensions is None:
        script_extensions = ['.py', '.js', '.sh', '.rb', '.go', '.rs', '.cpp', '.c', '.java']
    
    return any(file_path.endswith(ext) for ext in script_extensions)