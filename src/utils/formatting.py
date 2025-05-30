"""
文字列フォーマット関連のユーティリティ

テンプレート文字列の処理、キー抽出、安全なフォーマット処理を提供
"""
import re
from typing import Dict, List, Tuple, Any


def extract_template_keys(template: str) -> List[str]:
    """
    テンプレート文字列から変数キーを抽出
    
    Args:
        template: テンプレート文字列（例: '/path/{foo}/{bar}.py'）
        
    Returns:
        抽出されたキーのリスト（例: ['foo', 'bar']）
    """
    return re.findall(r'{(\w+)}', template)


def safe_format_template(template: str, **kwargs) -> Tuple[str, List[str]]:
    """
    テンプレート文字列を安全にフォーマット
    不足しているキーはそのまま残す
    
    Args:
        template: フォーマットするテンプレート文字列
        **kwargs: フォーマット用の変数辞書
        
    Returns:
        Tuple[str, List[str]]: (フォーマット結果, 不足キーリスト)
        
    Example:
        >>> safe_format_template('/path/{foo}/{bar}.py', foo='A')
        ('/path/A/{bar}.py', ['bar'])
    """
    keys = extract_template_keys(template)
    missing = [k for k in keys if k not in kwargs]
    
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    
    formatted = template.format_map(SafeDict(kwargs))
    return formatted, missing


def format_with_context(template: str, context: Dict[str, Any]) -> str:
    """
    コンテキスト辞書を使ってテンプレートをフォーマット
    
    Args:
        template: フォーマットするテンプレート文字列
        context: フォーマット用のコンテキスト辞書
        
    Returns:
        フォーマット済みの文字列
    """
    if not isinstance(template, str):
        return template
    
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", str(value))
    
    return result


def build_path_template(base: str, *parts: str) -> str:
    """
    パステンプレートを構築
    
    Args:
        base: ベースパス
        *parts: パス部分のリスト
        
    Returns:
        構築されたパステンプレート
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
    """
    template_keys = set(extract_template_keys(template))
    missing_keys = [key for key in required_keys if key not in template_keys]
    
    return len(missing_keys) == 0, missing_keys