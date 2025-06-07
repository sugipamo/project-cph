"""
DEPRECATED: 文字列フォーマット関連のユーティリティ

この module は非推奨です。代わりに src.shared.utils.unified_formatter を使用してください。
後方互換性のために関数は残していますが、統一フォーマッターに委譲されます。

テンプレート文字列の処理、キー抽出、安全なフォーマット処理を提供
高性能化のため正規表現キャッシングとテンプレート処理最適化を実装
"""
import warnings
from typing import Dict, List, Tuple, Any


def extract_format_keys(s: str) -> List[str]:
    """
    DEPRECATED: Use src.shared.utils.unified_formatter.extract_format_keys instead
    
    文字列sからstr.format用のキー（{key}のkey部分）をリストで抽出する
    例: '/path/{foo}/{bar}.py' -> ['foo', 'bar']
    """
    warnings.warn(
        "format_utils.extract_format_keys is deprecated. Use unified_formatter.extract_format_keys instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from src.shared.utils.unified_formatter import extract_format_keys as new_extract_format_keys
    return new_extract_format_keys(s)


# 既存コードとの互換性のためのエイリアス
extract_template_keys = extract_format_keys


def format_with_missing_keys(s: str, **kwargs) -> Tuple[str, List[str]]:
    """
    DEPRECATED: Use src.shared.utils.unified_formatter.format_with_missing_keys instead
    
    sの{key}をkwargsで置換し、新しい文字列と足りなかったキーのリストを返す
    例: s = '/path/{foo}/{bar}.py', kwargs={'foo': 'A'}
    -> ('/path/A/{bar}.py', ['bar'])
    """
    warnings.warn(
        "format_utils.format_with_missing_keys is deprecated. Use unified_formatter.format_with_missing_keys instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from src.shared.utils.unified_formatter import format_with_missing_keys as new_format_with_missing_keys
    return new_format_with_missing_keys(s, **kwargs)


# より良いAPIを提供するエイリアス
safe_format_template = format_with_missing_keys


def format_with_context(template: str, context: Dict[str, Any]) -> str:
    """
    DEPRECATED: Use src.shared.utils.unified_formatter.format_with_context instead
    
    コンテキスト辞書を使ってテンプレートをフォーマット
    """
    warnings.warn(
        "format_utils.format_with_context is deprecated. Use unified_formatter.format_with_context instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from src.shared.utils.unified_formatter import format_with_context as new_format_with_context
    return new_format_with_context(template, context)


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
    DEPRECATED: Use src.shared.utils.unified_formatter.validate_template_keys instead
    
    テンプレートが必要なキーを含んでいるかチェック
    """
    warnings.warn(
        "format_utils.validate_template_keys is deprecated. Use unified_formatter.validate_template_keys instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from src.shared.utils.unified_formatter import validate_template_keys as new_validate_template_keys
    return new_validate_template_keys(template, required_keys)

if __name__ == "__main__":
    s = '/home/cphelper/project-cph/{contest_template_path}/{language_name}/main.py'
    print(extract_format_keys(s))  # ['contest_template_path', 'language_name']
    print(format_with_missing_keys(s, contest_template_path='abc'))
    # ('/home/cphelper/project-cph/abc/{language_name}/main.py', ['language_name']) 