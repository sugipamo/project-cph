"""Unified driver that resolves appropriate driver based on request type
"""
from typing import Any

from src.domain.constants.operation_type import OperationType


class UnifiedDriver:
    """Unified driver: resolves appropriate driver based on request type
    """

    def __init__(self, operations):
        """Args:
        operations: DIContainer or operations object with resolve method
        """
        self.operations = operations
        self._driver_cache = {}

    def execute(self, request) -> Any:
        """Execute request (automatically select appropriate driver)

        Args:
            request: Request to execute

        Returns:
            Execution result
        """
        # Get appropriate driver based on request type
        driver = self._get_driver_for_request(request)

        # Execute request with the driver
        return request.execute(driver=driver)

    def _get_driver_for_request(self, request) -> Any:
        """Get appropriate driver based on request type

        Args:
            request: Request object

        Returns:
            Appropriate driver
        """
        operation_type = getattr(request, 'operation_type', None)

        if operation_type == OperationType.FILE:
            return self._get_cached_driver("file_driver")
        if operation_type == OperationType.SHELL:
            return self._get_cached_driver("shell_driver")
        if operation_type == OperationType.DOCKER:
            return self._get_cached_driver("docker_driver")
        if operation_type == OperationType.PYTHON:
            return self._get_cached_driver("python_driver")
        if operation_type == OperationType.STATE_SHOW:
            return self._get_cached_driver("file_driver")
        if operation_type == OperationType.WORKSPACE:
            return self._get_cached_driver("workspace_driver")
        # Fallback: return self for composite/unknown types
        return self

    def _get_cached_driver(self, driver_name: str) -> Any:
        """Get cached driver (performance optimization)

        Args:
            driver_name: Driver name

        Returns:
            Driver instance
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

    # Shell driver methods
    def run(self, *args, **kwargs):
        """Run shell command using shell driver"""
        shell_driver = self._get_cached_driver("shell_driver")
        return shell_driver.run(*args, **kwargs)

    # File driver methods
    def copy(self, *args, **kwargs):
        """Copy file using file driver"""
        file_driver = self._get_cached_driver("file_driver")
        return file_driver.copy(*args, **kwargs)

    def move(self, *args, **kwargs):
        """Move file using file driver"""
        file_driver = self._get_cached_driver("file_driver")
        return file_driver.move(*args, **kwargs)

    def exists(self, *args, **kwargs):
        """Check file existence using file driver"""
        file_driver = self._get_cached_driver("file_driver")
        return file_driver.exists(*args, **kwargs)
