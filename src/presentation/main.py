"""Main entry point for the CPH application

クリーンアーキテクチャに準拠した段階的初期化を実装：
1. Infrastructure層の基本サービス初期化
2. Configuration層の純粋化された設定管理
3. 上位層への依存性注入
"""
from src.operations.results.__init__ import main
from src.application.pure_config_manager import PureConfigManager
from src.operations.results.__init__ import build_infrastructure
from src.application.services.config_loader_service import ConfigLoaderService
from src.infrastructure.di_container import DIKey
from src.presentation.docker_command_builder import set_config_manager

if __name__ == "__main__":
    # Phase 1: Infrastructure層の基本サービス初期化（循環依存なし）
    infrastructure = build_infrastructure()

    # Phase 2: 設定ファイル読み込み（Infrastructure層で副作用処理）
    config_loader = ConfigLoaderService(infrastructure)
    config_dict = config_loader.load_config_files(
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"  # 仮の言語（CLIで実際の言語解決後に更新される）
    )

    # Phase 3: 純粋なConfiguration層の初期化（副作用なし）
    config_manager = PureConfigManager()
    config_manager.initialize_from_config_dict(
        config_dict=config_dict,
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"
    )

    # Phase 4: CONFIG_MANAGERをDIContainerに登録
    infrastructure.register("CONFIG_MANAGER", lambda: config_manager)
    infrastructure.register(DIKey.CONFIG_MANAGER, lambda: config_manager)

    # Phase 5: RequestFactoryの登録（依存性注入）
    from src.operations.requests.request_factory import RequestFactory

    def create_request_factory():
        return RequestFactory(
            config_manager=config_manager,
            error_converter=None,  # ErrorConverterの注入が必要な場合は後で追加
            result_factory=None,   # ResultFactoryの注入が必要な場合は後で追加
            os_provider=infrastructure.resolve(DIKey.OS_PROVIDER),
            python_utils=None,     # PythonUtilsの注入が必要な場合は後で追加
            json_provider=infrastructure.resolve(DIKey.JSON_PROVIDER),
            time_ops=None          # TimeOpsの注入が必要な場合は後で追加
        )

    infrastructure.register("file_request_factory", create_request_factory)

    # Phase 6: Docker command builderに設定マネージャーを注入
    set_config_manager(config_manager)

    # Phase 7: アプリケーション実行（すべての依存性が解決済み）
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    exit_code = main(sys_provider.get_argv()[1:], sys_provider.exit, infrastructure)
    sys_provider.exit(exit_code)
