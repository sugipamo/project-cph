"""
統合フォーマット機能API

基底レイヤーと特化レイヤーの機能を統合して公開
既存コードとの互換性を保ちながら、新しい統合APIを提供
"""

# Core formatting functions (基底レイヤー)
from .core import (
    # String formatting
    extract_format_keys,
    format_with_missing_keys,
    format_with_context,
    SafeFormatter,
    
    # Template processing  
    build_path_template,
    validate_template_keys,
    TemplateValidator,
    
    # Validation
    validate_format_data,
    FormatDataValidator
)

# Specialized formatting functions (特化レイヤー)
from .specialized import (
    # Execution formatting
    ExecutionFormatData,
    create_execution_format_dict,
    format_execution_template,
    validate_execution_format_data,
    get_docker_naming_context,
    
    # Output formatting
    OutputFormatData,
    extract_output_data,
    format_output_content,
    decide_output_action,
    should_show_output,
    
    # Path formatting
    build_context_path,
    format_path_template,
    validate_path_template
)

# Backward compatibility aliases (既存コードとの互換性)
# これらのエイリアスにより既存のインポートパスが引き続き動作
extract_template_keys = extract_format_keys
safe_format_template = format_with_missing_keys
create_format_dict = create_execution_format_dict
format_template_string = format_execution_template
validate_execution_data = validate_execution_format_data
get_docker_naming_from_data = get_docker_naming_context
SimpleOutputData = OutputFormatData

__all__ = [
    # Core functions
    'extract_format_keys',
    'format_with_missing_keys', 
    'format_with_context',
    'SafeFormatter',
    'build_path_template',
    'validate_template_keys',
    'TemplateValidator',
    'validate_format_data',
    'FormatDataValidator',
    
    # Specialized functions
    'ExecutionFormatData',
    'create_execution_format_dict',
    'format_execution_template',
    'validate_execution_format_data', 
    'get_docker_naming_context',
    'OutputFormatData',
    'extract_output_data',
    'format_output_content',
    'decide_output_action',
    'should_show_output',
    'build_context_path',
    'format_path_template',
    'validate_path_template',
    
    # Backward compatibility aliases
    'extract_template_keys',
    'safe_format_template',
    'create_format_dict',
    'format_template_string',
    'validate_execution_data',
    'get_docker_naming_from_data',
    'SimpleOutputData'
]


# Unified API classes for convenience
class UnifiedFormatter:
    """
    統合フォーマット機能を提供するファサードクラス
    
    基底レイヤーと特化レイヤーの機能を統合したインターフェース
    """
    
    def __init__(self, default_context: dict = None):
        """
        Args:
            default_context: デフォルトのフォーマットコンテキスト
        """
        self.string_formatter = SafeFormatter(default_context)
        self.template_validator = TemplateValidator()
        self.data_validator = FormatDataValidator()
    
    # String formatting methods
    def format_string(self, template: str, context: dict = None) -> str:
        """文字列フォーマット"""
        return self.string_formatter.format(template, context)
    
    def format_with_validation(self, template: str, context: dict = None) -> tuple:
        """バリデーション付き文字列フォーマット"""
        return self.string_formatter.format_with_validation(template, context)
    
    # Template processing methods
    def validate_template(self, template: str, required_keys: list = None) -> tuple:
        """テンプレートバリデーション"""
        return self.template_validator.validate(template, required_keys)
    
    def get_template_keys(self, template: str) -> list:
        """テンプレートキー抽出"""
        return self.template_validator.get_template_keys(template)
    
    # Data validation methods
    def validate_data(self, data, required_fields: list = None) -> tuple:
        """データバリデーション"""
        if required_fields:
            self.data_validator.required_fields = required_fields
        return self.data_validator.validate(data)


class ExecutionContextFormatter:
    """
    ExecutionContext専用の統合フォーマッター
    
    ExecutionContext関連のフォーマット処理を統合
    """
    
    def __init__(self, execution_data: ExecutionFormatData = None):
        """
        Args:
            execution_data: デフォルトの実行データ
        """
        self.execution_data = execution_data
    
    def format_template(self, template: str, data: ExecutionFormatData = None) -> tuple:
        """テンプレートフォーマット"""
        target_data = data or self.execution_data
        if not target_data:
            raise ValueError("ExecutionFormatData is required")
        return format_execution_template(template, target_data)
    
    def create_format_dict(self, data: ExecutionFormatData = None) -> dict:
        """フォーマット辞書作成"""
        target_data = data or self.execution_data
        if not target_data:
            raise ValueError("ExecutionFormatData is required")
        return create_execution_format_dict(target_data)
    
    def validate_data(self, data: ExecutionFormatData = None) -> tuple:
        """データバリデーション"""
        target_data = data or self.execution_data
        if not target_data:
            raise ValueError("ExecutionFormatData is required")
        return validate_execution_format_data(target_data)
    
    def get_docker_context(self, data: ExecutionFormatData = None, **kwargs) -> dict:
        """Docker命名コンテキスト取得"""
        target_data = data or self.execution_data
        if not target_data:
            raise ValueError("ExecutionFormatData is required")
        return get_docker_naming_context(target_data, **kwargs)


class OutputFormatter:
    """
    出力フォーマット専用クラス
    
    出力関連のフォーマット処理を統合
    """
    
    def __init__(self, stdout_prefix: str = "", stderr_prefix: str = "[ERROR] "):
        """
        Args:
            stdout_prefix: 標準出力のプレフィックス
            stderr_prefix: 標準エラーのプレフィックス
        """
        from .specialized.output_formatter import OutputFormatter as SpecializedOutputFormatter
        self.formatter = SpecializedOutputFormatter(stdout_prefix, stderr_prefix)
    
    def extract_data(self, result) -> OutputFormatData:
        """出力データ抽出"""
        return extract_output_data(result)
    
    def format_content(self, output_data: OutputFormatData) -> str:
        """出力内容フォーマット"""
        return self.formatter.format(output_data)
    
    def decide_action(self, show_output: bool, output_data: OutputFormatData) -> tuple:
        """出力アクション決定"""
        return self.formatter.decide_action(show_output, output_data)
    
    def should_show(self, request) -> bool:
        """出力表示判定"""
        return should_show_output(request)