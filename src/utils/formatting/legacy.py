"""
フォーマット処理ライブラリの互換性レイヤー
既存コードとの後方互換性を維持するためのラッパー

このモジュールは段階的移行期間中に使用されます：
- 既存のformat_utils関数APIを維持
- 既存の純粋関数APIを維持  
- 新しい統合APIへの透明な移行を提供

注意: このモジュールは非推奨（deprecated）であり、将来的に削除される予定です。
新しいコードでは src.utils.formatting.UnifiedFormatter を直接使用してください。
"""
import warnings
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

# 新しい統合ライブラリをインポート
from .core import FormattingCore, FormatOperationResult
from .execution_context import ExecutionContextFormatter, ExecutionFormatData
from .output_manager import OutputManagerFormatter, OutputFormatData


def _deprecated_warning(old_function: str, new_function: str):
    """非推奨警告を表示"""
    warnings.warn(
        f"{old_function} is deprecated. Use {new_function} instead.",
        DeprecationWarning,
        stacklevel=3
    )


# === format_utils.py 互換性関数 ===

def extract_format_keys(s: str) -> List[str]:
    """
    文字列sからstr.format用のキー（{key}のkey部分）をリストで抽出する
    
    注意: この関数は非推奨です。
    FormattingCore.extract_template_keys() を使用してください。
    """
    _deprecated_warning(
        "extract_format_keys()",
        "FormattingCore.extract_template_keys()"
    )
    return FormattingCore.extract_template_keys(s, strict=False)


def extract_template_keys(s: str) -> List[str]:
    """
    テンプレートキー抽出（エイリアス）
    
    注意: この関数は非推奨です。
    FormattingCore.extract_template_keys() を使用してください。
    """
    _deprecated_warning(
        "extract_template_keys()",
        "FormattingCore.extract_template_keys()"
    )
    return FormattingCore.extract_template_keys(s, strict=False)


def format_with_missing_keys(s: str, **kwargs) -> Tuple[str, List[str]]:
    """
    sの{key}をkwargsで置換し、新しい文字列と足りなかったキーのリストを返す
    
    注意: この関数は非推奨です。
    FormattingCore.safe_format() を使用してください。
    """
    _deprecated_warning(
        "format_with_missing_keys()",
        "FormattingCore.safe_format()"
    )
    return FormattingCore.safe_format(s, kwargs, strict=False, allow_missing=True)


def safe_format_template(s: str, **kwargs) -> Tuple[str, List[str]]:
    """
    安全なテンプレートフォーマット（エイリアス）
    
    注意: この関数は非推奨です。
    FormattingCore.safe_format() を使用してください。
    """
    _deprecated_warning(
        "safe_format_template()",
        "FormattingCore.safe_format()"
    )
    return FormattingCore.safe_format(s, kwargs, strict=False, allow_missing=True)


# === execution_context_formatter_pure.py 互換性関数 ===

@dataclass(frozen=True)
class ExecutionFormatDataLegacy:
    """互換性維持のための旧データクラス"""
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict


def create_format_dict(data: ExecutionFormatDataLegacy) -> Dict[str, str]:
    """
    ExecutionFormatDataからフォーマット用辞書を生成する純粋関数
    
    注意: この関数は非推奨です。
    ExecutionContextFormatter.create_format_dict() を使用してください。
    """
    _deprecated_warning(
        "create_format_dict()",
        "ExecutionContextFormatter.create_format_dict()"
    )
    
    # 旧データ形式を新データ形式に変換
    new_data = ExecutionFormatData(
        command_type=data.command_type,
        language=data.language,
        contest_name=data.contest_name,
        problem_name=data.problem_name,
        env_type=data.env_type,
        env_json=data.env_json
    )
    
    return ExecutionContextFormatter.create_format_dict(new_data, strict=False)


# === output_manager_formatter_pure.py 互換性関数 ===

@dataclass(frozen=True)
class SimpleOutputData:
    """互換性維持のための旧データクラス"""
    stdout: Optional[str] = None
    stderr: Optional[str] = None


def extract_output_data(result) -> SimpleOutputData:
    """
    結果オブジェクトから出力データを抽出する純粋関数
    
    注意: この関数は非推奨です。
    OutputManagerFormatter.extract_output_data() を使用してください。
    """
    _deprecated_warning(
        "extract_output_data()",
        "OutputManagerFormatter.extract_output_data()"
    )
    
    # 新しい形式で抽出してから旧形式に変換
    new_data = OutputManagerFormatter.extract_output_data(result, strict=False)
    
    return SimpleOutputData(
        stdout=new_data.stdout,
        stderr=new_data.stderr
    )


def should_show_output(request) -> bool:
    """
    リクエストオブジェクトから出力表示フラグを抽出する純粋関数
    
    注意: この関数は非推奨です。
    OutputManagerFormatter.should_show_output() を使用してください。
    """
    _deprecated_warning(
        "should_show_output()",
        "OutputManagerFormatter.should_show_output()"
    )
    return OutputManagerFormatter.should_show_output(request, strict=False)


def format_output_content(output_data: SimpleOutputData) -> str:
    """
    出力データから実際の出力テキストを生成する純粋関数
    
    注意: この関数は非推奨です。
    OutputManagerFormatter.format_output_content() を使用してください。
    """
    _deprecated_warning(
        "format_output_content()",
        "OutputManagerFormatter.format_output_content()"
    )
    
    # 旧データ形式を新データ形式に変換
    new_data = OutputFormatData(
        stdout=output_data.stdout,
        stderr=output_data.stderr
    )
    
    return OutputManagerFormatter.format_output_content(new_data, strict=False)


# === 統合ユーティリティ関数 ===

def get_legacy_migration_info() -> Dict[str, str]:
    """非推奨関数から新関数への移行情報を取得"""
    return {
        "extract_format_keys": "FormattingCore.extract_template_keys",
        "extract_template_keys": "FormattingCore.extract_template_keys", 
        "format_with_missing_keys": "FormattingCore.safe_format",
        "safe_format_template": "FormattingCore.safe_format",
        "create_format_dict": "ExecutionContextFormatter.create_format_dict",
        "extract_output_data": "OutputManagerFormatter.extract_output_data",
        "should_show_output": "OutputManagerFormatter.should_show_output",
        "format_output_content": "OutputManagerFormatter.format_output_content"
    }


def check_deprecated_usage(code_string: str) -> List[str]:
    """コード文字列内の非推奨関数使用をチェック"""
    deprecated_functions = get_legacy_migration_info().keys()
    found_deprecated = []
    
    for func_name in deprecated_functions:
        if func_name in code_string:
            found_deprecated.append(func_name)
    
    return found_deprecated


# エクスポート用
__all__ = [
    # format_utils.py 互換
    'extract_format_keys',
    'extract_template_keys', 
    'format_with_missing_keys',
    'safe_format_template',
    
    # execution_context_formatter_pure.py 互換
    'ExecutionFormatDataLegacy',
    'create_format_dict',
    
    # output_manager_formatter_pure.py 互換
    'SimpleOutputData',
    'extract_output_data',
    'should_show_output',
    'format_output_content',
    
    # ユーティリティ
    'get_legacy_migration_info',
    'check_deprecated_usage'
]