"""
パス関連フォーマット特化機能

パステンプレートの処理とコンテキスト固有のパス構築を提供
"""
from typing import Dict, Any, List, Tuple
from ..core.string_formatter import format_with_context, extract_format_keys
from ..core.template_processor import build_path_template, validate_template_keys


def build_context_path(base_template: str, context: Dict[str, Any], *additional_parts: str) -> str:
    """
    コンテキストを使ってパステンプレートを構築
    
    Args:
        base_template: ベースパステンプレート
        context: フォーマット用のコンテキスト
        *additional_parts: 追加のパス部分
        
    Returns:
        str: 構築されたパス
        
    Example:
        >>> context = {'lang': 'python', 'contest': 'abc123'}
        >>> build_context_path('/base/{lang}/{contest}', context, 'problem_a')
        '/base/python/abc123/problem_a'
    """
    # ベーステンプレートをフォーマット
    formatted_base = format_with_context(base_template, context)
    
    # 追加パーツがある場合は結合
    if additional_parts:
        return build_path_template(formatted_base, *additional_parts)
    
    return formatted_base


def format_path_template(template: str, context: Dict[str, Any]) -> str:
    """
    パステンプレートをコンテキストでフォーマット
    
    Args:
        template: パステンプレート
        context: フォーマット用のコンテキスト
        
    Returns:
        str: フォーマット済みのパス
    """
    return format_with_context(template, context)


def normalize_path_separators(path: str, target_separator: str = '/') -> str:
    """
    パスのセパレータを指定されたセパレータに正規化
    
    Args:
        path: 正規化するパス
        target_separator: 目標セパレータ ('/' または '\\')
        
    Returns:
        str: 正規化されたパス
    """
    # すべてのセパレータを統一
    if target_separator == '/':
        normalized = path.replace('\\', '/')
    else:
        normalized = path.replace('/', '\\')
    
    # 連続するセパレータを単一のセパレータに置換
    while target_separator + target_separator in normalized:
        normalized = normalized.replace(target_separator + target_separator, target_separator)
    
    return normalized


def join_path_parts(*parts: str, separator: str = '/') -> str:
    """
    パス部分を結合（空白のみの部分は除外、先頭/末尾のセパレータを正しく処理）
    
    Args:
        *parts: 結合するパス部分
        separator: 使用するパス区切り文字
        
    Returns:
        str: 結合されたパス
    """
    if not parts:
        return ""
    
    # 空白のみの部分を除外
    valid_parts = [part for part in parts if part.strip()]
    
    if not valid_parts:
        return ""
    
    # 各部分から先頭と末尾のセパレータを削除
    cleaned_parts = []
    for part in valid_parts:
        # 先頭と末尾のセパレータを削除（ただし/と\の両方を考慮）
        cleaned = part.strip().strip('/').strip('\\')
        if cleaned:
            cleaned_parts.append(cleaned)
    
    return separator.join(cleaned_parts)


def validate_path_template(template: str, required_keys: List[str]) -> Tuple[bool, List[str]]:
    """
    パステンプレートの必要キーが含まれているかを検証
    
    Args:
        template: 検証するパステンプレート
        required_keys: 必要なキーのリスト
        
    Returns:
        Tuple[bool, List[str]]: (検証結果, 不足キーリスト)
    """
    template_keys = extract_format_keys(template)
    missing_keys = [key for key in required_keys if key not in template_keys]
    return len(missing_keys) == 0, missing_keys


class PathFormatter:
    """パスフォーマット処理のクラス実装"""
    
    def __init__(self, base_paths: Dict[str, str] = None, default_context: Dict[str, Any] = None, path_separator: str = '/'):
        """
        Args:
            base_paths: ベースパスのテンプレート辞書
            default_context: デフォルトのコンテキスト
            path_separator: 使用するパス区切り文字
        """
        self.base_paths = base_paths or {}
        self.default_context = default_context or {}
        self.path_separator = path_separator
    
    def format_path(self, path_key: str, context: Dict[str, Any] = None, *additional_parts: str) -> str:
        """
        パスキーに基づいてパスを生成
        
        Args:
            path_key: ベースパス辞書のキー
            context: 追加のコンテキスト
            *additional_parts: 追加のパス部分
            
        Returns:
            str: 生成されたパス
        """
        if path_key not in self.base_paths:
            raise ValueError(f"Unknown path key: {path_key}")
        
        # コンテキストをマージ
        merged_context = {**self.default_context}
        if context:
            merged_context.update(context)
        
        # パスを構築
        base_template = self.base_paths[path_key]
        return build_context_path(base_template, merged_context, *additional_parts)
    
    def add_base_path(self, key: str, template: str):
        """ベースパステンプレートを追加"""
        self.base_paths[key] = template
    
    def update_default_context(self, context: Dict[str, Any]):
        """デフォルトコンテキストを更新"""
        self.default_context.update(context)
    
    def validate_all_paths(self, required_context_keys: List[str]) -> Dict[str, Tuple[bool, List[str]]]:
        """
        全ベースパスのバリデーション
        
        Args:
            required_context_keys: 必須のコンテキストキー
            
        Returns:
            Dict[str, Tuple[bool, List[str]]]: パスキーごとのバリデーション結果
        """
        results = {}
        for path_key, template in self.base_paths.items():
            is_valid, missing_keys = validate_path_template(template, required_context_keys)
            results[path_key] = (is_valid, missing_keys)
        
        return results
    
    def get_path_keys(self, path_key: str) -> List[str]:
        """
        指定されたパステンプレートで使用されているキーを取得
        
        Args:
            path_key: ベースパス辞書のキー
            
        Returns:
            List[str]: 使用されているキーのリスト
        """
        if path_key not in self.base_paths:
            return []
        
        return extract_format_keys(self.base_paths[path_key])