"""
システム情報管理の純粋関数実装
"""
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from pathlib import Path


@dataclass(frozen=True)
class SystemInfo:
    """システム情報の不変データクラス"""
    command: Optional[str] = None
    language: Optional[str] = None
    env_type: Optional[str] = None
    contest_name: Optional[str] = None
    problem_name: Optional[str] = None
    env_json: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "command": self.command,
            "language": self.language,
            "env_type": self.env_type,
            "contest_name": self.contest_name,
            "problem_name": self.problem_name,
            "env_json": self.env_json
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemInfo':
        """辞書から作成"""
        return cls(
            command=data.get("command"),
            language=data.get("language"),
            env_type=data.get("env_type"),
            contest_name=data.get("contest_name"),
            problem_name=data.get("problem_name"),
            env_json=data.get("env_json")
        )


@dataclass(frozen=True)
class FileContent:
    """ファイル内容の不変データクラス"""
    content: str
    exists: bool
    path: str
    encoding: str = "utf-8"


@dataclass(frozen=True)
class SystemInfoResult:
    """システム情報操作結果の不変データクラス"""
    info: Optional[SystemInfo]
    success: bool
    errors: list
    warnings: list
    
    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])


def create_default_system_info_pure() -> SystemInfo:
    """
    デフォルトのシステム情報を作成する純粋関数
    
    Returns:
        SystemInfo: デフォルトのシステム情報
    """
    return SystemInfo(
        command=None,
        language=None,
        env_type=None,
        contest_name=None,
        problem_name=None,
        env_json=None
    )


def parse_system_info_from_json_pure(json_content: str) -> SystemInfoResult:
    """
    JSON文字列からシステム情報を解析する純粋関数
    
    Args:
        json_content: JSON形式の文字列
        
    Returns:
        SystemInfoResult: 解析結果
    """
    try:
        data = json.loads(json_content)
        info = SystemInfo.from_dict(data)
        return SystemInfoResult(
            info=info,
            success=True,
            errors=[],
            warnings=[]
        )
    except json.JSONDecodeError as e:
        return SystemInfoResult(
            info=None,
            success=False,
            errors=[f"Invalid JSON format: {str(e)}"],
            warnings=[]
        )
    except Exception as e:
        return SystemInfoResult(
            info=None,
            success=False,
            errors=[f"Error parsing system info: {str(e)}"],
            warnings=[]
        )


def load_system_info_from_content_pure(file_content: Optional[FileContent]) -> SystemInfoResult:
    """
    ファイル内容からシステム情報を読み込む純粋関数
    
    Args:
        file_content: ファイル内容（Noneの場合はファイルが存在しない）
        
    Returns:
        SystemInfoResult: 読み込み結果
    """
    if not file_content or not file_content.exists:
        # ファイルが存在しない場合はデフォルト情報を返す
        default_info = create_default_system_info_pure()
        return SystemInfoResult(
            info=default_info,
            success=True,
            errors=[],
            warnings=["System info file not found, using defaults"]
        )
    
    if not file_content.content.strip():
        # 空ファイルの場合はデフォルト情報を返す
        default_info = create_default_system_info_pure()
        return SystemInfoResult(
            info=default_info,
            success=True,
            errors=[],
            warnings=["System info file is empty, using defaults"]
        )
    
    return parse_system_info_from_json_pure(file_content.content)


def serialize_system_info_to_json_pure(info: SystemInfo, indent: int = 2) -> str:
    """
    システム情報をJSON文字列にシリアライズする純粋関数
    
    Args:
        info: システム情報
        indent: JSONのインデント
        
    Returns:
        JSON文字列
    """
    try:
        return json.dumps(info.to_dict(), ensure_ascii=False, indent=indent)
    except Exception as e:
        raise ValueError(f"Failed to serialize system info: {str(e)}")


def update_system_info_pure(
    current_info: SystemInfo,
    updates: Dict[str, Any]
) -> SystemInfo:
    """
    システム情報を更新する純粋関数
    
    Args:
        current_info: 現在のシステム情報
        updates: 更新する値の辞書
        
    Returns:
        SystemInfo: 更新されたシステム情報
    """
    current_dict = current_info.to_dict()
    
    # 有効なフィールドのみ更新
    valid_fields = {
        "command", "language", "env_type", 
        "contest_name", "problem_name", "env_json"
    }
    
    for key, value in updates.items():
        if key in valid_fields:
            current_dict[key] = value
    
    return SystemInfo.from_dict(current_dict)


def merge_system_info_pure(
    base_info: SystemInfo,
    override_info: SystemInfo,
    merge_env_json: bool = True
) -> SystemInfo:
    """
    2つのシステム情報をマージする純粋関数
    
    Args:
        base_info: ベースとなるシステム情報
        override_info: 上書きするシステム情報
        merge_env_json: env_jsonをマージするかどうか
        
    Returns:
        SystemInfo: マージされたシステム情報
    """
    base_dict = base_info.to_dict()
    override_dict = override_info.to_dict()
    
    # None以外の値で上書き
    for key, value in override_dict.items():
        if value is not None:
            if key == "env_json" and merge_env_json:
                # env_jsonは深いマージ
                base_env = base_dict.get("env_json") or {}
                override_env = value or {}
                merged_env = {**base_env, **override_env}
                base_dict[key] = merged_env
            else:
                base_dict[key] = value
    
    return SystemInfo.from_dict(base_dict)


def validate_system_info_pure(info: SystemInfo) -> list:
    """
    システム情報の妥当性を検証する純粋関数
    
    Args:
        info: 検証対象のシステム情報
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    # 環境タイプの検証
    valid_env_types = {"local", "docker", "wsl"}
    if info.env_type and info.env_type not in valid_env_types:
        errors.append(f"Invalid env_type: {info.env_type}. Must be one of {valid_env_types}")
    
    # 言語の検証（基本的な）
    valid_languages = {"python", "rust", "cpp", "java", "javascript", "go"}
    if info.language and info.language not in valid_languages:
        errors.append(f"Potentially unsupported language: {info.language}")
    
    # コンテスト名の検証
    if info.contest_name and not isinstance(info.contest_name, str):
        errors.append("contest_name must be a string")
    
    # 問題名の検証
    if info.problem_name and not isinstance(info.problem_name, str):
        errors.append("problem_name must be a string")
    
    # env_jsonの基本検証
    if info.env_json is not None and not isinstance(info.env_json, dict):
        errors.append("env_json must be a dictionary")
    
    return errors


def extract_contest_info_pure(info: SystemInfo) -> Dict[str, Optional[str]]:
    """
    システム情報からコンテスト関連情報を抽出する純粋関数
    
    Args:
        info: システム情報
        
    Returns:
        コンテスト情報の辞書
    """
    return {
        "contest_name": info.contest_name,
        "problem_name": info.problem_name,
        "language": info.language,
        "env_type": info.env_type
    }


def extract_execution_info_pure(info: SystemInfo) -> Dict[str, Any]:
    """
    システム情報から実行関連情報を抽出する純粋関数
    
    Args:
        info: システム情報
        
    Returns:
        実行情報の辞書
    """
    execution_info = {
        "command": info.command,
        "language": info.language,
        "env_type": info.env_type,
        "env_json": info.env_json
    }
    
    # env_jsonから実行設定を抽出
    if info.env_json and info.language:
        language_config = info.env_json.get(info.language, {})
        if "commands" in language_config:
            execution_info["available_commands"] = list(language_config["commands"].keys())
    
    return execution_info


def filter_system_info_fields_pure(
    info: SystemInfo, 
    include_fields: Optional[list] = None,
    exclude_fields: Optional[list] = None
) -> Dict[str, Any]:
    """
    システム情報から指定されたフィールドをフィルタリングする純粋関数
    
    Args:
        info: システム情報
        include_fields: 含めるフィールドのリスト（Noneの場合は全て）
        exclude_fields: 除外するフィールドのリスト
        
    Returns:
        フィルタリングされた辞書
    """
    result = info.to_dict()
    
    if include_fields is not None:
        # 指定されたフィールドのみ含める
        result = {k: v for k, v in result.items() if k in include_fields}
    
    if exclude_fields is not None:
        # 指定されたフィールドを除外
        result = {k: v for k, v in result.items() if k not in exclude_fields}
    
    return result


def calculate_system_info_metrics_pure(info: SystemInfo) -> Dict[str, Any]:
    """
    システム情報のメトリクスを計算する純粋関数
    
    Args:
        info: システム情報
        
    Returns:
        メトリクス辞書
    """
    metrics = {
        "fields_populated": 0,
        "total_fields": 6,
        "completion_rate": 0.0,
        "has_contest_info": False,
        "has_execution_info": False,
        "env_json_languages": 0,
        "env_json_commands": 0
    }
    
    # フィールドの充足率
    fields = [info.command, info.language, info.env_type, 
              info.contest_name, info.problem_name, info.env_json]
    populated_fields = sum(1 for field in fields if field is not None)
    
    metrics["fields_populated"] = populated_fields
    metrics["completion_rate"] = populated_fields / metrics["total_fields"]
    
    # コンテスト情報の有無
    metrics["has_contest_info"] = bool(info.contest_name and info.problem_name)
    
    # 実行情報の有無
    metrics["has_execution_info"] = bool(info.command and info.language)
    
    # env_jsonの詳細
    if info.env_json:
        metrics["env_json_languages"] = len(info.env_json)
        total_commands = 0
        for lang_config in info.env_json.values():
            if isinstance(lang_config, dict) and "commands" in lang_config:
                total_commands += len(lang_config["commands"])
        metrics["env_json_commands"] = total_commands
    
    return metrics


def create_system_info_from_params_pure(
    command: Optional[str] = None,
    language: Optional[str] = None,
    env_type: Optional[str] = None,
    contest_name: Optional[str] = None,
    problem_name: Optional[str] = None,
    env_json: Optional[Dict[str, Any]] = None
) -> SystemInfo:
    """
    パラメータからシステム情報を作成する純粋関数
    
    Args:
        command: コマンド
        language: 言語
        env_type: 環境タイプ
        contest_name: コンテスト名
        problem_name: 問題名
        env_json: 環境設定JSON
        
    Returns:
        SystemInfo: 作成されたシステム情報
    """
    return SystemInfo(
        command=command,
        language=language,
        env_type=env_type,
        contest_name=contest_name,
        problem_name=problem_name,
        env_json=env_json
    )