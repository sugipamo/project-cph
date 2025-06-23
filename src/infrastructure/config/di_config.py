"""Dependency injection configuration with lazy loading."""
from pathlib import Path
from typing import Any

from src.infrastructure.di_container import DIContainer, DIKey


def _create_shell_driver(file_driver: Any) -> Any:
    """Lazy factory for shell driver."""
    from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
    return LocalShellDriver(file_driver=file_driver)


def _create_docker_driver(container: Any) -> Any:
    """Lazy factory for docker driver."""
    from src.infrastructure.drivers.docker.docker_driver import LocalDockerDriver
    file_driver = container.resolve(DIKey.FILE_DRIVER)
    return LocalDockerDriver(file_driver)


def _create_file_driver() -> Any:
    """Lazy factory for file driver."""
    from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
    return LocalFileDriver(base_dir=Path('.'))


def _create_python_driver(container: Any) -> Any:
    """Lazy factory for python driver."""
    from src.infrastructure.drivers.python.python_driver import LocalPythonDriver
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    return LocalPythonDriver(config_manager)


def _create_persistence_driver() -> Any:
    """Lazy factory for persistence driver."""
    from src.infrastructure.drivers.persistence.persistence_driver import SQLitePersistenceDriver
    return SQLitePersistenceDriver()


def _create_sqlite_manager(container: Any) -> Any:
    """Lazy factory for SQLite manager (legacy)."""
    from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager
    sqlite_provider = container.resolve(DIKey.SQLITE_PROVIDER)
    # Use the existing database path - no defaults allowed
    db_path = "./cph_history.db"
    return SQLiteManager(db_path=db_path, sqlite_provider=sqlite_provider)


def _create_operation_repository(container: Any) -> Any:
    """Lazy factory for operation repository."""
    from src.infrastructure.persistence.sqlite.repositories.operation_repository import OperationRepository
    sqlite_manager = container.resolve(DIKey.SQLITE_MANAGER)
    json_provider = container.resolve(DIKey.JSON_PROVIDER)
    return OperationRepository(sqlite_manager, json_provider=json_provider)


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


def _create_system_config_repository(container: Any) -> Any:
    """Lazy factory for system config repository."""
    from src.infrastructure.persistence.sqlite.repositories.system_config_repository import SystemConfigRepository
    sqlite_manager = container.resolve(DIKey.SQLITE_MANAGER)
    config_manager = container.resolve("json_config_loader")
    return SystemConfigRepository(sqlite_manager, config_manager)




def _create_unified_driver(container: DIContainer) -> Any:
    """Lazy factory for unified driver."""
    from src.infrastructure.drivers.unified.unified_driver import UnifiedDriver
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
    from src.infrastructure.environment.environment_manager import EnvironmentManager
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    logger = container.resolve(DIKey.LOGGER)
    return EnvironmentManager(env_type=None, config_manager=config_manager, logger=logger)


def _create_logger(container: Any) -> Any:
    """Lazy factory for logger (backward compatibility)."""
    # Use unified logger for compatibility with LoggerInterface
    return _create_unified_logger(container)


def _create_logging_output_manager() -> Any:
    """Lazy factory for logging output manager."""
    from src.infrastructure.drivers.logging import OutputManager
    from src.infrastructure.drivers.logging.types import LogLevel
    return OutputManager(name="output", level=LogLevel.DEBUG)


def _create_mock_logging_output_manager() -> Any:
    """Lazy factory for mock logging output manager."""
    from src.infrastructure.drivers.logging import MockOutputManager
    from src.infrastructure.drivers.logging.types import LogLevel
    return MockOutputManager(name="mock_output", level=LogLevel.DEBUG)


def _create_application_logger_adapter(container: Any) -> Any:
    """Lazy factory for application logger adapter."""
    from src.infrastructure.drivers.logging.adapters import ApplicationLoggerAdapter
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    return ApplicationLoggerAdapter(output_manager)


def _create_workflow_logger_adapter(container: Any) -> Any:
    """Lazy factory for workflow logger adapter."""
    from src.infrastructure.drivers.logging.adapters import WorkflowLoggerAdapter
    output_manager = container.resolve(DIKey.LOGGING_OUTPUT_MANAGER)
    return WorkflowLoggerAdapter(output_manager)


def _create_unified_logger(container: Any) -> Any:
    """Lazy factory for unified logger."""
    from src.infrastructure.drivers.logging import UnifiedLogger
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
    from src.infrastructure.drivers.filesystem.local_filesystem import LocalFileSystem
    return LocalFileSystem()


def _create_request_factory(container: Any) -> Any:
    """Lazy factory for request factory with config manager injection."""
    # Get config manager from container
    from src.infrastructure.di_container import DIKey
    from src.operations.factories.request_factory import RequestFactory
    config_manager = container.resolve(DIKey.CONFIG_MANAGER)
    return RequestFactory(config_manager)


def _create_system_config_loader(container: Any) -> Any:
    """Lazy factory for system config loader."""
    from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader
    return SystemConfigLoader(container)




def _create_file_pattern_service(container: Any) -> Any:
    """Lazy factory for file pattern service - currently disabled."""
    # TODO: Restore when FilePatternService is available
    # from src.workflow.preparation.file.file_pattern_service import FilePatternService
    #
    # config_loader = container.resolve("json_config_loader")
    # file_driver = container.resolve("file_driver")
    # logger = container.resolve("logger")
    # return FilePatternService(config_loader, file_driver, logger)
    return None




def _create_json_config_loader(container: Any) -> Any:
    """Lazy factory for JSON config loader."""
    # 互換性維持: infrastructure層では設定マネージャーを直接作成すべきではない
    # main.pyから注入されるべき
    # クリーンアーキテクチャ違反回避: infrastructure層からconfiguration層への依存を削除
    # このファクトリは一時的に None を返す
    # TODO: main.pyで適切に設定マネージャーをセットアップしてください
    raise RuntimeError("CONFIG_MANAGERはmain.pyから注入されるべきです。クリーンアーキテクチャ違反を避けるため、infrastructure層からconfiguration層への直接依存を削除しました。")


def _create_contest_manager(container: Any) -> Any:
    """Lazy factory for contest manager."""
    from src.infrastructure.persistence.sqlite.contest_manager import ContestManager

    # For now, pass container and let ContestManager load env_json as needed
    # This avoids circular dependency issues
    return ContestManager(container, {})


def _create_json_provider() -> Any:
    """Lazy factory for JSON provider."""
    from src.infrastructure.providers import SystemJsonProvider
    return SystemJsonProvider()


def _create_sqlite_provider() -> Any:
    """Lazy factory for SQLite provider."""
    from src.infrastructure.providers import SystemSQLiteProvider
    return SystemSQLiteProvider()


def _create_mock_json_provider() -> Any:
    """Lazy factory for mock JSON provider."""
    from src.infrastructure.providers import MockJsonProvider
    return MockJsonProvider()


def _create_mock_sqlite_provider() -> Any:
    """Lazy factory for mock SQLite provider."""
    from src.infrastructure.providers import MockSQLiteProvider
    return MockSQLiteProvider()


def _create_configuration_repository(container: Any) -> Any:
    """Lazy factory for configuration repository."""
    from src.infrastructure.persistence.configuration_repository import ConfigurationRepository
    json_provider = container.resolve(DIKey.JSON_PROVIDER)
    sqlite_provider = container.resolve(DIKey.SQLITE_PROVIDER)
    return ConfigurationRepository(json_provider=json_provider, sqlite_provider=sqlite_provider)


def _create_os_provider() -> Any:
    """Lazy factory for OS provider."""
    from src.infrastructure.providers import SystemOsProvider
    return SystemOsProvider()


def _create_mock_os_provider() -> Any:
    """Lazy factory for mock OS provider."""
    from src.infrastructure.providers import MockOsProvider
    return MockOsProvider()


def _create_sys_provider() -> Any:
    """Lazy factory for sys provider."""
    from src.infrastructure.providers import SystemSysProvider
    return SystemSysProvider()


def _create_mock_sys_provider() -> Any:
    """Lazy factory for mock sys provider."""
    from src.infrastructure.providers import MockSysProvider
    return MockSysProvider(argv=["test_program"], platform="test")


def configure_production_dependencies(container: DIContainer) -> None:
    """Configure production dependencies with lazy loading."""
    # Register providers (副作用集約)
    container.register(DIKey.JSON_PROVIDER, _create_json_provider)
    container.register(DIKey.SQLITE_PROVIDER, _create_sqlite_provider)
    container.register(DIKey.OS_PROVIDER, _create_os_provider)
    container.register(DIKey.SYS_PROVIDER, _create_sys_provider)
    container.register(DIKey.CONFIGURATION_REPOSITORY, lambda: _create_configuration_repository(container))

    # Register core drivers
    container.register(DIKey.SHELL_DRIVER, lambda: _create_shell_driver(container.resolve(DIKey.FILE_DRIVER)))
    container.register(DIKey.DOCKER_DRIVER, lambda: _create_docker_driver(container))
    container.register(DIKey.FILE_DRIVER, _create_file_driver)
    container.register(DIKey.PYTHON_DRIVER, lambda: _create_python_driver(container))
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
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        return MockFileDriver(base_dir=Path('.'))

    def _create_mock_shell_driver(file_driver):
        from src.infrastructure.mock.mock_shell_driver import MockShellDriver
        return MockShellDriver(file_driver=file_driver)

    def _create_mock_docker_driver():
        from src.infrastructure.mock.mock_docker_driver import MockDockerDriver
        json_provider = container.resolve(DIKey.JSON_PROVIDER)
        return MockDockerDriver(json_provider=json_provider)

    def _create_mock_python_driver():
        from src.infrastructure.mock.mock_python_driver import MockPythonDriver
        return MockPythonDriver()

    container.register(DIKey.SHELL_DRIVER, lambda: _create_mock_shell_driver(container.resolve(DIKey.FILE_DRIVER)))
    container.register(DIKey.DOCKER_DRIVER, _create_mock_docker_driver)
    container.register(DIKey.FILE_DRIVER, _create_mock_file_driver)
    container.register(DIKey.PYTHON_DRIVER, _create_mock_python_driver)

def _register_test_persistence(container: DIContainer) -> None:
    """Register test persistence layer."""
    def _create_test_sqlite_manager():
        from src.infrastructure.persistence.sqlite.fast_sqlite_manager import FastSQLiteManager
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

def _register_environment_and_factory(container: DIContainer) -> None:
    """Register environment and factory."""
    container.register(DIKey.ENVIRONMENT_MANAGER, lambda: _create_environment_manager(container))
    container.register(DIKey.UNIFIED_REQUEST_FACTORY, lambda: _create_request_factory(container))

def _register_mock_interfaces(container: DIContainer) -> None:
    """Register mock interfaces."""
    def _create_mock_logger():
        return lambda: _create_unified_logger(container)

    def _create_mock_filesystem():
        from tests.base.mock_filesystem import MockFileSystem
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
