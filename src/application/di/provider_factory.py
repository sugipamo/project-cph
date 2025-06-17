"""プロバイダーファクトリー - DIコンテナで副作用プロバイダーを管理"""
from typing import Any, Dict

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.drivers.logging import ConsoleLogger, SystemConsoleLogger
from src.infrastructure.providers import (
    EnvironmentProvider,
    FileProvider,
    RegistryProvider,
    SystemEnvironmentProvider,
    SystemFileProvider,
    SystemRegistryProvider,
    SystemTimeProvider,
    SystemWorkingDirectoryProvider,
    TimeProvider,
    WorkingDirectoryProvider,
)


class ProviderFactory:
    """副作用プロバイダーを一元管理するファクトリー"""

    def __init__(self, use_mocks: bool = False):
        self.use_mocks = use_mocks
        self._providers: Dict[str, Any] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """プロバイダーを初期化（副作用の起点）"""
        if self.use_mocks:
            self._initialize_mock_providers()
        else:
            self._initialize_system_providers()

    def _initialize_system_providers(self) -> None:
        """システムプロバイダーを初期化"""
        # ファイルプロバイダー
        self._providers['file'] = SystemFileProvider()

        # 時刻プロバイダー
        self._providers['time'] = SystemTimeProvider()

        # 環境変数プロバイダー
        self._providers['environment'] = SystemEnvironmentProvider()

        # ワーキングディレクトリプロバイダー
        self._providers['working_directory'] = SystemWorkingDirectoryProvider()

        # レジストリプロバイダー
        self._providers['registry'] = SystemRegistryProvider()


        # コンソールロガー
        self._providers['console_logger'] = SystemConsoleLogger()

        # 統合設定マネージャー
        self._providers['config_manager'] = TypeSafeConfigNodeManager()

    def _initialize_mock_providers(self) -> None:
        """モックプロバイダーを初期化（テスト用）"""
        from src.infrastructure.drivers.logging import MockConsoleLogger
        from src.infrastructure.providers import (
            MockEnvironmentProvider,
            MockFileProvider,
            MockRegistryProvider,
            MockTimeProvider,
            MockWorkingDirectoryProvider,
        )

        # モックプロバイダー
        self._providers['file'] = MockFileProvider()
        self._providers['time'] = MockTimeProvider()
        self._providers['environment'] = MockEnvironmentProvider()
        self._providers['working_directory'] = MockWorkingDirectoryProvider()
        self._providers['registry'] = MockRegistryProvider()
        self._providers['console_logger'] = MockConsoleLogger()

        # モック設定マネージャー
        self._providers['config_manager'] = TypeSafeConfigNodeManager()

    def get_file_provider(self) -> FileProvider:
        """ファイルプロバイダーを取得"""
        return self._providers['file']

    def get_time_provider(self) -> TimeProvider:
        """時刻プロバイダーを取得"""
        return self._providers['time']

    def get_environment_provider(self) -> EnvironmentProvider:
        """環境変数プロバイダーを取得"""
        return self._providers['environment']

    def get_working_directory_provider(self) -> WorkingDirectoryProvider:
        """ワーキングディレクトリプロバイダーを取得"""
        return self._providers['working_directory']

    def get_registry_provider(self) -> RegistryProvider:
        """レジストリプロバイダーを取得"""
        return self._providers['registry']


    def get_console_logger(self) -> ConsoleLogger:
        """コンソールロガーを取得"""
        return self._providers['console_logger']

    def get_config_manager(self) -> TypeSafeConfigNodeManager:
        """統合設定マネージャーを取得"""
        return self._providers['config_manager']

    def reset_providers(self) -> None:
        """プロバイダーをリセット（テスト用）"""
        self._providers.clear()
        self._initialize_providers()


def initialize_providers(use_mocks: bool = False) -> ProviderFactory:
    """プロバイダーファクトリーを初期化して返す"""
    return ProviderFactory(use_mocks=use_mocks)


def get_provider_factory(use_mocks: bool = False) -> ProviderFactory:
    """新しいプロバイダーファクトリーを取得"""
    return ProviderFactory(use_mocks=use_mocks)


# 便利関数
def get_file_provider() -> FileProvider:
    """ファイルプロバイダーを取得"""
    return get_provider_factory().get_file_provider()


def get_time_provider() -> TimeProvider:
    """時刻プロバイダーを取得"""
    return get_provider_factory().get_time_provider()


def get_environment_provider() -> EnvironmentProvider:
    """環境変数プロバイダーを取得"""
    return get_provider_factory().get_environment_provider()


def get_console_logger() -> ConsoleLogger:
    """コンソールロガーを取得"""
    return get_provider_factory().get_console_logger()
