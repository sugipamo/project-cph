"""
基本的な文字列フォーマット機能

高性能な文字列フォーマット処理を提供
正規表現キャッシングとテンプレート処理最適化を実装
"""
import re
from typing import Dict, List, Tuple, Any
from functools import lru_cache


# Pre-compiled regex patterns for better performance
# This pattern matches {key} but not {{key}} (escaped braces)
_FORMAT_KEY_PATTERN = re.compile(r'(?<!\{)\{(\w+)\}(?!\})')


@lru_cache(maxsize=512)
def extract_format_keys(template: str) -> List[str]:
    """
    テンプレート文字列からフォーマットキー（{key}のkey部分）をリストで抽出
    
    Args:
        template: 解析するテンプレート文字列
        
    Returns:
        List[str]: 抽出されたキーのリスト
        
    Example:
        >>> extract_format_keys('/path/{foo}/{bar}.py')
        ['foo', 'bar']
        
    Performance optimizations:
        - Pre-compiled regex patterns
        - LRU cache for result reuse
    """
    return _FORMAT_KEY_PATTERN.findall(template)


def format_with_missing_keys(template: str, **kwargs) -> Tuple[str, List[str]]:
    """
    テンプレートの{key}をkwargsで置換し、結果と不足キーのリストを返す
    
    Args:
        template: フォーマットするテンプレート文字列
        **kwargs: フォーマット用のキーワード引数
        
    Returns:
        Tuple[str, List[str]]: (フォーマット済み文字列, 不足キーリスト)
        
    Example:
        >>> template = '/path/{foo}/{bar}.py'
        >>> format_with_missing_keys(template, foo='A')
        ('/path/A/{bar}.py', ['bar'])
    """
    keys = extract_format_keys(template)
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
        str: フォーマット済みの文字列
        
    Performance optimizations:
        - str.format_map() for O(n) processing
        - String conversion done once
        - Fallback mechanism for error handling
    """
    if not isinstance(template, str):
        return template
    
    # Convert values to strings once for better performance
    str_context = {k: str(v) for k, v in context.items()}
    
    class SafeDict(dict):
        def __missing__(self, key):
            return f"{{{key}}}"
    
    try:
        return template.format_map(SafeDict(str_context))
    except (KeyError, ValueError):
        # Fallback to original method if format_map fails
        result = template
        for key, value in str_context.items():
            result = result.replace(f"{{{key}}}", value)
        return result


class SafeFormatter:
    """
    セーフなフォーマット処理を提供するクラス
    
    不正なテンプレートや不足キーに対して安全にフォーマット処理を実行
    """
    
    def __init__(self, default_context: Dict[str, Any] = None):
        """
        Args:
            default_context: デフォルトのコンテキスト辞書
        """
        self.default_context = default_context or {}
    
    def format(self, template: str, context: Dict[str, Any] = None) -> str:
        """
        テンプレートを安全にフォーマット
        
        Args:
            template: フォーマットするテンプレート
            context: 追加のコンテキスト辞書
            
        Returns:
            str: フォーマット済み文字列
        """
        merged_context = {**self.default_context}
        if context:
            merged_context.update(context)
        
        return format_with_context(template, merged_context)
    
    def format_with_validation(self, template: str, context: Dict[str, Any] = None) -> Tuple[str, List[str]]:
        """
        バリデーション付きでテンプレートをフォーマット
        
        Args:
            template: フォーマットするテンプレート
            context: 追加のコンテキスト辞書
            
        Returns:
            Tuple[str, List[str]]: (フォーマット済み文字列, 不足キーリスト)
        """
        merged_context = {**self.default_context}
        if context:
            merged_context.update(context)
        
        return format_with_missing_keys(template, **merged_context)


# Backward compatibility aliases
extract_template_keys = extract_format_keys
safe_format_template = format_with_missing_keys