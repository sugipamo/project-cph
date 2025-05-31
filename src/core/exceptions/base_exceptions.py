"""
Base exception hierarchy for CPH project
"""
from typing import Optional, Dict, Any


class CPHException(Exception):
    """プロジェクト共通の基底例外"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, 
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.context = context or {}
        self.original_exception = original_exception
        self.message = message
    
    def add_context(self, key: str, value: Any):
        """コンテキスト情報を追加"""
        self.context[key] = value
        return self
    
    def get_full_message(self) -> str:
        """完全なエラーメッセージを取得"""
        msg = self.message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg += f" (Context: {context_str})"
        if self.original_exception:
            msg += f" (Caused by: {type(self.original_exception).__name__}: {self.original_exception})"
        return msg


class ValidationError(CPHException):
    """バリデーションエラー"""
    
    def __init__(self, field: str, reason: str, value: Any = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.field = field
        self.reason = reason
        self.value = value
        
        message = f"Validation failed for '{field}': {reason}"
        if value is not None:
            message += f" (value: {value})"
        
        super().__init__(message, context)


class ConfigurationError(CPHException):
    """設定関連エラー"""
    
    def __init__(self, config_key: str, message: str, 
                 config_file: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.config_key = config_key
        self.config_file = config_file
        
        full_message = f"Configuration error in '{config_key}': {message}"
        if config_file:
            full_message += f" (file: {config_file})"
        
        super().__init__(full_message, context)


class ExecutionError(CPHException):
    """実行時エラー"""
    
    def __init__(self, operation: str, message: str, 
                 exit_code: Optional[int] = None,
                 stdout: Optional[str] = None,
                 stderr: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        self.operation = operation
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        
        full_message = f"Execution failed in {operation}: {message}"
        if exit_code is not None:
            full_message += f" (exit code: {exit_code})"
        
        execution_context = context or {}
        if stdout:
            execution_context['stdout'] = stdout
        if stderr:
            execution_context['stderr'] = stderr
        
        super().__init__(full_message, execution_context, original_exception)


class ResourceError(CPHException):
    """リソース関連エラー"""
    
    def __init__(self, resource_type: str, resource_id: str, action: str, 
                 message: str, context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        
        full_message = f"Resource error: {action} failed for {resource_type} '{resource_id}': {message}"
        
        super().__init__(full_message, context, original_exception)


class DependencyError(CPHException):
    """依存関係エラー"""
    
    def __init__(self, dependency_type: str, message: str,
                 missing_dependencies: Optional[list] = None,
                 circular_dependencies: Optional[list] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.dependency_type = dependency_type
        self.missing_dependencies = missing_dependencies or []
        self.circular_dependencies = circular_dependencies or []
        
        full_message = f"Dependency error in {dependency_type}: {message}"
        
        dependency_context = context or {}
        if self.missing_dependencies:
            dependency_context['missing'] = self.missing_dependencies
        if self.circular_dependencies:
            dependency_context['circular'] = self.circular_dependencies
        
        super().__init__(full_message, dependency_context)


class OperationTimeoutError(ExecutionError):
    """操作タイムアウトエラー"""
    
    def __init__(self, operation: str, timeout_seconds: float,
                 context: Optional[Dict[str, Any]] = None):
        self.timeout_seconds = timeout_seconds
        
        message = f"Operation timed out after {timeout_seconds} seconds"
        timeout_context = context or {}
        timeout_context['timeout_seconds'] = timeout_seconds
        
        super().__init__(operation, message, context=timeout_context)


class AuthenticationError(CPHException):
    """認証エラー"""
    
    def __init__(self, auth_type: str, message: str,
                 context: Optional[Dict[str, Any]] = None):
        self.auth_type = auth_type
        
        full_message = f"Authentication failed for {auth_type}: {message}"
        
        super().__init__(full_message, context)


class PermissionError(CPHException):
    """権限エラー"""
    
    def __init__(self, resource: str, action: str, required_permission: str,
                 context: Optional[Dict[str, Any]] = None):
        self.resource = resource
        self.action = action
        self.required_permission = required_permission
        
        message = f"Permission denied: cannot {action} {resource} (requires {required_permission})"
        
        super().__init__(message, context)