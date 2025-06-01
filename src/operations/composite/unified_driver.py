"""
Unified driver that resolves appropriate driver based on request type
"""
from typing import Any, Optional
from src.operations.constants.operation_type import OperationType


class UnifiedDriver:
    """
    統合ドライバー：リクエストタイプに基づいて適切なドライバーを解決
    """
    
    def __init__(self, operations):
        """
        Args:
            operations: DIContainer or operations object with resolve method
        """
        self.operations = operations
        self._driver_cache = {}
    
    def execute(self, request) -> Any:
        """
        リクエストを実行（適切なドライバーを自動選択）
        
        Args:
            request: 実行するリクエスト
            
        Returns:
            実行結果
        """
        # Get appropriate driver based on request type
        driver = self._get_driver_for_request(request)
        
        # Execute request with the driver
        return request.execute(driver=driver)
    
    def _get_driver_for_request(self, request) -> Any:
        """
        リクエストタイプに基づいて適切なドライバーを取得
        
        Args:
            request: リクエストオブジェクト
            
        Returns:
            適切なドライバー
        """
        operation_type = getattr(request, 'operation_type', None)
        
        if operation_type == OperationType.FILE:
            return self._get_cached_driver("file_driver")
        elif operation_type == OperationType.SHELL:
            return self._get_cached_driver("shell_driver")
        elif operation_type == OperationType.DOCKER:
            return self._get_cached_driver("docker_driver")
        elif operation_type == OperationType.PYTHON:
            return self._get_cached_driver("python_driver")
        else:
            # Fallback: return self for composite/unknown types
            return self
    
    def _get_cached_driver(self, driver_name: str) -> Any:
        """
        キャッシュされたドライバーを取得（パフォーマンス最適化）
        
        Args:
            driver_name: ドライバー名
            
        Returns:
            ドライバーインスタンス
        """
        if driver_name not in self._driver_cache:
            self._driver_cache[driver_name] = self.operations.resolve(driver_name)
        return self._driver_cache[driver_name]
    
    # Docker driver methods
    def exec_in_container(self, *args, **kwargs):
        """Execute command in container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.exec_in_container(*args, **kwargs)
    
    def run_container(self, *args, **kwargs):
        """Run container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.run_container(*args, **kwargs)
    
    def stop_container(self, *args, **kwargs):
        """Stop container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.stop_container(*args, **kwargs)
    
    def remove_container(self, *args, **kwargs):
        """Remove container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.remove_container(*args, **kwargs)
    
    def inspect(self, *args, **kwargs):
        """Inspect container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.inspect(*args, **kwargs)
    
    def get_logs(self, *args, **kwargs):
        """Get container logs using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.get_logs(*args, **kwargs)
    
    def build(self, *args, **kwargs):
        """Build image using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.build(*args, **kwargs)
    
    def cp(self, *args, **kwargs):
        """Copy files to/from container using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.cp(*args, **kwargs)
    
    def ps(self, *args, **kwargs):
        """List containers using docker driver"""
        docker_driver = self._get_cached_driver("docker_driver")
        return docker_driver.ps(*args, **kwargs)
    
    # Delegate all other method calls to operations
    def __getattr__(self, name):
        """他のメソッド呼び出しをoperationsに委譲"""
        return getattr(self.operations, name)