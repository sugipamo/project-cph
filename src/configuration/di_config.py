"""Dependency injection configuration with lazy loading."""
from pathlib import Path
from typing import Any

from src.application.contest_manager import ContestManager
from src.application.fast_sqlite_manager import FastSQLiteManager
from src.application.mock_output_manager import MockOutputManager
from src.application.output_manager import OutputManager
from src.application.sqlite_manager import SQLiteManager
from src.configuration.configuration_repository import ConfigurationRepository
from src.configuration.environment_manager import EnvironmentManager
from src.configuration.system_config_repository import SystemConfigRepository
from src.data.docker_image.docker_image_repository import DockerImageRepository
from src.data.operation.operation_repository import OperationRepository
from src.domain.workflow_logger_adapter import WorkflowLoggerAdapter
from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.drivers.docker.docker_driver import DockerDriver
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
from src.infrastructure.drivers.generic.unified_driver import UnifiedDriver
from src.infrastructure.drivers.python.python_driver import LocalPythonDriver
from src.infrastructure.drivers.shell_python_driver import LocalShellPythonDriver
from src_check.mocks.drivers.mock_docker_driver import MockDockerDriver
from src_check.mocks.drivers.mock_file_driver import MockFileDriver
from src_check.mocks.drivers.mock_python_driver import MockPythonDriver
from src_check.mocks.drivers.mock_shell_driver import MockShellDriver
from src.infrastructure.json_provider import MockJsonProvider, SystemJsonProvider
from src.infrastructure.os_provider import MockOsProvider, SystemOsProvider
from src.infrastructure.sqlite_provider import MockSQLiteProvider, SystemSQLiteProvider
from src.operations.requests.request_factory import RequestFactory
from src.operations.results.__init__ import (
    ApplicationLoggerAdapter,
    DockerContainerRepository,
    LocalFileSystem,
    LocalShellDriver,
    SessionRepository,
    SQLitePersistenceDriver,
    SystemConfigLoader,
    UnifiedLogger,
)
from src.utils.sys_provider import MockSysProvider, SystemSysProvider
from src.utils.types import LogLevel
from tests.base.mock_filesystem import MockFileSystem


def _create_shell_driver(file_driver: Any) -> Any:
    """Lazy factory for shell driver."""
    return LocalShellDriver(file_driver=file_driver)


def _create_docker_driver(container: Any) -> Any:
    """Lazy factory for docker driver with tracking."""
    file_driver = container.resolve(DIKey.FILE_DRIVER)
    return DockerDriver(file_driver, di_container=container)


def _create_file_driver() -> Any:
    """Lazy factory for file driver."""
    return LocalFileDriver(base_dir=Path('.'))


def _create_python_driver(container: Any) -> Any:
    """Lazy factory for python driver."""
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    return LocalPythonDriver(config_manager)


def _create_persistence_driver() -> Any:
    """Lazy factory for persistence driver."""
    return SQLitePersistenceDriver()


def _create_shell_python_driver(container: Any) -> Any:
    """Lazy factory for combined shell/python driver."""
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    file_driver = container.resolve(DIKey.FILE_DRIVER)
    return LocalShellPythonDriver(config_manager, file_driver)


def _create_sqlite_manager(container: Any) -> Any:
    """Lazy factory for SQLite manager (legacy)."""
    sqlite_provider = container.resolve(DIKey.SQLITE_PROVIDER)
    # Use the existing database path - no defaults allowed
    db_path = "./cph_history.db"
    return SQLiteManager(db_path=db_path, sqlite_provider=sqlite_provider)


def _create_operation_repository(container: Any) -> Any:
    """Lazy factory for operation repository."""
    sqlite_manager = container.resolve(DIKey.SQLITE_MANAGER)
    json_provider = container.resolve(DIKey.JSON_PROVIDER)
    return OperationRepository(sqlite_manager, json_provider=json_provider)


def _create_session_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for session repository."""
    return SessionRepository(sqlite_manager)


def _create_docker_container_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for docker container repository."""
    return DockerContainerRepository(sqlite_manager)


def _create_docker_image_repository(sqlite_manager: Any) -> Any:
    """Lazy factory for docker image repository."""
    return DockerImageRepository(sqlite_manager)


def _create_system_config_repository(container: Any) -> Any:
    """Lazy factory for system config repository."""
    sqlite_manager = container.resolve(DIKey.SQLITE_MANAGER)
    config_manager = container.resolve("json_config_loader")
    return SystemConfigRepository(sqlite_manager, config_manager)




def _create_unified_driver(container: DIContainer) -> Any:
    """Lazy factory for unified driver."""
    logger = container.resolve(DIKey.UNIFIED_LOGGER)
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    return UnifiedDriver(container, logger, config_manager)


def _create_execution_controller() -> Any:
    """Lazy factory for execution controller."""
    # ExecutionController has been removed - returning None for now
    # TODO: Implement if needed or remove this factory
    return None


def _create_output_manager() -> Any:
    """Lazy factory for output manager."""
    # OutputManager has been removed - returning None for now
    # TODO: Implement if needed or remove this factory
    return None


def _create_environment_manager(container: Any) -> Any:
    """Lazy factory for environment manager."""
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    logger = container.resolve(DIKey.LOGGER)
    return EnvironmentManager(env_type=None, config_manager=config_manager, logger=logger)


def _create_logger(container: Any) -> Any:
    """Lazy factory for logger (backward compatibility)."""
    # Use unified logger for compatibility with LoggerInterface
    return _create_unified_logger(container)


def _create_logging_output_manager() -> Any:
    """Lazy factory for logging output manager."""
    return OutputManager(name="output", level=LogLevel.DEBUG)


def _create_mock_logging_output_manager() -> Any:
    """Lazy factory for mock logging output manager."""
    return MockOutputManager(name="mock_output", level=LogLevel.DEBUG)


def _create_application_logger_adapter(container: Any) -> Any:
    """Lazy factory for application logger adapter."""
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    return ApplicationLoggerAdapter(output_manager)


def _create_workflow_logger_adapter(container: Any) -> Any:
    """Lazy factory for workflow logger adapter."""
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    return WorkflowLoggerAdapter(output_manager)


def _create_unified_logger(container: Any) -> Any:
    """Lazy factory for unified logger."""
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    logger_config = {
        "format": {
            "icons": {
                "debug": "🐛",
                "info": "ℹ️"
            }
        }
    }
    return UnifiedLogger(
        output_manager=output_manager,
        name="unified_logger",
        logger_config=logger_config,
        di_container=container
    )


def _create_filesystem() -> Any:
    """Lazy factory for filesystem."""
    return LocalFileSystem()


def _create_request_factory(container: Any) -> Any:
    """Lazy factory for request factory with config manager injection."""
    # Get config manager from container
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    return RequestFactory(config_manager)


def _create_system_config_loader(container: Any) -> Any:
    """Lazy factory for system config loader."""
    return SystemConfigLoader(container)




def _create_file_pattern_service(container: Any) -> Any:
    """Lazy factory for file pattern service - currently disabled."""
    return None


def _create_json_config_loader(container: Any) -> Any:
    """Lazy factory for JSON config loader."""
    # 互換性維持: main.pyから設定されるまでNoneを返す
    # CONFIG_MANAGERがmain.pyで適切に登録されている場合はそれを返す
    try:
        # main.pyで既に登録されている場合はそれを使用
        if container.is_registered("CONFIG_MANAGER"):
            return container.resolve("CONFIG_MANAGER")
    except Exception:
        pass

    # 登録されていない場合はNoneを返す（後でmain.pyから設定される）
    return None


def _create_contest_manager(container: Any) -> Any:
    """Lazy factory for contest manager."""

    # For now, pass container and let ContestManager load env_json as needed
    # This avoids circular dependency issues
    return ContestManager(container, {})


def _create_json_provider() -> Any:
    """Lazy factory for JSON provider."""
    return SystemJsonProvider()


def _create_sqlite_provider() -> Any:
    """Lazy factory for SQLite provider."""
    return SystemSQLiteProvider()


def _create_mock_json_provider() -> Any:
    """Lazy factory for mock JSON provider."""
    return MockJsonProvider()


def _create_mock_sqlite_provider() -> Any:
    """Lazy factory for mock SQLite provider."""
    return MockSQLiteProvider()


def _create_configuration_repository(container: Any) -> Any:
    """Lazy factory for configuration repository."""
    json_provider = container.resolve(DIKey.JSON_PROVIDER)
    sqlite_provider = container.resolve(DIKey.SQLITE_PROVIDER)
    return ConfigurationRepository(json_provider=json_provider, sqlite_provider=sqlite_provider)


def _create_os_provider() -> Any:
    """Lazy factory for OS provider."""
    return SystemOsProvider()


def _create_mock_os_provider() -> Any:
    """Lazy factory for mock OS provider."""
    return MockOsProvider()


def _create_sys_provider(container: Any) -> Any:
    """Lazy factory for sys provider."""

    # 循環依存を避けるため、基本的なloggerインターフェースを提供
    class BasicLogger:
        def info(self, msg: str): pass
        def debug(self, msg: str): pass
        def warning(self, msg: str): pass
        def error(self, msg: str): pass
        def critical(self, msg: str): pass
        def log(self, level: int, msg: str): pass

    return SystemSysProvider(BasicLogger())


def _create_mock_sys_provider() -> Any:
    """Lazy factory for mock sys provider."""
    return MockSysProvider(argv=["test_program"], platform="test")


def configure_production_dependencies(container: DIContainer) -> None:
    """Configure production dependencies with lazy loading."""
    # Register providers (副作用集約)
    container.register(DIKey.JSON_PROVIDER, _create_json_provider)
    container.register(DIKey.SQLITE_PROVIDER, _create_sqlite_provider)
    container.register(DIKey.OS_PROVIDER, _create_os_provider)
    container.register(DIKey.SYS_PROVIDER, lambda: _create_sys_provider(container))
    container.register(DIKey.CONFIGURATION_REPOSITORY, lambda: _create_configuration_repository(container))

    # Register core drivers
    container.register(DIKey.SHELL_PYTHON_DRIVER, lambda: _create_shell_python_driver(container))
    container.register(DIKey.SHELL_DRIVER, lambda: container.resolve(DIKey.SHELL_PYTHON_DRIVER))
    container.register(DIKey.PYTHON_DRIVER, lambda: container.resolve(DIKey.SHELL_PYTHON_DRIVER))
    container.register(DIKey.DOCKER_DRIVER, lambda: _create_docker_driver(container))
    container.register(DIKey.FILE_DRIVER, _create_file_driver)
    container.register(DIKey.PERSISTENCE_DRIVER, _create_persistence_driver)

    # Register persistence layer (legacy support)
    container.register(DIKey.SQLITE_MANAGER, lambda: _create_sqlite_manager(container))
    container.register(DIKey.OPERATION_REPOSITORY, lambda: _create_operation_repository(container))
    container.register(DIKey.SESSION_REPOSITORY, _create_session_repository)
    container.register(DIKey.DOCKER_CONTAINER_REPOSITORY, _create_docker_container_repository)
    container.register(DIKey.DOCKER_IMAGE_REPOSITORY, _create_docker_image_repository)
    container.register(DIKey.SYSTEM_CONFIG_REPOSITORY, lambda: _create_system_config_repository(container))

    # Register orchestration layer
    container.register(DIKey.UNIFIED_DRIVER, lambda: _create_unified_driver(container))
    container.register(DIKey.EXECUTION_CONTROLLER, _create_execution_controller)
    container.register(DIKey.OUTPUT_MANAGER, _create_output_manager)

    # Register logging layer
    container.register(DIKey.LOGGING_OUTPUT_MANAGER, _create_logging_output_manager)
    container.register(DIKey.APPLICATION_LOGGER, lambda: _create_application_logger_adapter(container))
    container.register(DIKey.WORKFLOW_LOGGER, lambda: _create_workflow_logger_adapter(container))
    container.register(DIKey.UNIFIED_LOGGER, lambda: _create_unified_logger(container))
    container.register(DIKey.LOGGER, lambda: _create_logger(container))

    # Register environment and factory
    container.register(DIKey.ENVIRONMENT_MANAGER, lambda: _create_environment_manager(container))
    container.register(DIKey.UNIFIED_REQUEST_FACTORY, lambda: _create_request_factory(container))
    container.register(DIKey.CONFIG_MANAGER, lambda: _create_json_config_loader(container))

    # Register interfaces
    container.register("logger", lambda: _create_logger(container))
    container.register("filesystem", _create_filesystem)

    # Register simplified workspace management
    container.register("json_config_loader", lambda: _create_json_config_loader(container))
    container.register("config_manager", lambda: _create_json_config_loader(container))  # config_managerエイリアスを追加
    container.register("system_config_loader", lambda: _create_system_config_loader(container))
    container.register("contest_manager", lambda: _create_contest_manager(container))

    # Register string-based aliases for backward compatibility
    container.register('shell_driver', lambda: container.resolve(DIKey.SHELL_DRIVER))
    container.register('docker_driver', lambda: container.resolve(DIKey.DOCKER_DRIVER))
    container.register('file_driver', lambda: container.resolve(DIKey.FILE_DRIVER))
    container.register('python_driver', lambda: container.resolve(DIKey.PYTHON_DRIVER))
    container.register('persistence_driver', lambda: container.resolve(DIKey.PERSISTENCE_DRIVER))
    container.register('unified_driver', lambda: container.resolve(DIKey.UNIFIED_DRIVER))
    container.register('sqlite_manager', lambda: container.resolve(DIKey.SQLITE_MANAGER))
    container.register('unified_logger', lambda: container.resolve(DIKey.UNIFIED_LOGGER))


def configure_test_dependencies(container: DIContainer) -> None:
    """Configure test dependencies with mocks."""
    _register_mock_providers(container)
    _register_mock_drivers(container)
    _register_test_persistence(container)
    _register_orchestration_layer(container)
    _register_test_logging(container)
    _register_environment_and_factory(container)
    _register_mock_interfaces(container)
    _register_workspace_management(container)
    _register_compatibility_aliases(container)

def _register_mock_providers(container: DIContainer) -> None:
    """Register mock providers."""
    container.register(DIKey.JSON_PROVIDER, _create_mock_json_provider)
    container.register(DIKey.SQLITE_PROVIDER, _create_mock_sqlite_provider)
    container.register(DIKey.OS_PROVIDER, _create_mock_os_provider)
    container.register(DIKey.SYS_PROVIDER, _create_mock_sys_provider)
    container.register(DIKey.CONFIGURATION_REPOSITORY, lambda: _create_configuration_repository(container))

def _register_mock_drivers(container: DIContainer) -> None:
    """Register mock drivers."""
    def _create_mock_file_driver():
        return MockFileDriver(base_dir=Path('.'))

    def _create_mock_shell_driver(file_driver):
        return MockShellDriver(file_driver=file_driver)

    def _create_mock_docker_driver():
        json_provider = container.resolve(DIKey.JSON_PROVIDER)
        return MockDockerDriver(json_provider=json_provider)

    def _create_mock_python_driver():
        return MockPythonDriver()

    container.register(DIKey.SHELL_DRIVER, lambda: _create_mock_shell_driver(container.resolve(DIKey.FILE_DRIVER)))
    container.register(DIKey.DOCKER_DRIVER, _create_mock_docker_driver)
    container.register(DIKey.FILE_DRIVER, _create_mock_file_driver)
    container.register(DIKey.PYTHON_DRIVER, _create_mock_python_driver)

def _register_test_persistence(container: DIContainer) -> None:
    """Register test persistence layer."""
    def _create_test_sqlite_manager():
        sqlite_provider = container.resolve(DIKey.SQLITE_PROVIDER)
        return FastSQLiteManager(":memory:", skip_migrations=False, sqlite_provider=sqlite_provider)

    container.register(DIKey.SQLITE_MANAGER, lambda: _create_test_sqlite_manager())
    container.register(DIKey.OPERATION_REPOSITORY, lambda: _create_operation_repository(container))
    container.register(DIKey.SESSION_REPOSITORY, _create_session_repository)
    container.register(DIKey.DOCKER_CONTAINER_REPOSITORY, _create_docker_container_repository)
    container.register(DIKey.DOCKER_IMAGE_REPOSITORY, _create_docker_image_repository)
    container.register(DIKey.SYSTEM_CONFIG_REPOSITORY, lambda: _create_system_config_repository(container))

def _register_orchestration_layer(container: DIContainer) -> None:
    """Register orchestration layer."""
    container.register(DIKey.UNIFIED_DRIVER, lambda: _create_unified_driver(container))
    container.register(DIKey.EXECUTION_CONTROLLER, _create_execution_controller)
    container.register(DIKey.OUTPUT_MANAGER, _create_output_manager)

def _register_test_logging(container: DIContainer) -> None:
    """Register test logging layer."""
    container.register(DIKey.LOGGING_OUTPUT_MANAGER, _create_mock_logging_output_manager)
    container.register(DIKey.APPLICATION_LOGGER, lambda: _create_application_logger_adapter(container))
    container.register(DIKey.WORKFLOW_LOGGER, lambda: _create_workflow_logger_adapter(container))
    container.register(DIKey.UNIFIED_LOGGER, lambda: _create_unified_logger(container))
    container.register(DIKey.LOGGER, lambda: _create_logger(container))

def _register_environment_and_factory(container: DIContainer) -> None:
    """Register environment and factory."""
    container.register(DIKey.ENVIRONMENT_MANAGER, lambda: _create_environment_manager(container))
    container.register(DIKey.UNIFIED_REQUEST_FACTORY, lambda: _create_request_factory(container))

def _register_mock_interfaces(container: DIContainer) -> None:
    """Register mock interfaces."""
    def _create_mock_logger():
        return lambda: _create_unified_logger(container)

    def _create_mock_filesystem():
        return MockFileSystem()

    container.register("logger", _create_mock_logger())
    container.register("filesystem", _create_mock_filesystem)

def _register_workspace_management(container: DIContainer) -> None:
    """Register simplified workspace management."""
    container.register("json_config_loader", lambda: _create_json_config_loader(container))
    container.register("config_manager", lambda: _create_json_config_loader(container))
    container.register("system_config_loader", lambda: _create_system_config_loader(container))
    container.register("contest_manager", lambda: _create_contest_manager(container))

def _register_compatibility_aliases(container: DIContainer) -> None:
    """Register string-based aliases for backward compatibility."""
    aliases = {
        'shell_driver': DIKey.SHELL_DRIVER,
        'docker_driver': DIKey.DOCKER_DRIVER,
        'file_driver': DIKey.FILE_DRIVER,
        'python_driver': DIKey.PYTHON_DRIVER,
        'persistence_driver': DIKey.PERSISTENCE_DRIVER,
        'unified_driver': DIKey.UNIFIED_DRIVER,
        'sqlite_manager': DIKey.SQLITE_MANAGER,
        'unified_logger': DIKey.UNIFIED_LOGGER
    }

    for alias, key in aliases.items():
        container.register(alias, lambda k=key: container.resolve(k))
