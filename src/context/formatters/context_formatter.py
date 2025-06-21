"""TypedExecutionConfiguration のフォーマット処理を純粋関数として実装
"""
from dataclasses import dataclass
from typing import Optional, Union

from src.infrastructure.drivers.docker.utils.docker_naming import (
    get_docker_container_name,
    get_docker_image_name,
    get_oj_container_name,
    get_oj_image_name,
)
from src.operations.pure.formatters import format_string_simple, format_with_missing_keys

# 新設定システムをサポート
try:
    from src.configuration.config_manager import TypedExecutionConfiguration
except ImportError as e:
    raise ImportError(f"Required TypedExecutionConfiguration module not available: {e}") from e


@dataclass(frozen=True)
class ExecutionFormatData:
    """フォーマット用のイミュータブルなデータ構造"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str


def create_format_data_from_typed_config(config: 'TypedExecutionConfiguration') -> ExecutionFormatData:
    """TypedExecutionConfigurationからExecutionFormatDataを作成"""
    return ExecutionFormatData(
        command_type=config.command_type,
        language=config.language,
        contest_name=config.contest_name,
        problem_name=config.problem_name,
        env_type=config.env_type
    )


def create_format_dict_from_typed_config(config: 'TypedExecutionConfiguration') -> dict[str, str]:
    """TypedExecutionConfigurationから直接フォーマット用辞書を生成する純粋関数"""
    format_dict = {
        "command_type": config.command_type,
        "language": config.language,
        "contest_name": config.contest_name,
        "problem_name": config.problem_name,
        "env_type": config.env_type,
        "local_workspace_path": str(config.local_workspace_path),
        "contest_current_path": str(config.contest_current_path),
        "language_id": config.language_id,
        "source_file_name": config.source_file_name,
        "run_command": config.run_command,
        "language_name": config.language,
    }

    # オプショナルなパス情報
    if hasattr(config, 'contest_stock_path'):
        format_dict["contest_stock_path"] = str(config.contest_stock_path)
    if hasattr(config, 'contest_template_path'):
        format_dict["contest_template_path"] = str(config.contest_template_path)
    if hasattr(config, 'contest_temp_path'):
        format_dict["contest_temp_path"] = str(config.contest_temp_path)

    return format_dict


def create_format_dict(data: ExecutionFormatData) -> dict[str, str]:
    """ExecutionFormatDataからフォーマット用辞書を生成する純粋関数

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
        "env_type": data.env_type,
    }

    # TypedExecutionConfigurationから直接値を取得
    # env_json依存を廃止し、設定システムから直接アクセス
    format_dict.update({
        "language_name": data.language,
    })

    return format_dict


def format_template_string(template: str, data: Union[ExecutionFormatData, 'TypedExecutionConfiguration']) -> tuple[str, set]:
    """テンプレート文字列をデータでフォーマットする純粋関数

    Args:
        template: フォーマットするテンプレート文字列
        data: フォーマット用のデータ（ExecutionFormatDataまたはTypedExecutionConfiguration）

    Returns:
        Tuple[str, set]: (フォーマット済み文字列, 見つからなかったキーのセット)
    """
    # TypedExecutionConfigurationの場合
    if TypedExecutionConfiguration and isinstance(data, TypedExecutionConfiguration):
        # ConfigNodeベースのテンプレート展開を優先
        if hasattr(data, 'resolve_formatted_string'):
            try:
                formatted = data.resolve_formatted_string(template)
                return formatted, set()  # 新システムではmissing keysの詳細は取得しない
            except Exception as e:
                raise ValueError(f"文字列フォーマット解決エラー: {e}") from e

        format_dict = create_format_dict_from_typed_config(data)
    else:
        # ExecutionFormatDataの場合
        format_dict = create_format_dict(data)

    formatted, missing_list = format_with_missing_keys(template, **format_dict)
    return formatted, set(missing_list)


def validate_execution_data(data: Union[ExecutionFormatData, 'TypedExecutionConfiguration']) -> tuple[bool, Optional[str]]:
    """データの基本的なバリデーションを行う純粋関数

    Args:
        data: バリデーション対象のデータ（ExecutionFormatDataまたはTypedExecutionConfiguration）

    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    # TypedExecutionConfigurationの場合
    if TypedExecutionConfiguration and isinstance(data, TypedExecutionConfiguration):
        # 新設定システムの内部バリデーションを使用
        if hasattr(data, 'validate_execution_data'):
            return data.validate_execution_data()

        # フォールバック: 基本的なバリデーション
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

        return True, None

    # ExecutionFormatDataの場合（従来通り）
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
    # Note: ConfigurationLoader.get_language_config()を使用している場合、
    # env_jsonは既に言語固有にマージされた設定なので、言語キーの存在チェックは不要

    return True, None


def format_values_with_context_dict(values: list, context_dict: dict) -> list:
    """Format list of values with context dictionary

    Args:
        values: List of string values to format
        context_dict: Dictionary containing format variables

    Returns:
        List of formatted strings
    """
    result = []
    for value in values:
        if isinstance(value, str):
            formatted = format_string_simple(value, context_dict)
            result.append(formatted)
        else:
            result.append(str(value))

    return result


def get_docker_naming_from_data(data: Union[ExecutionFormatData, 'TypedExecutionConfiguration'],
                               dockerfile_content: Optional[str],
                               oj_dockerfile_content: Optional[str]) -> dict:
    """データからDocker命名情報を生成する純粋関数

    Args:
        data: 実行データ（ExecutionFormatDataまたはTypedExecutionConfiguration）
        dockerfile_content: Dockerfileの内容（オプション）
        oj_dockerfile_content: OJ Dockerfileの内容（オプション）

    Returns:
        dict: Docker命名情報
    """
    # 言語名を取得
    language = data.language

    # Container names are fixed (no hash)
    container_name = get_docker_container_name(language, "")
    oj_container_name = get_oj_container_name("")

    # Image names use hash if dockerfile content is provided
    image_name = get_docker_image_name(language, dockerfile_content)
    oj_image_name = get_oj_image_name(oj_dockerfile_content)

    return {
        "image_name": image_name,
        "container_name": container_name,
        "oj_image_name": oj_image_name,
        "oj_container_name": oj_container_name
    }
