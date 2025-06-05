"""
フォーマット機能の基底レイヤー

基本的な文字列フォーマット、テンプレート処理、バリデーション機能を提供
高性能かつ再利用可能な純粋関数として実装
"""

from .string_formatter import (
    extract_format_keys,
    format_with_missing_keys,
    format_with_context,
    SafeFormatter
)

from .template_processor import (
    build_path_template,
    validate_template_keys,
    TemplateValidator
)

from .validation import (
    validate_format_data,
    FormatDataValidator
)

__all__ = [
    # String formatting
    'extract_format_keys',
    'format_with_missing_keys', 
    'format_with_context',
    'SafeFormatter',
    
    # Template processing
    'build_path_template',
    'validate_template_keys',
    'TemplateValidator',
    
    # Validation
    'validate_format_data',
    'FormatDataValidator'
]