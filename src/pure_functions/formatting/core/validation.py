"""
フォーマット関連のバリデーション機能

データ構造やフォーマット引数の検証機能を提供
"""
from typing import Any, List, Tuple, Optional, Dict


def validate_format_data(data: Any, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    フォーマットデータの基本的なバリデーションを実行
    
    Args:
        data: バリデーション対象のデータ
        required_fields: 必須フィールドのリスト
        
    Returns:
        Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
    """
    if data is None:
        return False, "Data cannot be None"
    
    # dataclassの場合
    if hasattr(data, '__dataclass_fields__'):
        return _validate_dataclass(data, required_fields)
    
    # 辞書の場合
    if isinstance(data, dict):
        return _validate_dict(data, required_fields)
    
    # その他のオブジェクトの場合（属性チェック）
    return _validate_object(data, required_fields)


def _validate_dataclass(data: Any, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """dataclassのバリデーション"""
    for field_name in required_fields:
        if not hasattr(data, field_name):
            return False, f"Required field '{field_name}' is missing"
        
        value = getattr(data, field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Required field '{field_name}' is empty"
    
    return True, None


def _validate_dict(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """辞書のバリデーション"""
    for field_name in required_fields:
        if field_name not in data:
            return False, f"Required key '{field_name}' is missing"
        
        value = data[field_name]
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Required key '{field_name}' is empty"
    
    return True, None


def _validate_object(data: Any, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """一般オブジェクトのバリデーション"""
    for field_name in required_fields:
        if not hasattr(data, field_name):
            return False, f"Required attribute '{field_name}' is missing"
        
        value = getattr(data, field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Required attribute '{field_name}' is empty"
    
    return True, None


class FormatDataValidator:
    """
    フォーマットデータの統一的なバリデーション機能を提供
    
    カスタマイズ可能なバリデーションルールと詳細なエラー報告
    """
    
    def __init__(self, required_fields: List[str] = None, custom_validators: Dict[str, callable] = None):
        """
        Args:
            required_fields: 必須フィールドのリスト
            custom_validators: カスタムバリデーター関数の辞書
        """
        self.required_fields = required_fields or []
        self.custom_validators = custom_validators or {}
    
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """
        データをバリデート
        
        Args:
            data: バリデーション対象のデータ
            
        Returns:
            Tuple[bool, List[str]]: (バリデーション結果, エラーメッセージリスト)
        """
        errors = []
        
        # 基本的なバリデーション
        is_valid, error = validate_format_data(data, self.required_fields)
        if not is_valid:
            errors.append(error)
        
        # カスタムバリデーション
        for field_name, validator in self.custom_validators.items():
            try:
                if hasattr(data, field_name):
                    value = getattr(data, field_name)
                elif isinstance(data, dict) and field_name in data:
                    value = data[field_name]
                else:
                    continue
                
                if not validator(value):
                    errors.append(f"Custom validation failed for field '{field_name}'")
                    
            except Exception as e:
                errors.append(f"Custom validation error for field '{field_name}': {str(e)}")
        
        return len(errors) == 0, errors
    
    def add_required_field(self, field_name: str):
        """必須フィールドを追加"""
        if field_name not in self.required_fields:
            self.required_fields.append(field_name)
    
    def add_custom_validator(self, field_name: str, validator: callable):
        """カスタムバリデーターを追加"""
        self.custom_validators[field_name] = validator
    
    def validate_format_context(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        フォーマットコンテキストのバリデーション
        
        Args:
            context: フォーマット用のコンテキスト辞書
            
        Returns:
            Tuple[bool, List[str]]: (バリデーション結果, エラーメッセージリスト)
        """
        errors = []
        
        if not isinstance(context, dict):
            errors.append("Context must be a dictionary")
            return False, errors
        
        # 必須フィールドのチェック
        for field_name in self.required_fields:
            if field_name not in context:
                errors.append(f"Required context key '{field_name}' is missing")
            elif context[field_name] is None:
                errors.append(f"Context key '{field_name}' cannot be None")
        
        return len(errors) == 0, errors