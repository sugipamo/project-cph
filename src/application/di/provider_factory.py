"""プロバイダーファクトリー - DIコンテナで副作用プロバイダーを管理"""
from typing import Any, Dict, Optional

from src.infrastructure.config.unified_config_loader import UnifiedConfigLoader
from src.infrastructure.drivers.logging import ConsoleLogger, SystemConsoleLogger
from src.infrastructure.providers import (
    EnvironmentProvider,
    FileProvider,
    LanguageRegistryProvider,
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

        # 言語レジストリプロバイダー
        self._providers['language_registry'] = LanguageRegistryProvider(
            self._providers['registry']
        )

        # コンソールロガー
        self._providers['console_logger'] = SystemConsoleLogger()

        # 統合設定ローダー
        from pathlib import Path
        self._providers['config_loader'] = UnifiedConfigLoader(
            contest_env_dir=Path("./contest_env"),
            system_config_dir=Path("./config/system"),
            file_provider=self._providers['file']
        )

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
        self._providers['language_registry'] = LanguageRegistryProvider(
            self._providers['registry']
        )
        self._providers['console_logger'] = MockConsoleLogger()

        # モック設定ローダー
        from pathlib import Path
        self._providers['config_loader'] = UnifiedConfigLoader(
            contest_env_dir=Path("./mock_contest_env"),
            system_config_dir=Path("./mock_config/system"),
            file_provider=self._providers['file']
        )

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

    def get_language_registry_provider(self) -> LanguageRegistryProvider:
        """言語レジストリプロバイダーを取得"""
        return self._providers['language_registry']

    def get_console_logger(self) -> ConsoleLogger:
        """コンソールロガーを取得"""
        return self._providers['console_logger']

    def get_config_loader(self) -> UnifiedConfigLoader:
        """統合設定ローダーを取得"""
        return self._providers['config_loader']

    def reset_providers(self) -> None:
        """プロバイダーをリセット（テスト用）"""
        self._providers.clear()
        self._initialize_providers()


# グローバルファクトリーインスタンス（アプリケーション起動時に初期化）
_global_factory: Optional[ProviderFactory] = None


def initialize_providers(use_mocks: bool = False) -> None:
    """グローバルプロバイダーファクトリーを初期化"""
    global _global_factory
    _global_factory = ProviderFactory(use_mocks=use_mocks)


def get_provider_factory() -> ProviderFactory:
    """グローバルプロバイダーファクトリーを取得"""
    global _global_factory
    if _global_factory is None:
        _global_factory = ProviderFactory()
    return _global_factory


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
