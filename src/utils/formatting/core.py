"""
統合フォーマット処理ライブラリ - 基底レイヤー

既存の3つのフォーマット実装を統合し、統一されたAPIを提供

このモジュールは以下の既存実装を統合します：
- src/context/utils/format_utils.py (汎用フォーマット)
- src/pure_functions/execution_context_formatter_pure.py (ExecutionContext特化)
- src/pure_functions/output_manager_formatter_pure.py (OutputManager特化)
"""
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Tuple, Any, Optional, Union


@dataclass(frozen=True)
class FormatOperationResult:
    """フォーマット操作結果の統一データクラス"""
    success: bool
    result: Optional[str]
    missing_keys: List[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.missing_keys is None:
            object.__setattr__(self, 'missing_keys', [])
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


# Pre-compiled regex patterns for better performance
_FORMAT_KEY_PATTERN = re.compile(r'{(\w+)}')
_ADVANCED_FORMAT_PATTERN = re.compile(r'{([^}]+)}')
_SAFE_KEY_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class FormattingCore:
    """統合されたフォーマット処理クラス
    
    シンプルなAPI（例外ベース）と詳細なAPI（結果型ベース）の両方を提供
    """
    
    @staticmethod
    @lru_cache(maxsize=512)
    def extract_template_keys(template: str, 
                            advanced: bool = False,
                            strict: bool = False) -> Union[List[str], FormatOperationResult]:
        """テンプレート文字列からキーを抽出する
        
        Args:
            template: 対象テンプレート文字列
            advanced: 高度なフォーマット指定子も抽出するか
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: キーのリスト
            strict=Trueの場合: FormatOperationResult
            
        Examples:
            extract_template_keys("/path/{foo}/{bar}.py") -> ["foo", "bar"]
            extract_template_keys("{name:>10}", advanced=True) -> ["name"]
        """
        try:
            if not template or not isinstance(template, str):
                error_msg = "Template must be a non-empty string"
                if strict:
                    return FormatOperationResult(
                        success=False,
                        result=None,
                        missing_keys=[],
                        errors=[error_msg],
                        warnings=[],
                        metadata={"template": str(template)}
                    )
                else:
                    raise ValueError(error_msg)
            
            # パターン選択
            pattern = _ADVANCED_FORMAT_PATTERN if advanced else _FORMAT_KEY_PATTERN
            
            # キー抽出
            raw_keys = pattern.findall(template)
            
            # 高度なパターンの場合、フォーマット指定子を除去
            if advanced:
                keys = []
                warnings = []
                for key in raw_keys:
                    # コロンでフォーマット指定子を分割
                    key_name = key.split(':')[0].split('!')[0]
                    if key_name:
                        keys.append(key_name)
                    else:
                        warnings.append(f"Empty key found in format: {{{key}}}")
            else:
                keys = raw_keys
                warnings = []
            
            # キーの妥当性チェック
            valid_keys = []
            for key in keys:
                if _SAFE_KEY_PATTERN.match(key):
                    valid_keys.append(key)
                else:
                    warnings.append(f"Invalid key name: {key}")
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "template": template,
                        "keys_found": len(valid_keys),
                        "advanced": advanced,
                        "raw_keys": raw_keys
                    }
                )
            else:
                return valid_keys
                
        except Exception as e:
            error_msg = f"Failed to extract template keys: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": str(template)}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def safe_format(template: str, 
                   format_dict: Dict[str, Any],
                   strict: bool = False,
                   allow_missing: bool = True) -> Union[Tuple[str, List[str]], FormatOperationResult]:
        """安全なテンプレートフォーマット処理
        
        Args:
            template: フォーマット対象のテンプレート
            format_dict: フォーマット用の値辞書
            strict: Trueの場合、詳細な結果型を返す
            allow_missing: 欠損キーを許可するか
            
        Returns:
            strict=Falseの場合: (フォーマット済み文字列, 欠損キーリスト)
            strict=Trueの場合: FormatOperationResult
            
        Examples:
            safe_format("/path/{foo}/{bar}.py", {"foo": "A"}) 
            -> ("/path/A/{bar}.py", ["bar"])
        """
        try:
            if not isinstance(template, str):
                error_msg = "Template must be a string"
                if strict:
                    return FormatOperationResult(
                        success=False,
                        result=None,
                        missing_keys=[],
                        errors=[error_msg],
                        warnings=[],
                        metadata={"template": str(template)}
                    )
                else:
                    raise ValueError(error_msg)
            
            if not isinstance(format_dict, dict):
                error_msg = "Format dictionary must be a dict"
                if strict:
                    return FormatOperationResult(
                        success=False,
                        result=None,
                        missing_keys=[],
                        errors=[error_msg],
                        warnings=[],
                        metadata={"template": template}
                    )
                else:
                    raise ValueError(error_msg)
            
            # キー抽出
            keys = FormattingCore.extract_template_keys(template, strict=False)
            missing_keys = [k for k in keys if k not in format_dict]
            
            warnings = []
            
            # 型変換の安全な実行
            safe_dict = {}
            for key, value in format_dict.items():
                if value is None:
                    safe_dict[key] = ""
                    warnings.append(f"None value converted to empty string for key: {key}")
                elif not isinstance(value, (str, int, float, bool)):
                    safe_dict[key] = str(value)
                    warnings.append(f"Non-primitive value converted to string for key: {key}")
                else:
                    safe_dict[key] = value
            
            # 欠損キーの処理
            if allow_missing:
                class SafeDict(dict):
                    def __missing__(self, key):
                        return '{' + key + '}'
                
                formatted = template.format_map(SafeDict(safe_dict))
            else:
                if missing_keys:
                    error_msg = f"Missing required keys: {missing_keys}"
                    if strict:
                        return FormatOperationResult(
                            success=False,
                            result=None,
                            missing_keys=missing_keys,
                            errors=[error_msg],
                            warnings=warnings,
                            metadata={"template": template, "available_keys": list(format_dict.keys())}
                        )
                    else:
                        raise KeyError(error_msg)
                
                formatted = template.format(**safe_dict)
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=formatted,
                    missing_keys=missing_keys,
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "template": template,
                        "keys_used": len(set(keys) & set(format_dict.keys())),
                        "allow_missing": allow_missing
                    }
                )
            else:
                return formatted, missing_keys
                
        except Exception as e:
            error_msg = f"Failed to format template: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": template}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def validate_template(template: str,
                         strict: bool = False) -> Union[bool, FormatOperationResult]:
        """テンプレート文字列の妥当性を検証
        
        Args:
            template: 検証対象のテンプレート
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: bool
            strict=Trueの場合: FormatOperationResult
        """
        try:
            if not isinstance(template, str):
                if strict:
                    return FormatOperationResult(
                        success=False,
                        result=None,
                        missing_keys=[],
                        errors=["Template must be a string"],
                        warnings=[],
                        metadata={"template": str(template)}
                    )
                else:
                    return False
            
            warnings = []
            errors = []
            
            # 基本的な形式チェック
            open_braces = template.count('{')
            close_braces = template.count('}')
            
            if open_braces != close_braces:
                errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
            
            # テンプレートキーの検証
            try:
                keys = FormattingCore.extract_template_keys(template, advanced=True, strict=False)
                if not keys and ('{' in template or '}' in template):
                    warnings.append("Template contains braces but no valid keys found")
            except Exception as e:
                errors.append(f"Failed to extract keys: {e}")
            
            # フォーマット構文のテスト
            try:
                # 空の辞書でフォーマットを試行（欠損キー許可）
                test_dict = {}
                FormattingCore.safe_format(template, test_dict, strict=False, allow_missing=True)
            except Exception as e:
                errors.append(f"Invalid format syntax: {e}")
            
            is_valid = len(errors) == 0
            
            if strict:
                return FormatOperationResult(
                    success=is_valid,
                    result=str(is_valid),
                    missing_keys=[],
                    errors=errors,
                    warnings=warnings,
                    metadata={
                        "template": template,
                        "open_braces": open_braces,
                        "close_braces": close_braces
                    }
                )
            else:
                return is_valid
                
        except Exception as e:
            error_msg = f"Failed to validate template: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": str(template)}
                )
            else:
                return False
    
    @staticmethod
    def merge_format_dicts(*dicts: Dict[str, Any], 
                          strict: bool = False) -> Union[Dict[str, Any], FormatOperationResult]:
        """複数のフォーマット辞書を安全にマージ
        
        Args:
            *dicts: マージする辞書群
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: マージされた辞書
            strict=Trueの場合: FormatOperationResult
        """
        try:
            if not dicts:
                if strict:
                    return FormatOperationResult(
                        success=True,
                        result=None,
                        missing_keys=[],
                        errors=[],
                        warnings=["No dictionaries provided"],
                        metadata={"input_count": 0}
                    )
                else:
                    return {}
            
            merged = {}
            warnings = []
            conflicts = []
            
            for i, d in enumerate(dicts):
                if not isinstance(d, dict):
                    error_msg = f"Argument {i} is not a dictionary: {type(d)}"
                    if strict:
                        return FormatOperationResult(
                            success=False,
                            result=None,
                            missing_keys=[],
                            errors=[error_msg],
                            warnings=warnings,
                            metadata={"failed_at_index": i}
                        )
                    else:
                        raise TypeError(error_msg)
                
                for key, value in d.items():
                    if key in merged and merged[key] != value:
                        conflicts.append(f"Key '{key}': {merged[key]} -> {value}")
                        warnings.append(f"Overwriting key '{key}' in merge")
                    merged[key] = value
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "input_count": len(dicts),
                        "output_keys": len(merged),
                        "conflicts": conflicts
                    }
                )
            else:
                return merged
                
        except Exception as e:
            error_msg = f"Failed to merge dictionaries: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"input_count": len(dicts) if dicts else 0}
                )
            else:
                raise ValueError(error_msg)


# 互換性のためのエイリアス関数
def extract_format_keys(template: str) -> List[str]:
    """互換性維持のためのエイリアス"""
    return FormattingCore.extract_template_keys(template, strict=False)


def extract_template_keys(template: str) -> List[str]:
    """互換性維持のためのエイリアス"""
    return FormattingCore.extract_template_keys(template, strict=False)


def format_with_missing_keys(template: str, **kwargs) -> Tuple[str, List[str]]:
    """互換性維持のためのエイリアス"""
    return FormattingCore.safe_format(template, kwargs, strict=False, allow_missing=True)


def safe_format_template(template: str, **kwargs) -> Tuple[str, List[str]]:
    """互換性維持のためのエイリアス"""
    return FormattingCore.safe_format(template, kwargs, strict=False, allow_missing=True)