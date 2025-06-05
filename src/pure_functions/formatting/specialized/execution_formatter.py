"""
ExecutionContext特化のフォーマット機能

ExecutionContextで使用される専用のフォーマット処理を提供
基底レイヤーの機能を活用しつつ、特化した機能を実装
"""
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass

from ..core.string_formatter import format_with_missing_keys
from ..core.validation import validate_format_data


@dataclass(frozen=True)
class ExecutionFormatData:
    """ExecutionContext用のイミュータブルなフォーマットデータ構造"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict


def create_execution_format_dict(data: ExecutionFormatData) -> Dict[str, str]:
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
    
    # env_jsonから追加の値を取得
    if data.env_json and data.language in data.env_json:
        lang_config = data.env_json[data.language]
        
        # パス関連
        format_dict.update({
            "contest_current_path": lang_config.get("contest_current_path", "./contest_current"),
            "contest_stock_path": lang_config.get("contest_stock_path", "./contest_stock"),
            "contest_template_path": lang_config.get("contest_template_path", "./contest_template/{language_name}"),
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


def format_execution_template(template: str, data: ExecutionFormatData) -> Tuple[str, set]:
    """
    テンプレート文字列をExecutionFormatDataでフォーマットする純粋関数
    
    Args:
        template: フォーマットするテンプレート文字列
        data: フォーマット用のデータ
        
    Returns:
        Tuple[str, set]: (フォーマット済み文字列, 見つからなかったキーのセット)
    """
    format_dict = create_execution_format_dict(data)
    formatted, missing_list = format_with_missing_keys(template, **format_dict)
    return formatted, set(missing_list)


def validate_execution_format_data(data: ExecutionFormatData) -> Tuple[bool, Optional[str]]:
    """
    ExecutionFormatDataの基本的なバリデーションを行う純粋関数
    
    Args:
        data: バリデーション対象のデータ
        
    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    required_fields = [
        'command_type', 'language', 'contest_name', 
        'problem_name', 'env_type'
    ]
    
    is_valid, error = validate_format_data(data, required_fields)
    if not is_valid:
        return is_valid, error
    
    # env_jsonの検証
    if data.env_json and data.language:
        if data.language not in data.env_json:
            return False, f"Language '{data.language}' not found in env_json"
    
    return True, None


def get_docker_naming_context(data: ExecutionFormatData, 
                             dockerfile_content: Optional[str] = None,
                             oj_dockerfile_content: Optional[str] = None) -> Dict[str, str]:
    """
    ExecutionFormatDataからDocker命名コンテキストを生成する純粋関数
    
    Args:
        data: 実行データ
        dockerfile_content: Dockerfileの内容（オプション）
        oj_dockerfile_content: OJ Dockerfileの内容（オプション）
        
    Returns:
        Dict[str, str]: Docker命名情報
    """
    from src.operations.utils.docker_naming import (
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


def create_extended_format_dict(data: ExecutionFormatData, 
                               docker_context: Dict[str, str] = None,
                               additional_context: Dict[str, Any] = None) -> Dict[str, str]:
    """
    拡張されたフォーマット辞書を作成
    
    Args:
        data: 基本フォーマットデータ
        docker_context: Docker関連のコンテキスト
        additional_context: 追加のコンテキスト
        
    Returns:
        Dict[str, str]: 拡張されたフォーマット辞書
    """
    format_dict = create_execution_format_dict(data)
    
    if docker_context:
        format_dict.update(docker_context)
    
    if additional_context:
        # 文字列に変換して追加
        str_context = {k: str(v) for k, v in additional_context.items()}
        format_dict.update(str_context)
    
    return format_dict


# Backward compatibility aliases (既存コードとの互換性)
create_format_dict = create_execution_format_dict
format_template_string = format_execution_template
validate_execution_data = validate_execution_format_data
get_docker_naming_from_data = get_docker_naming_context