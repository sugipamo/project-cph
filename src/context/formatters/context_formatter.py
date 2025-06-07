"""
ExecutionContext のフォーマット処理を純粋関数として実装
"""
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ExecutionFormatData:
    """フォーマット用のイミュータブルなデータ構造"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict
    previous_contest_name: Optional[str] = None
    previous_problem_name: Optional[str] = None


def create_format_dict(data: ExecutionFormatData) -> Dict[str, str]:
    """
    ExecutionFormatDataからフォーマット用辞書を生成する純粋関数
    
    Args:
        data: フォーマット用のデータ
        
    Returns:
        Dict[str, str]: フォーマット用のキーと値の辞書
    """
    # 基本的な値
    format_dict = {
        "command_type": data.command_type,
        "language": data.language,
        "contest_name": data.contest_name,
        "problem_name": data.problem_name,
        "problem_id": data.problem_name,  # 互換性のため
        "env_type": data.env_type,
    }
    
    # previous情報を追加（Noneの場合もそのまま設定）
    format_dict.update({
        "previous_contest_name": data.previous_contest_name,
        "previous_problem_id": data.previous_problem_name,
    })
    
    # env_jsonから追加の値を取得
    if data.env_json and data.language in data.env_json:
        lang_config = data.env_json[data.language]
        
        # パス関連
        format_dict.update({
            "contest_current_path": lang_config.get("contest_current_path", "./contest_current"),
            "contest_stock_path": lang_config.get("contest_stock_path", "./contest_stock"),
            "contest_template_path": lang_config.get("contest_template_path", "./contest_template"),
            "contest_temp_path": lang_config.get("contest_temp_path", "./.temp"),
            "workspace_path": lang_config.get("workspace_path", "./workspace"),
        })
        
        # その他の値
        format_dict.update({
            "language_id": lang_config.get("language_id", ""),
            "source_file_name": lang_config.get("source_file_name", "main.py"),
            "language_name": data.language,
        })
    
    return format_dict


def format_template_string(template: str, data: ExecutionFormatData) -> Tuple[str, set]:
    """
    テンプレート文字列をExecutionFormatDataでフォーマットする純粋関数
    
    Args:
        template: フォーマットするテンプレート文字列
        data: フォーマット用のデータ
        
    Returns:
        Tuple[str, set]: (フォーマット済み文字列, 見つからなかったキーのセット)
    """
    from src.utils.formatters import format_with_missing_keys
    format_dict = create_format_dict(data)
    formatted, missing_list = format_with_missing_keys(template, **format_dict)
    return formatted, set(missing_list)


def validate_execution_data(data: ExecutionFormatData) -> Tuple[bool, Optional[str]]:
    """
    ExecutionFormatDataの基本的なバリデーションを行う純粋関数
    
    Args:
        data: バリデーション対象のデータ
        
    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    # 必須フィールドのチェック
    if not data.command_type:
        return False, "command_type is required"
    
    if not data.language:
        return False, "language is required"
    
    if not data.contest_name:
        return False, "contest_name is required"
    
    if not data.problem_name:
        return False, "problem_name is required"
    
    if not data.env_type:
        return False, "env_type is required"
    
    # env_jsonの検証
    if data.env_json and data.language:
        if data.language not in data.env_json:
            return False, f"Language '{data.language}' not found in env_json"
    
    return True, None


def format_values_with_context_dict(values: list, context_dict: dict) -> list:
    """
    Format list of values with context dictionary
    
    Args:
        values: List of string values to format
        context_dict: Dictionary containing format variables
        
    Returns:
        List of formatted strings
    """
    from src.utils.formatters import format_string_simple as format_string_pure
    
    result = []
    for value in values:
        if isinstance(value, str):
            formatted = format_string_pure(value, context_dict)
            result.append(formatted)
        else:
            result.append(str(value))
    
    return result


def get_docker_naming_from_data(data: ExecutionFormatData, 
                               dockerfile_content: Optional[str] = None,
                               oj_dockerfile_content: Optional[str] = None) -> dict:
    """
    ExecutionFormatDataからDocker命名情報を生成する純粋関数
    
    Args:
        data: 実行データ
        dockerfile_content: Dockerfileの内容（オプション）
        oj_dockerfile_content: OJ Dockerfileの内容（オプション）
        
    Returns:
        dict: Docker命名情報
    """
    from src.infrastructure.drivers.docker.utils.docker_naming import (
        get_docker_image_name, get_docker_container_name,
        get_oj_image_name, get_oj_container_name
    )
    
    # Container names are fixed (no hash)
    container_name = get_docker_container_name(data.language)
    oj_container_name = get_oj_container_name()
    
    # Image names use hash if dockerfile content is provided
    image_name = get_docker_image_name(data.language, dockerfile_content)
    oj_image_name = get_oj_image_name(oj_dockerfile_content)
    
    return {
        "image_name": image_name,
        "container_name": container_name,
        "oj_image_name": oj_image_name,
        "oj_container_name": oj_container_name
    }