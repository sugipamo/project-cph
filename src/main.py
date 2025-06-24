"""Main entry point for the CPH application
"""
from src.cli.cli_app import main
from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.build_infrastructure import build_infrastructure
from src.infrastructure.di_container import DIKey
from src.infrastructure.drivers.docker.utils.docker_command_builder import set_config_manager

if __name__ == "__main__":
    infrastructure = build_infrastructure()

    # Docker command builderに設定マネージャーを注入
    config_manager = TypeSafeConfigNodeManager(infrastructure)
    # CONFIG_MANAGERをinfrastructureに登録（クリーンアーキテクチャ準拠）
    infrastructure.register("CONFIG_MANAGER", lambda: config_manager)
    infrastructure.register(DIKey.CONFIG_MANAGER, lambda: config_manager)

    # file_request_factoryの登録（依存性注入強化）
    from src.operations.factories.request_factory import RequestFactory

    # RequestFactoryに必要な依存関係を注入
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

    # 初期化時は仮の言語で読み込み（user_input_parserで実際の言語解決後に再読み込み）
    config_manager.load_from_files(
        system_dir="./config/system",
        env_dir="./contest_env",
        language="python"  # 仮の言語（CLIで実際の言語解決後に更新される）
    )
    set_config_manager(config_manager)

    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    exit_code = main(sys_provider.get_argv()[1:], sys_provider.exit, infrastructure)
    sys_provider.exit(exit_code)
