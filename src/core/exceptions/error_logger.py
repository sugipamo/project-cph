"""
Standardized error logging utilities
"""
import json
import time
import traceback
from typing import Any, Dict, Optional, Union
from enum import Enum


class LogLevel(Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorLogger:
    """統一されたエラーログ出力"""
    
    def __init__(self, enable_console: bool = True, enable_file: bool = False,
                 log_file: Optional[str] = None):
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.log_file = log_file
    
    def log_operation_error(self, operation: str, error: Exception, 
                          context: Optional[Dict[str, Any]] = None,
                          level: LogLevel = LogLevel.ERROR):
        """操作エラーのログ出力"""
        log_data = {
            'level': level.value,
            'type': 'operation_error',
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': time.time(),
            'traceback': traceback.format_exc() if level == LogLevel.CRITICAL else None
        }
        
        self._write_log(log_data)
    
    def log_validation_error(self, field: str, value: Any, reason: str,
                           context: Optional[Dict[str, Any]] = None,
                           level: LogLevel = LogLevel.WARNING):
        """バリデーションエラーのログ出力"""
        log_data = {
            'level': level.value,
            'type': 'validation_error',
            'field': field,
            'invalid_value': self._sanitize_value(value),
            'reason': reason,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def log_configuration_error(self, config_key: str, reason: str,
                              config_file: Optional[str] = None,
                              context: Optional[Dict[str, Any]] = None,
                              level: LogLevel = LogLevel.ERROR):
        """設定エラーのログ出力"""
        log_data = {
            'level': level.value,
            'type': 'configuration_error',
            'config_key': config_key,
            'config_file': config_file,
            'reason': reason,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def log_resource_error(self, resource_type: str, resource_id: str, action: str,
                         error: Union[str, Exception], context: Optional[Dict[str, Any]] = None,
                         level: LogLevel = LogLevel.ERROR):
        """リソースエラーのログ出力"""
        log_data = {
            'level': level.value,
            'type': 'resource_error',
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'error': str(error),
            'context': context or {},
            'timestamp': time.time()
        }
        
        if isinstance(error, Exception):
            log_data['error_type'] = type(error).__name__
        
        self._write_log(log_data)
    
    def log_execution_start(self, operation: str, context: Optional[Dict[str, Any]] = None):
        """実行開始のログ出力"""
        log_data = {
            'level': LogLevel.INFO.value,
            'type': 'execution_start',
            'operation': operation,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def log_execution_success(self, operation: str, duration: float,
                            result_summary: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None):
        """実行成功のログ出力"""
        log_data = {
            'level': LogLevel.INFO.value,
            'type': 'execution_success',
            'operation': operation,
            'duration_seconds': duration,
            'result_summary': result_summary,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def log_performance_warning(self, operation: str, duration: float, threshold: float,
                              context: Optional[Dict[str, Any]] = None):
        """パフォーマンス警告のログ出力"""
        log_data = {
            'level': LogLevel.WARNING.value,
            'type': 'performance_warning',
            'operation': operation,
            'duration_seconds': duration,
            'threshold_seconds': threshold,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def log_security_event(self, event_type: str, description: str,
                         severity: LogLevel = LogLevel.WARNING,
                         context: Optional[Dict[str, Any]] = None):
        """セキュリティイベントのログ出力"""
        log_data = {
            'level': severity.value,
            'type': 'security_event',
            'event_type': event_type,
            'description': description,
            'context': context or {},
            'timestamp': time.time()
        }
        
        self._write_log(log_data)
    
    def _write_log(self, log_data: Dict[str, Any]):
        """ログデータの出力"""
        if self.enable_console:
            self._write_console_log(log_data)
        
        if self.enable_file and self.log_file:
            self._write_file_log(log_data)
    
    def _write_console_log(self, log_data: Dict[str, Any]):
        """コンソールログの出力"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log_data['timestamp']))
        level = log_data['level']
        log_type = log_data['type']
        
        # レベルに応じた色付け（ANSIエスケープシーケンス）
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        reset_color = '\033[0m'
        
        color = colors.get(level, '')
        
        # 基本メッセージの構築
        if log_type == 'operation_error':
            message = f"Operation '{log_data['operation']}' failed: {log_data['error_message']}"
        elif log_type == 'validation_error':
            message = f"Validation failed for '{log_data['field']}': {log_data['reason']}"
        elif log_type == 'configuration_error':
            message = f"Configuration error in '{log_data['config_key']}': {log_data['reason']}"
        elif log_type == 'resource_error':
            message = f"Resource {log_data['action']} failed for {log_data['resource_type']} '{log_data['resource_id']}': {log_data['error']}"
        elif log_type == 'execution_start':
            message = f"Starting operation: {log_data['operation']}"
        elif log_type == 'execution_success':
            message = f"Operation '{log_data['operation']}' completed successfully in {log_data['duration_seconds']:.2f}s"
        elif log_type == 'performance_warning':
            message = f"Performance warning: {log_data['operation']} took {log_data['duration_seconds']:.2f}s (threshold: {log_data['threshold_seconds']:.2f}s)"
        elif log_type == 'security_event':
            message = f"Security event ({log_data['event_type']}): {log_data['description']}"
        else:
            message = f"Unknown log type: {log_type}"
        
        print(f"{color}[{timestamp}] {level} - {message}{reset_color}")
        
        # コンテキスト情報の出力（DEBUGレベルまたはERROR以上の場合）
        if level in ['DEBUG', 'ERROR', 'CRITICAL'] and log_data.get('context'):
            print(f"  Context: {json.dumps(log_data['context'], indent=2, default=str)}")
        
        # トレースバック情報の出力
        if log_data.get('traceback'):
            print(f"  Traceback:\n{log_data['traceback']}")
    
    def _write_file_log(self, log_data: Dict[str, Any]):
        """ファイルログの出力"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, default=str)
                f.write('\n')
        except Exception as e:
            # ファイル出力に失敗した場合はコンソールに出力
            print(f"Failed to write log to file {self.log_file}: {e}")
    
    def _sanitize_value(self, value: Any) -> Any:
        """値のサニタイズ（ログ出力用）"""
        if isinstance(value, str) and len(value) > 100:
            return value[:97] + "..."
        elif isinstance(value, (dict, list)) and len(str(value)) > 200:
            return f"{type(value).__name__}({len(value)} items)"
        else:
            return value


# グローバルロガーインスタンス
default_logger = ErrorLogger()


def log_operation_error(operation: str, error: Exception, context: Optional[Dict[str, Any]] = None):
    """操作エラーのログ出力（便利関数）"""
    default_logger.log_operation_error(operation, error, context)


def log_validation_error(field: str, value: Any, reason: str, context: Optional[Dict[str, Any]] = None):
    """バリデーションエラーのログ出力（便利関数）"""
    default_logger.log_validation_error(field, value, reason, context)


def log_execution_start(operation: str, context: Optional[Dict[str, Any]] = None):
    """実行開始のログ出力（便利関数）"""
    default_logger.log_execution_start(operation, context)


def log_execution_success(operation: str, duration: float, result_summary: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None):
    """実行成功のログ出力（便利関数）"""
    default_logger.log_execution_success(operation, duration, result_summary, context)