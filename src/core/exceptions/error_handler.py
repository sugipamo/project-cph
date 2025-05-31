"""
Centralized error handling utilities
"""
import time
import traceback
from typing import Any, Dict, Optional, Type, Union, Callable
from .base_exceptions import *
from .message_formatter import ErrorMessageFormatter
from src.operations.result import OperationResult


class ErrorHandler:
    """統一されたエラーハンドラー"""
    
    @staticmethod
    def handle_operation_error(operation: str, error: Exception, 
                             context: Optional[Dict[str, Any]] = None) -> OperationResult:
        """操作エラーの統一処理"""
        error_message = ErrorMessageFormatter.execution_error(operation, str(error))
        
        # 特定の例外タイプに基づく詳細情報の抽出
        exit_code = getattr(error, 'returncode', -1)
        stdout = getattr(error, 'stdout', None)
        stderr = getattr(error, 'stderr', None)
        
        # Add context to metadata if provided
        metadata = context.copy() if context else {}
        
        return OperationResult(
            success=False,
            error_message=error_message,
            exception=error,
            returncode=exit_code,
            stdout=stdout,
            stderr=stderr,
            metadata=metadata
        )
    
    @staticmethod
    def handle_validation_error(field: str, reason: str, value: Any = None,
                               context: Optional[Dict[str, Any]] = None) -> ValidationError:
        """バリデーションエラーの統一処理"""
        return ValidationError(field, reason, value, context)
    
    @staticmethod
    def handle_configuration_error(config_key: str, reason: str,
                                  config_file: Optional[str] = None,
                                  context: Optional[Dict[str, Any]] = None) -> ConfigurationError:
        """設定エラーの統一処理"""
        return ConfigurationError(config_key, reason, config_file, context)
    
    @staticmethod
    def handle_resource_error(resource_type: str, resource_id: str, action: str,
                            reason: str, context: Optional[Dict[str, Any]] = None,
                            original_exception: Optional[Exception] = None) -> ResourceError:
        """リソースエラーの統一処理"""
        return ResourceError(resource_type, resource_id, action, reason, context, original_exception)
    
    @staticmethod
    def handle_file_operation_error(operation: str, file_path: str, error: Exception,
                                  context: Optional[Dict[str, Any]] = None) -> ExecutionError:
        """ファイル操作エラーの統一処理"""
        message = ErrorMessageFormatter.format_file_operation_error(operation, file_path, str(error))
        
        file_context = context or {}
        file_context.update({
            'file_path': file_path,
            'operation': operation
        })
        
        return ExecutionError(f"file_{operation}", message, context=file_context, original_exception=error)
    
    @staticmethod
    def handle_shell_execution_error(command: Union[str, list], error: Exception,
                                   working_dir: Optional[str] = None,
                                   context: Optional[Dict[str, Any]] = None) -> ExecutionError:
        """シェル実行エラーの統一処理"""
        cmd_str = " ".join(command) if isinstance(command, list) else command
        
        shell_context = context or {}
        shell_context.update({
            'command': cmd_str,
            'working_dir': working_dir
        })
        
        # subprocess.CalledProcessError などの詳細情報を抽出
        exit_code = getattr(error, 'returncode', -1)
        stdout = getattr(error, 'stdout', None)
        stderr = getattr(error, 'stderr', None)
        
        return ExecutionError(
            "shell_execution",
            f"Shell command failed: {str(error)}",
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            context=shell_context,
            original_exception=error
        )
    
    @staticmethod
    def handle_docker_operation_error(operation: str, container_or_image: str,
                                    error: Exception, context: Optional[Dict[str, Any]] = None) -> ExecutionError:
        """Docker操作エラーの統一処理"""
        docker_context = context or {}
        docker_context.update({
            'docker_operation': operation,
            'target': container_or_image
        })
        
        return ExecutionError(
            f"docker_{operation}",
            f"Docker {operation} failed for '{container_or_image}': {str(error)}",
            context=docker_context,
            original_exception=error
        )
    
    @staticmethod
    def handle_timeout_error(operation: str, timeout_seconds: float,
                           context: Optional[Dict[str, Any]] = None) -> OperationTimeoutError:
        """タイムアウトエラーの統一処理"""
        return OperationTimeoutError(operation, timeout_seconds, context)
    
    @staticmethod
    def wrap_exception(func: Callable, operation_name: str,
                      error_handler: Optional[Callable[[Exception], Exception]] = None,
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """関数実行をエラーハンドリングでラップ"""
        try:
            return func()
        except Exception as e:
            if error_handler:
                raise error_handler(e)
            else:
                # デフォルトのエラーハンドリング
                raise ExecutionError(
                    operation_name,
                    f"Operation failed: {str(e)}",
                    context=context,
                    original_exception=e
                )
    
    @staticmethod
    def convert_to_operation_result(func: Callable, operation_name: str,
                                  context: Optional[Dict[str, Any]] = None) -> OperationResult:
        """関数実行結果をOperationResultに変換"""
        start_time = time.time()
        
        try:
            result = func()
            # Add context to metadata if provided
            metadata = context.copy() if context else {}
            
            return OperationResult(
                success=True,
                start_time=start_time,
                end_time=time.time(),
                metadata=metadata
            )
        except Exception as e:
            return ErrorHandler.handle_operation_error(operation_name, e, context)
    
    @staticmethod
    def create_error_context(operation: str, **kwargs) -> Dict[str, Any]:
        """エラーコンテキストの作成"""
        context = {
            'operation': operation,
            'timestamp': time.time()
        }
        context.update(kwargs)
        return context
    
    @staticmethod
    def get_root_cause(exception: Exception) -> Exception:
        """例外の根本原因を取得"""
        current = exception
        while hasattr(current, 'original_exception') and current.original_exception:
            current = current.original_exception
        return current
    
    @staticmethod
    def format_exception_chain(exception: Exception) -> str:
        """例外チェーンのフォーマット"""
        chain = []
        current = exception
        
        while current:
            chain.append(f"{type(current).__name__}: {str(current)}")
            if hasattr(current, 'original_exception'):
                current = current.original_exception
            else:
                current = getattr(current, '__cause__', None) or getattr(current, '__context__', None)
        
        return " -> ".join(chain)