"""
Error recovery mechanisms including retry, fallback, and circuit breaker patterns
"""
import time
import random
from typing import Any, Callable, Optional, Dict, List, Union
from enum import Enum
from .base_exceptions import CPHException, ExecutionError, OperationTimeoutError
from .error_logger import ErrorLogger, LogLevel


class RetryStrategy(Enum):
    """リトライ戦略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    JITTERED_BACKOFF = "jittered_backoff"


class CircuitBreakerState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "closed"      # 正常状態
    OPEN = "open"          # 失敗状態（呼び出し拒否）
    HALF_OPEN = "half_open"  # テスト状態


class RetryConfig:
    """リトライ設定"""
    
    def __init__(self, max_attempts: int = 3,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter_range: float = 0.1,
                 retryable_exceptions: Optional[List[type]] = None):
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter_range = jitter_range
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def calculate_delay(self, attempt: int) -> float:
        """リトライ遅延時間の計算"""
        if self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        elif self.strategy == RetryStrategy.JITTERED_BACKOFF:
            base_delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
            jitter = random.uniform(-self.jitter_range, self.jitter_range) * base_delay
            delay = base_delay + jitter
        else:
            delay = self.base_delay
        
        return min(delay, self.max_delay)
    
    def should_retry(self, exception: Exception) -> bool:
        """例外がリトライ対象かチェック"""
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)


class CircuitBreakerConfig:
    """サーキットブレーカー設定"""
    
    def __init__(self, failure_threshold: int = 5,
                 success_threshold: int = 3,
                 timeout_seconds: float = 60.0,
                 monitored_exceptions: Optional[List[type]] = None):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.monitored_exceptions = monitored_exceptions or [Exception]


class CircuitBreaker:
    """サーキットブレーカー実装"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.logger = ErrorLogger()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """関数呼び出しをサーキットブレーカーで保護"""
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time < self.config.timeout_seconds:
                raise ExecutionError(
                    "circuit_breaker",
                    f"Circuit breaker '{self.name}' is OPEN",
                    context={"circuit_breaker": self.name, "state": self.state.value}
                )
            else:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if self._should_monitor(e):
                self._on_failure()
            raise e
    
    def _should_monitor(self, exception: Exception) -> bool:
        """例外が監視対象かチェック"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.monitored_exceptions)
    
    def _on_success(self):
        """成功時の処理"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.logger.log_execution_success(
                    f"circuit_breaker_{self.name}",
                    0,
                    f"Circuit breaker closed after {self.success_count} successes"
                )
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN]:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.log_operation_error(
                    f"circuit_breaker_{self.name}",
                    ExecutionError(
                        "circuit_breaker",
                        f"Circuit breaker opened after {self.failure_count} failures"
                    ),
                    context={"circuit_breaker": self.name, "failure_count": self.failure_count}
                )
    
    def reset(self):
        """サーキットブレーカーをリセット"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0


class FallbackHandler:
    """フォールバック処理"""
    
    def __init__(self, fallback_func: Callable, 
                 fallback_exceptions: Optional[List[type]] = None):
        self.fallback_func = fallback_func
        self.fallback_exceptions = fallback_exceptions or [Exception]
    
    def call(self, primary_func: Callable, *args, **kwargs) -> Any:
        """プライマリ関数を実行し、失敗時にフォールバック"""
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            if self._should_fallback(e):
                return self.fallback_func(*args, **kwargs)
            raise e
    
    def _should_fallback(self, exception: Exception) -> bool:
        """例外がフォールバック対象かチェック"""
        return any(isinstance(exception, exc_type) for exc_type in self.fallback_exceptions)


class ErrorRecovery:
    """エラー回復機能の統合クラス"""
    
    def __init__(self, logger: Optional[ErrorLogger] = None):
        self.logger = logger or ErrorLogger()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def retry_with_config(self, func: Callable, config: RetryConfig,
                         operation_name: str, *args, **kwargs) -> Any:
        """設定に基づくリトライ実行"""
        last_exception = None
        
        for attempt in range(1, config.max_attempts + 1):
            try:
                if attempt > 1:
                    self.logger.log_execution_start(
                        f"{operation_name}_retry",
                        context={"attempt": attempt, "max_attempts": config.max_attempts}
                    )
                
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.logger.log_execution_success(
                        f"{operation_name}_retry",
                        0,
                        f"Succeeded on attempt {attempt}",
                        context={"attempt": attempt}
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt == config.max_attempts or not config.should_retry(e):
                    break
                
                delay = config.calculate_delay(attempt)
                
                self.logger.log_operation_error(
                    f"{operation_name}_retry_attempt",
                    e,
                    context={
                        "attempt": attempt,
                        "max_attempts": config.max_attempts,
                        "next_delay": delay
                    },
                    level=LogLevel.WARNING
                )
                
                time.sleep(delay)
        
        # 最終的に失敗
        self.logger.log_operation_error(
            f"{operation_name}_retry_failed",
            last_exception,
            context={
                "total_attempts": config.max_attempts,
                "final_exception": type(last_exception).__name__
            }
        )
        
        raise ExecutionError(
            operation_name,
            f"Operation failed after {config.max_attempts} attempts",
            context={"max_attempts": config.max_attempts},
            original_exception=last_exception
        )
    
    def retry(self, max_attempts: int = 3, delay: float = 1.0,
             backoff_factor: float = 2.0, operation_name: str = "operation"):
        """デコレーター形式のリトライ"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                config = RetryConfig(
                    max_attempts=max_attempts,
                    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                    base_delay=delay,
                    backoff_factor=backoff_factor
                )
                return self.retry_with_config(func, config, operation_name, *args, **kwargs)
            return wrapper
        return decorator
    
    def with_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """サーキットブレーカーデコレーター"""
        if name not in self.circuit_breakers:
            breaker_config = config or CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, breaker_config)
        
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                return self.circuit_breakers[name].call(func, *args, **kwargs)
            return wrapper
        return decorator
    
    def with_fallback(self, fallback_func: Callable, 
                     fallback_exceptions: Optional[List[type]] = None):
        """フォールバックデコレーター"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                handler = FallbackHandler(fallback_func, fallback_exceptions)
                return handler.call(func, *args, **kwargs)
            return wrapper
        return decorator
    
    def safe_execute(self, func: Callable, operation_name: str,
                    retry_config: Optional[RetryConfig] = None,
                    circuit_breaker_name: Optional[str] = None,
                    fallback_func: Optional[Callable] = None,
                    *args, **kwargs) -> Any:
        """安全な実行（リトライ、サーキットブレーカー、フォールバック対応）"""
        
        # 実行関数の準備
        execution_func = func
        
        # フォールバック適用
        if fallback_func:
            handler = FallbackHandler(fallback_func)
            execution_func = lambda *a, **kw: handler.call(func, *a, **kw)
        
        # サーキットブレーカー適用
        if circuit_breaker_name:
            if circuit_breaker_name not in self.circuit_breakers:
                self.circuit_breakers[circuit_breaker_name] = CircuitBreaker(
                    circuit_breaker_name, CircuitBreakerConfig()
                )
            
            breaker = self.circuit_breakers[circuit_breaker_name]
            execution_func = lambda *a, **kw: breaker.call(execution_func, *a, **kw)
        
        # リトライ適用
        if retry_config:
            return self.retry_with_config(execution_func, retry_config, operation_name, *args, **kwargs)
        else:
            return execution_func(*args, **kwargs)
    
    def reset_circuit_breaker(self, name: str):
        """サーキットブレーカーのリセット"""
        if name in self.circuit_breakers:
            self.circuit_breakers[name].reset()
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """すべてのサーキットブレーカーの状態を取得"""
        status = {}
        for name, breaker in self.circuit_breakers.items():
            status[name] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count,
                "last_failure_time": breaker.last_failure_time
            }
        return status


# グローバルインスタンス
default_recovery = ErrorRecovery()


def retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """グローバルリトライデコレーター"""
    return default_recovery.retry(max_attempts, delay, backoff_factor)


def with_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """グローバルサーキットブレーカーデコレーター"""
    return default_recovery.with_circuit_breaker(name, config)


def with_fallback(fallback_func: Callable, fallback_exceptions: Optional[List[type]] = None):
    """グローバルフォールバックデコレーター"""
    return default_recovery.with_fallback(fallback_func, fallback_exceptions)