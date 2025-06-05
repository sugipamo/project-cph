"""
統合フォーマット処理ライブラリ

既存の3つのフォーマット実装を統合し、統一されたAPIを提供

使用例:
    # 基本的なフォーマット
    from src.utils.formatting import FormattingCore
    result = FormattingCore.safe_format("Hello {name}!", {"name": "World"})
    
    # ExecutionContext特化
    from src.utils.formatting import ExecutionContextFormatter, ExecutionFormatData
    data = ExecutionFormatData(command_type="run", language="python", ...)
    result = ExecutionContextFormatter.format_execution_template(template, data)
    
    # OutputManager特化
    from src.utils.formatting import OutputManagerFormatter, OutputFormatData
    output_data = OutputManagerFormatter.extract_output_data(result)
    formatted = OutputManagerFormatter.format_output_content(output_data)
    
    # 互換性レイヤー（既存コードとの互換性）
    from src.utils.formatting import extract_format_keys, safe_format_template
    keys = extract_format_keys("Hello {name}!")
    result, missing = safe_format_template("Hello {name}!", name="World")
"""

# 基底レイヤーのエクスポート
from .core import (
    FormattingCore,
    FormatOperationResult,
    extract_format_keys,
    extract_template_keys,
    format_with_missing_keys,
    safe_format_template
)

# ExecutionContext特化レイヤーのエクスポート
from .execution_context import (
    ExecutionContextFormatter,
    ExecutionFormatData,
    create_format_dict as create_execution_format_dict
)

# OutputManager特化レイヤーのエクスポート
from .output_manager import (
    OutputManagerFormatter,
    OutputFormatData,
    extract_output_data as extract_output_data_simple,
    should_show_output as should_show_output_simple,
    format_output_content as format_output_content_simple
)

# 統合API（推奨）
class UnifiedFormatter:
    """統合されたフォーマット処理の単一エントリーポイント
    
    全ての機能に統一されたインターフェースでアクセス可能
    """
    
    # 基底機能
    extract_keys = staticmethod(FormattingCore.extract_template_keys)
    safe_format = staticmethod(FormattingCore.safe_format)
    validate_template = staticmethod(FormattingCore.validate_template)
    merge_dicts = staticmethod(FormattingCore.merge_format_dicts)
    
    # ExecutionContext機能
    create_execution_dict = staticmethod(ExecutionContextFormatter.create_format_dict)
    format_execution = staticmethod(ExecutionContextFormatter.format_execution_template)
    extract_execution_vars = staticmethod(ExecutionContextFormatter.extract_execution_variables)
    
    # OutputManager機能
    extract_output = staticmethod(OutputManagerFormatter.extract_output_data)
    should_show = staticmethod(OutputManagerFormatter.should_show_output)
    format_output = staticmethod(OutputManagerFormatter.format_output_content)
    create_summary = staticmethod(OutputManagerFormatter.create_output_summary)


# メインエクスポート
__all__ = [
    # 基底クラス
    'FormattingCore',
    'FormatOperationResult',
    
    # 特化クラス
    'ExecutionContextFormatter',
    'ExecutionFormatData',
    'OutputManagerFormatter', 
    'OutputFormatData',
    
    # 統合API
    'UnifiedFormatter',
    
    # 互換性関数（非推奨だが維持）
    'extract_format_keys',
    'extract_template_keys',
    'format_with_missing_keys',
    'safe_format_template',
    'create_execution_format_dict',
    'extract_output_data_simple',
    'should_show_output_simple',
    'format_output_content_simple'
]

# バージョン情報
__version__ = "1.0.0"
__description__ = "統合フォーマット処理ライブラリ"