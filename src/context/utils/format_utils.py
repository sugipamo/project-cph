"""
文字列フォーマット関連のユーティリティ

テンプレート文字列の処理、キー抽出、安全なフォーマット処理を提供
高性能化のため正規表現キャッシングとテンプレート処理最適化を実装
"""
import re
from typing import Dict, List, Tuple, Any
from functools import lru_cache

# Pre-compiled regex patterns for better performance
_FORMAT_KEY_PATTERN = re.compile(r'{(\w+)}')


@lru_cache(maxsize=512)
def extract_format_keys(s: str) -> List[str]:
    """
    文字列sからstr.format用のキー（{key}のkey部分）をリストで抽出する
    例: '/path/{foo}/{bar}.py' -> ['foo', 'bar']
    
    パフォーマンス最適化:
    - 正規表現パターンの事前コンパイル
    - LRUキャッシュによる結果の再利用
    """
    return _FORMAT_KEY_PATTERN.findall(s)


# 既存コードとの互換性のためのエイリアス
extract_template_keys = extract_format_keys


def format_with_missing_keys(s: str, **kwargs) -> Tuple[str, List[str]]:
    """
    sの{key}をkwargsで置換し、新しい文字列と足りなかったキーのリストを返す
    例: s = '/path/{foo}/{bar}.py', kwargs={'foo': 'A'}
    -> ('/path/A/{bar}.py', ['bar'])
    """
    keys = extract_format_keys(s)
    missing = [k for k in keys if k not in kwargs]
    
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    
    formatted = s.format_map(SafeDict(kwargs))
    return formatted, missing


# より良いAPIを提供するエイリアス
safe_format_template = format_with_missing_keys


def format_with_context(template: str, context: Dict[str, Any]) -> str:
    """
    コンテキスト辞書を使ってテンプレートをフォーマット
    
    Args:
        template: フォーマットするテンプレート文字列
        context: フォーマット用のコンテキスト辞書
        
    Returns:
        フォーマット済みの文字列
        
    パフォーマンス最適化:
    - str.format_map()を使用してO(n)での処理
    - 文字列値への変換を一度だけ実行
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
    template_keys = set(extract_format_keys(template))
    missing_keys = [key for key in required_keys if key not in template_keys]
    
    return len(missing_keys) == 0, missing_keys

if __name__ == "__main__":
    s = '/home/cphelper/project-cph/{contest_template_path}/{language_name}/main.py'
    print(extract_format_keys(s))  # ['contest_template_path', 'language_name']
    print(format_with_missing_keys(s, contest_template_path='abc'))
    # ('/home/cphelper/project-cph/abc/{language_name}/main.py', ['language_name']) 