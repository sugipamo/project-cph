"""Dependency injection configuration with lazy loading."""
from pathlib import Path
from typing import Any

from src.infrastructure.di_container import DIContainer, DIKey


def _create_shell_driver() -> Any:
    """Lazy factory for shell driver."""
    from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
    return LocalShellDriver()


def _create_docker_driver() -> Any:
    """Lazy factory for docker driver."""
    from src.infrastructure.drivers.docker.docker_driver import LocalDockerDriver
    return LocalDockerDriver()


def _create_file_driver() -> Any:
    """Lazy factory for file driver."""
    from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
    return LocalFileDriver(base_dir=Path('.'))


def _create_python_driver() -> Any:
    """Lazy factory for python driver."""
    from src.infrastructure.drivers.python.python_driver import LocalPythonDriver
    return LocalPythonDriver()


def _create_persistence_driver() -> Any:
    """Lazy factory for persistence driver."""
    from src.infrastructure.drivers.persistence.persistence_driver import SQLitePersistenceDriver
    return SQLitePersistenceDriver()


def _create_sqlite_manager() -> Any:
    """Lazy factory for SQLite manager (legacy)."""
    from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager
    return SQLiteManager()


def _create_operation_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for operation repository."""
    from src.infrastructure.persistence.sqlite.repositories.operation_repository import OperationRepository
    return OperationRepository(sqlite_manager)


def _create_session_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for session repository."""
    from src.infrastructure.persistence.sqlite.repositories.session_repository import SessionRepository
    return SessionRepository(sqlite_manager)


def _create_docker_container_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for docker container repository."""
    from src.infrastructure.persistence.sqlite.repositories.docker_container_repository import DockerContainerRepository
    return DockerContainerRepository(sqlite_manager)


def _create_docker_image_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for docker image repository."""
    from src.infrastructure.persistence.sqlite.repositories.docker_image_repository import DockerImageRepository
    return DockerImageRepository(sqlite_manager)


def _create_system_config_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for system config repository."""
    from src.infrastructure.persistence.sqlite.repositories.system_config_repository import SystemConfigRepository
    return SystemConfigRepository(sqlite_manager)


def _create_unified_driver(container: DIContainer) -> Any:
    """Lazy factory for unified driver."""
    from src.application.orchestration.unified_driver import UnifiedDriver
    return UnifiedDriver(container)


def _create_execution_controller() -> Any:
    """Lazy factory for execution controller."""
    from src.application.orchestration.execution_controller import ExecutionController
    return ExecutionController()


def _create_output_manager() -> Any:
    """Lazy factory for output manager."""
    from src.application.orchestration.output_manager import OutputManager
    return OutputManager()


def _create_environment_manager() -> Any:
    """Lazy factory for environment manager."""
    from src.infrastructure.environment.environment_manager import EnvironmentManager
    return EnvironmentManager()


def _create_request_factory() -> Any:
    """Lazy factory for request factory."""
    from src.application.factories.unified_request_factory import UnifiedRequestFactory
    return UnifiedRequestFactory()


def configure_production_dependencies(container: DIContainer) -> None:
    """Configure production dependencies with lazy loading."""
    # Register core drivers
    container.register(DIKey.SHELL_DRIVER, _create_shell_driver)
    container.register(DIKey.DOCKER_DRIVER, _create_docker_driver)
    container.register(DIKey.FILE_DRIVER, _create_file_driver)
    container.register(DIKey.PYTHON_DRIVER, _create_python_driver)
    container.register(DIKey.PERSISTENCE_DRIVER, _create_persistence_driver)

    # Register persistence layer (legacy support)
    container.register(DIKey.SQLITE_MANAGER, _create_sqlite_manager)
    container.register(DIKey.OPERATION_REPOSITORY, _create_operation_repository)
    container.register(DIKey.SESSION_REPOSITORY, _create_session_repository)
    container.register(DIKey.DOCKER_CONTAINER_REPOSITORY, _create_docker_container_repository)
    container.register(DIKey.DOCKER_IMAGE_REPOSITORY, _create_docker_image_repository)
    container.register(DIKey.SYSTEM_CONFIG_REPOSITORY, _create_system_config_repository)

    # Register orchestration layer
    container.register(DIKey.UNIFIED_DRIVER, lambda: _create_unified_driver(container))
    container.register(DIKey.EXECUTION_CONTROLLER, _create_execution_controller)
    container.register(DIKey.OUTPUT_MANAGER, _create_output_manager)

    # Register environment and factory
    container.register(DIKey.ENVIRONMENT_MANAGER, _create_environment_manager)
    container.register(DIKey.UNIFIED_REQUEST_FACTORY, _create_request_factory)

    # Register string-based aliases for backward compatibility
    container.register('shell_driver', lambda: container.resolve(DIKey.SHELL_DRIVER))
    container.register('docker_driver', lambda: container.resolve(DIKey.DOCKER_DRIVER))
    container.register('file_driver', lambda: container.resolve(DIKey.FILE_DRIVER))
    container.register('python_driver', lambda: container.resolve(DIKey.PYTHON_DRIVER))
    container.register('persistence_driver', lambda: container.resolve(DIKey.PERSISTENCE_DRIVER))
    container.register('unified_driver', lambda: container.resolve(DIKey.UNIFIED_DRIVER))


def configure_test_dependencies(container: DIContainer) -> None:
    """Configure test dependencies with mocks."""
    # Import mock implementations lazily
    def _create_mock_file_driver():
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        return MockFileDriver(base_dir=Path('.'))

    def _create_mock_shell_driver():
        from src.infrastructure.mock.mock_shell_driver import MockShellDriver
        return MockShellDriver()

    def _create_mock_docker_driver():
        from src.infrastructure.mock.mock_docker_driver import MockDockerDriver
        return MockDockerDriver()

    def _create_mock_python_driver():
        from src.infrastructure.mock.mock_python_driver import MockPythonDriver
        return MockPythonDriver()

    def _create_test_sqlite_manager():
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
        return FastSQLiteManager(":memory:", skip_migrations=False)

    # Register mock drivers
    container.register(DIKey.SHELL_DRIVER, _create_mock_shell_driver)
    container.register(DIKey.DOCKER_DRIVER, _create_mock_docker_driver)
    container.register(DIKey.FILE_DRIVER, _create_mock_file_driver)
    container.register(DIKey.PYTHON_DRIVER, _create_mock_python_driver)

    # Register test persistence layer
    container.register(DIKey.SQLITE_MANAGER, _create_test_sqlite_manager)
    container.register(DIKey.OPERATION_REPOSITORY, _create_operation_repository)
    container.register(DIKey.SESSION_REPOSITORY, _create_session_repository)
    container.register(DIKey.DOCKER_CONTAINER_REPOSITORY, _create_docker_container_repository)
    container.register(DIKey.DOCKER_IMAGE_REPOSITORY, _create_docker_image_repository)
    container.register(DIKey.SYSTEM_CONFIG_REPOSITORY, _create_system_config_repository)

    # Register orchestration layer
    container.register(DIKey.UNIFIED_DRIVER, lambda: _create_unified_driver(container))
    container.register(DIKey.EXECUTION_CONTROLLER, _create_execution_controller)
    container.register(DIKey.OUTPUT_MANAGER, _create_output_manager)

    # Register environment and factory
    container.register(DIKey.ENVIRONMENT_MANAGER, _create_environment_manager)
    container.register(DIKey.UNIFIED_REQUEST_FACTORY, _create_request_factory)

    # Register string-based aliases for backward compatibility
    container.register('shell_driver', lambda: container.resolve(DIKey.SHELL_DRIVER))
    container.register('docker_driver', lambda: container.resolve(DIKey.DOCKER_DRIVER))
    container.register('file_driver', lambda: container.resolve(DIKey.FILE_DRIVER))
    container.register('python_driver', lambda: container.resolve(DIKey.PYTHON_DRIVER))
    container.register('persistence_driver', lambda: container.resolve(DIKey.PERSISTENCE_DRIVER))
    container.register('unified_driver', lambda: container.resolve(DIKey.UNIFIED_DRIVER))
