"""
Standardized error message formatting
"""
from typing import Any, Dict, List, Optional


class ErrorMessageFormatter:
    """統一されたエラーメッセージフォーマッター"""
    
    @staticmethod
    def validation_error(field: str, reason: str, value: Any = None) -> str:
        """バリデーションエラーメッセージの生成"""
        message = f"Validation failed for '{field}': {reason}"
        if value is not None:
            # 値が長すぎる場合は切り詰める
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            message += f" (value: {value_str})"
        return message
    
    @staticmethod
    def execution_error(operation: str, details: str, exit_code: Optional[int] = None) -> str:
        """実行エラーメッセージの生成"""
        message = f"Execution failed in {operation}: {details}"
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
        return message
    
    @staticmethod
    def resource_error(resource_type: str, resource_id: str, action: str, reason: str) -> str:
        """リソースエラーメッセージの生成"""
        return f"Resource error: {action} failed for {resource_type} '{resource_id}': {reason}"
    
    @staticmethod
    def configuration_error(config_key: str, reason: str, file_path: Optional[str] = None) -> str:
        """設定エラーメッセージの生成"""
        message = f"Configuration error in '{config_key}': {reason}"
        if file_path:
            message += f" (file: {file_path})"
        return message
    
    @staticmethod
    def dependency_error(dependency_type: str, reason: str, 
                        missing: Optional[List[str]] = None,
                        circular: Optional[List[str]] = None) -> str:
        """依存関係エラーメッセージの生成"""
        message = f"Dependency error in {dependency_type}: {reason}"
        
        if missing:
            message += f" (missing: {', '.join(missing)})"
        
        if circular:
            message += f" (circular: {' -> '.join(circular)})"
        
        return message
    
    @staticmethod
    def timeout_error(operation: str, timeout_seconds: float) -> str:
        """タイムアウトエラーメッセージの生成"""
        return f"Operation '{operation}' timed out after {timeout_seconds} seconds"
    
    @staticmethod
    def permission_error(resource: str, action: str, required_permission: str) -> str:
        """権限エラーメッセージの生成"""
        return f"Permission denied: cannot {action} {resource} (requires {required_permission})"
    
    @staticmethod
    def authentication_error(auth_type: str, reason: str) -> str:
        """認証エラーメッセージの生成"""
        return f"Authentication failed for {auth_type}: {reason}"
    
    @staticmethod
    def format_context_info(context: Dict[str, Any]) -> str:
        """コンテキスト情報のフォーマット"""
        if not context:
            return ""
        
        context_items = []
        for key, value in context.items():
            # 値が複雑な場合は簡略化
            if isinstance(value, (dict, list)) and len(str(value)) > 50:
                value_str = f"{type(value).__name__}({len(value)} items)"
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            
            context_items.append(f"{key}={value_str}")
        
        return f"Context: {', '.join(context_items)}"
    
    @staticmethod
    def format_multiple_errors(errors: List[str], max_errors: int = 5) -> str:
        """複数エラーのフォーマット"""
        if len(errors) <= max_errors:
            return "; ".join(errors)
        
        shown_errors = errors[:max_errors]
        remaining_count = len(errors) - max_errors
        return "; ".join(shown_errors) + f"; and {remaining_count} more errors"
    
    @staticmethod
    def format_file_operation_error(operation: str, file_path: str, reason: str) -> str:
        """ファイル操作エラーメッセージの生成"""
        return f"File {operation} failed for '{file_path}': {reason}"
    
    @staticmethod
    def format_network_error(endpoint: str, operation: str, reason: str) -> str:
        """ネットワークエラーメッセージの生成"""
        return f"Network {operation} failed for '{endpoint}': {reason}"