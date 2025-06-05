"""
ExecutionContext特化フォーマット処理

ExecutionContext固有のフォーマット機能を提供
基底レイヤーを継承して特化機能を追加
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Union

from .core import FormattingCore, FormatOperationResult


@dataclass(frozen=True)
class ExecutionFormatData:
    """ExecutionContext用フォーマットデータの不変データクラス"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict
    
    # 追加の実行コンテキスト情報
    workspace_path: Optional[str] = None
    mount_path: Optional[str] = None
    container_name: Optional[str] = None


class ExecutionContextFormatter(FormattingCore):
    """ExecutionContext特化のフォーマット処理クラス"""
    
    @staticmethod
    def create_format_dict(data: ExecutionFormatData,
                          strict: bool = False) -> Union[Dict[str, str], FormatOperationResult]:
        """ExecutionFormatDataからフォーマット用辞書を生成
        
        Args:
            data: ExecutionContext用フォーマットデータ
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: フォーマット用辞書
            strict=Trueの場合: FormatOperationResult
        """
        try:
            # 基本的な値
            format_dict = {
                "command_type": data.command_type,
                "language": data.language,
                "contest_name": data.contest_name,
                "problem_name": data.problem_name,
                "problem_id": data.problem_name,  # 互換性のため
                "env_type": data.env_type,
            }
            
            warnings = []
            
            # 追加のコンテキスト情報
            if data.workspace_path:
                format_dict["workspace_path"] = data.workspace_path
            if data.mount_path:
                format_dict["mount_path"] = data.mount_path
            if data.container_name:
                format_dict["container_name"] = data.container_name
            
            # env_jsonから言語固有の設定を取得
            if data.env_json and isinstance(data.env_json, dict):
                if data.language in data.env_json:
                    lang_config = data.env_json[data.language]
                    
                    if isinstance(lang_config, dict):
                        # パス関連の設定
                        path_configs = {
                            "contest_current_path": "./contest_current",
                            "contest_stock_path": "./contest_stock", 
                            "contest_template_path": "./contest_template/{language_name}",
                            "contest_temp_path": "./.temp",
                            "workspace_path": "./workspace",
                        }
                        
                        for key, default in path_configs.items():
                            value = lang_config.get(key, default)
                            format_dict[key] = value
                        
                        # その他の言語固有設定
                        other_configs = {
                            "language_id": "",
                            "source_file_name": "main.py",
                            "language_name": data.language,
                            "exec_command": "",
                            "compile_command": "",
                        }
                        
                        for key, default in other_configs.items():
                            value = lang_config.get(key, default)
                            format_dict[key] = value
                    else:
                        warnings.append(f"Language config for '{data.language}' is not a dictionary")
                else:
                    warnings.append(f"Language '{data.language}' not found in env_json")
                
                # グローバル設定の取得
                global_configs = {
                    "docker_image": "",
                    "timeout": "30",
                    "memory_limit": "256MB",
                }
                
                for key, default in global_configs.items():
                    if key in data.env_json:
                        format_dict[key] = str(data.env_json[key])
                    else:
                        format_dict[key] = default
            else:
                warnings.append("env_json is empty or not a dictionary")
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "data_fields": list(asdict(data).keys()),
                        "format_keys": len(format_dict),
                        "env_json_available": bool(data.env_json)
                    }
                )
            else:
                return format_dict
                
        except Exception as e:
            error_msg = f"Failed to create format dictionary: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"data": str(data)}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def format_execution_template(template: str,
                                data: ExecutionFormatData,
                                strict: bool = False,
                                allow_missing: bool = True) -> Union[str, FormatOperationResult]:
        """ExecutionContext用テンプレートのフォーマット
        
        Args:
            template: フォーマット対象テンプレート
            data: ExecutionContext用データ
            strict: Trueの場合、詳細な結果型を返す
            allow_missing: 欠損キーを許可するか
            
        Returns:
            strict=Falseの場合: フォーマット済み文字列
            strict=Trueの場合: FormatOperationResult
        """
        try:
            # フォーマット辞書を作成
            format_dict_result = ExecutionContextFormatter.create_format_dict(data, strict=True)
            
            if not format_dict_result.success:
                if strict:
                    return format_dict_result
                else:
                    raise ValueError(format_dict_result.errors[0] if format_dict_result.errors else "Failed to create format dictionary")
            
            # フォーマット辞書を取得（メタデータから復元）
            format_dict = ExecutionContextFormatter.create_format_dict(data, strict=False)
            
            # 基底クラスの安全フォーマットを使用
            result = ExecutionContextFormatter.safe_format(
                template, 
                format_dict, 
                strict=strict, 
                allow_missing=allow_missing
            )
            
            if strict and isinstance(result, FormatOperationResult):
                # 警告をマージ
                merged_warnings = format_dict_result.warnings + result.warnings
                return FormatOperationResult(
                    success=result.success,
                    result=result.result,
                    missing_keys=result.missing_keys,
                    errors=result.errors,
                    warnings=merged_warnings,
                    metadata={
                        **result.metadata,
                        "execution_context": True,
                        "data_type": "ExecutionFormatData"
                    }
                )
            else:
                return result
                
        except Exception as e:
            error_msg = f"Failed to format execution template: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": template, "data": str(data)}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def extract_execution_variables(template: str,
                                  strict: bool = False) -> Union[Dict[str, str], FormatOperationResult]:
        """ExecutionContext固有の変数を抽出
        
        Args:
            template: 解析対象テンプレート
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: 変数名と説明の辞書
            strict=Trueの場合: FormatOperationResult
        """
        try:
            # テンプレートからキーを抽出
            keys = ExecutionContextFormatter.extract_template_keys(template, strict=False)
            
            # ExecutionContext固有の変数説明
            execution_variables = {
                "command_type": "実行コマンドタイプ (run/test/submit等)",
                "language": "プログラミング言語名",
                "contest_name": "コンテスト名",
                "problem_name": "問題名",
                "problem_id": "問題ID (problem_nameのエイリアス)",
                "env_type": "実行環境タイプ",
                "workspace_path": "ワークスペースパス",
                "mount_path": "Dockerマウントパス", 
                "container_name": "Dockerコンテナ名",
                "contest_current_path": "現在のコンテストパス",
                "contest_stock_path": "コンテストストックパス",
                "contest_template_path": "コンテストテンプレートパス",
                "contest_temp_path": "コンテスト一時パス",
                "language_id": "言語ID",
                "source_file_name": "ソースファイル名",
                "language_name": "言語名",
                "exec_command": "実行コマンド",
                "compile_command": "コンパイルコマンド",
                "docker_image": "Dockerイメージ名",
                "timeout": "タイムアウト時間",
                "memory_limit": "メモリ制限",
            }
            
            # 使用されている変数のみを抽出
            used_variables = {}
            unknown_variables = []
            
            for key in keys:
                if key in execution_variables:
                    used_variables[key] = execution_variables[key]
                else:
                    unknown_variables.append(key)
            
            warnings = []
            if unknown_variables:
                warnings.append(f"Unknown variables found: {unknown_variables}")
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "template": template,
                        "total_keys": len(keys),
                        "known_keys": len(used_variables),
                        "unknown_keys": len(unknown_variables),
                        "unknown_variables": unknown_variables
                    }
                )
            else:
                return used_variables
                
        except Exception as e:
            error_msg = f"Failed to extract execution variables: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": template}
                )
            else:
                raise ValueError(error_msg)


# 互換性のためのエイリアス関数
def create_format_dict(data: ExecutionFormatData) -> Dict[str, str]:
    """既存コードとの互換性維持"""
    return ExecutionContextFormatter.create_format_dict(data, strict=False)