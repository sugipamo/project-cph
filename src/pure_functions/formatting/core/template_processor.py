"""
テンプレート処理機能

パステンプレート構築、テンプレートバリデーション等の機能を提供
"""
from typing import List, Tuple
from .string_formatter import extract_format_keys


def build_path_template(base: str, *parts: str) -> str:
    """
    パステンプレートを構築
    
    Args:
        base: ベースパス
        *parts: パス部分のリスト
        
    Returns:
        str: 構築されたパステンプレート
        
    Example:
        >>> build_path_template('/base', 'sub', 'file.py')
        '/base/sub/file.py'
    """
    return '/'.join([base.rstrip('/'), *[part.strip('/') for part in parts]])


def validate_template_keys(template: str, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    テンプレートが必要なキーを含んでいるかチェック
    
    Args:
        template: チェックするテンプレート文字列
        required_keys: 必須キーのリスト
        
    Returns:
        Tuple[bool, List[str]]: (有効かどうか, 不足キーリスト)
        
    Example:
        >>> validate_template_keys('/{foo}/{bar}', ['foo', 'bar', 'baz'])
        (False, ['baz'])
    """
    template_keys = set(extract_format_keys(template))
    missing_keys = [key for key in required_keys if key not in template_keys]
    
    return len(missing_keys) == 0, missing_keys


class TemplateValidator:
    """
    テンプレートバリデーション機能を提供するクラス
    
    複数のテンプレートに対する一貫したバリデーションルールを管理
    """
    
    def __init__(self, required_keys: List[str] = None):
        """
        Args:
            required_keys: 常に必要とされるキーのリスト
        """
        self.required_keys = required_keys or []
    
    def validate(self, template: str, additional_required_keys: List[str] = None) -> Tuple[bool, List[str]]:
        """
        テンプレートをバリデート
        
        Args:
            template: バリデートするテンプレート
            additional_required_keys: 追加で必要なキーのリスト
            
        Returns:
            Tuple[bool, List[str]]: (有効かどうか, 不足キーリスト)
        """
        all_required_keys = self.required_keys.copy()
        if additional_required_keys:
            all_required_keys.extend(additional_required_keys)
        
        return validate_template_keys(template, all_required_keys)
    
    def validate_multiple(self, templates: List[str]) -> List[Tuple[str, bool, List[str]]]:
        """
        複数のテンプレートを一度にバリデート
        
        Args:
            templates: バリデートするテンプレートのリスト
            
        Returns:
            List[Tuple[str, bool, List[str]]]: (テンプレート, 有効性, 不足キー)のリスト
        """
        results = []
        for template in templates:
            is_valid, missing_keys = self.validate(template)
            results.append((template, is_valid, missing_keys))
        
        return results
    
    def get_template_keys(self, template: str) -> List[str]:
        """
        テンプレートから使用されているキーを抽出
        
        Args:
            template: 解析するテンプレート
            
        Returns:
            List[str]: 使用されているキーのリスト
        """
        return extract_format_keys(template)