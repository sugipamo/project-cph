# 新設定システムの統合
from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.context.dockerfile_resolver import DockerfileResolver

# from .execution_context import ExecutionContext  # 新システムで置き換え済み
from src.context.parsers.validation_service import ValidationService
from src.context.resolver.config_resolver import create_config_root_from_dict, resolve_by_match_desc
from src.infrastructure.di_container import DIKey
from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest

CONTEST_ENV_DIR = "contest_env"


def _create_execution_config(command_type=None, language=None, contest_name=None,
                           problem_name=None, env_type=None, infrastructure=None):
    """新設定システムを使用してExecutionConfigを作成するヘルパー関数"""
    config_manager = TypeSafeConfigNodeManager(infrastructure)
    if language is None:
        raise ValueError("language parameter cannot be None")
    config_manager.load_from_files(
        system_dir="./config/system",
        env_dir=CONTEST_ENV_DIR,
        language=language
    )

    if contest_name is None:
        raise ValueError("contest_name parameter cannot be None")
    if problem_name is None:
        raise ValueError("problem_name parameter cannot be None")
    if language is None:
        raise ValueError("language parameter cannot be None")
    if env_type is None:
        raise ValueError("env_type parameter cannot be None")
    if command_type is None:
        raise ValueError("command_type parameter cannot be None")
    context = config_manager.create_execution_config(
        contest_name=contest_name,
        problem_name=problem_name,
        language=language,
        env_type=env_type,
        command_type=command_type
    )

    return context


def _load_current_context_sqlite(infrastructure):
    """SQLiteから現在のコンテキスト情報を読み込む"""
    # infrastructure IS the container in this context
    config_loader = SystemConfigLoader(infrastructure)

    context = config_loader.get_current_context()
    config_loader.load_config()

    return {
        "command": context["command"],
        "language": context["language"],
        "env_type": context["env_type"],
        "contest_name": context["contest_name"],
        "problem_name": context["problem_name"],
    }


def _save_current_context_sqlite(infrastructure, context_info):
    """SQLiteに現在のコンテキスト情報を保存する"""
    # infrastructure IS the container in this context
    config_loader = SystemConfigLoader(infrastructure)

    # 実行コンテキストを更新
    config_loader.update_current_context(
        command=context_info["command"],
        language=context_info["language"],
        env_type=context_info["env_type"],
        contest_name=context_info["contest_name"],
        problem_name=context_info["problem_name"]
    )



def _parse_command_line_args(args, context, root, infrastructure):
    """コマンドライン引数を解析する（柔軟な順序対応）"""
    # 柔軟なスキャン方式で各タイプを検出・削除
    args, context = _scan_and_apply_language(args, context, root, infrastructure)
    args, context = _scan_and_apply_env_type(args, context, root, infrastructure)
    args, context = _scan_and_apply_command(args, context, root, infrastructure)
    args, context = _apply_problem_name(args, context, infrastructure)
    args, context = _apply_contest_name(args, context, infrastructure)

    return args, context


def _scan_and_apply_language(args, context, root, infrastructure):
    """言語を全引数からスキャンして適用 - 引数で指定された場合のみ更新、なければ既存設定を保持"""
    # 実際の言語のみをターゲット（動的に取得）
    from pathlib import Path

    from src.configuration.config_manager import FileLoader

    file_loader = FileLoader(infrastructure)
    valid_languages = set(file_loader.get_available_languages(Path("contest_env")))

    for idx, arg in enumerate(args):
        # 第1レベルのノード（言語）のみをチェック
        for lang_node in root.next_nodes:
            # 実際の言語ノードのみ処理
            if lang_node.key in valid_languages and arg in lang_node.matches:
                # 新しいコンテキストを作成
                new_context = _create_execution_config(
                    command_type=context.command_type,
                    language=lang_node.key,
                    contest_name=context.contest_name,
                    problem_name=context.problem_name,
                    env_type=context.env_type,
                    infrastructure=infrastructure
                )
                new_args = args[:idx] + args[idx+1:]
                return new_args, new_context

    # 引数に言語指定がない場合は既存設定を保持
    return args, context


def _apply_language(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_language(args, context, root)


def _scan_and_apply_env_type(args, context, root, infrastructure):
    """環境タイプを全引数からスキャンして適用 - 引数で指定された場合のみ更新、なければ既存設定を保持"""
    if context.language:
        env_type_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
        for idx, arg in enumerate(args):
            for env_type_node in env_type_nodes:
                for node in env_type_node.next_nodes:
                    if arg in node.matches:
                        # 新しいコンテキストを作成
                        new_context = _create_execution_config(
                            command_type=context.command_type,
                            language=context.language,
                            contest_name=context.contest_name,
                            problem_name=context.problem_name,
                            env_type=node.key,
                            infrastructure=infrastructure
                                )
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, new_context

    # 引数にenv_type指定がない場合は既存設定を保持
    return args, context


def _apply_env_type(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_env_type(args, context, root)


def _scan_and_apply_command(args, context, root, infrastructure):
    """コマンドを全引数からスキャンして適用"""
    if context.language:
        command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
        for idx, arg in enumerate(args):
            for command_node in command_nodes:
                for node in command_node.next_nodes:
                    if arg in node.matches:
                        # 新しいコンテキストを作成
                        new_context = _create_execution_config(
                            command_type=node.key,
                            language=context.language,
                            contest_name=context.contest_name,
                            problem_name=context.problem_name,
                            env_type=context.env_type,
                            infrastructure=infrastructure
                                )
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, new_context

    return args, context


def _apply_command(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_command(args, context, root)


def _apply_problem_name(args, context, infrastructure):
    """問題名の適用"""
    if args:
        problem_name = args.pop()
        # 新しいコンテキストを作成
        new_context = _create_execution_config(
            command_type=context.command_type,
            language=context.language,
            contest_name=context.contest_name,
            problem_name=problem_name,
            env_type=context.env_type,
            infrastructure=infrastructure
        )
        return args, new_context

    return args, context


def _apply_contest_name(args, context, infrastructure):
    """コンテスト名の適用"""
    if args:
        contest_name = args.pop()
        # 新しいコンテキストを作成
        new_context = _create_execution_config(
            command_type=context.command_type,
            language=context.language,
            contest_name=contest_name,
            problem_name=context.problem_name,
            env_type=context.env_type,
            infrastructure=infrastructure
        )
        return args, new_context

    return args, context


def _load_shared_config(base_dir: str, infrastructure):
    """共有設定を読み込む（依存性注入版）"""
    file_driver = infrastructure.resolve("file_driver")
    os_provider = infrastructure.resolve(DIKey.OS_PROVIDER)
    json_provider = infrastructure.resolve(DIKey.JSON_PROVIDER)

    shared_path = os_provider.path_join(base_dir, "shared", "env.json")

    try:
        req = FileRequest(FileOpType.READ, shared_path)
        result = req.execute_operation(driver=file_driver)
        return json_provider.loads(result.content)
    except Exception as e:
        raise ValueError(f"Failed to load shared JSON: {e}") from e









def make_dockerfile_loader(infrastructure):
    def loader(path: str) -> str:
        file_driver = infrastructure.resolve("file_driver")
        req = FileRequest(FileOpType.READ, path)
        result = req.execute_operation(driver=file_driver)
        return result.content
    return loader


def parse_user_input(
    args: list[str],
    infrastructure
):
    """ユーザー入力を解析してExecutionContextAdapterを生成する。

    Args:
        args: コマンドライン引数のリスト
        infrastructure: DIコンテナで、必要なサービスを解決する

    Returns:
        ExecutionContextAdapter: 解析結果と設定情報を含むコンテキスト

    Raises:
        ValueError: 引数が不正、またはバリデーションエラーの場合
    """
    # 1. Initialize services and load base data
    context_data = _initialize_and_load_base_data(infrastructure)

    # 2. Resolve environment configuration
    env_config = _resolve_environment_configuration(context_data, infrastructure)

    # 3. Create and configure initial context
    context = _create_initial_context(context_data, env_config, infrastructure)

    # 4. Parse command line arguments
    args, context = _parse_command_line_args(args, context, env_config['root'], infrastructure)

    # 5. Handle contest management (removed - backup should be handled by runstep)

    # 6. Finalize environment configuration
    context = _finalize_environment_configuration(context, env_config, infrastructure)

    # 7. Setup persistence and docker
    _setup_context_persistence_and_docker(context, args, infrastructure)

    # 8. Validate and return
    return _validate_and_return_context(context)


def _initialize_and_load_base_data(infrastructure):
    """Initialize services and load base context data."""
    ValidationService()
    current_context_info = _load_current_context_sqlite(infrastructure)
    return current_context_info


def _resolve_environment_configuration(context_data, infrastructure):
    """Load and resolve environment configuration."""
    from pathlib import Path

    from src.configuration.config_manager import FileLoader

    file_loader = FileLoader()

    # 全言語の設定を統合して言語候補を作成
    all_languages = file_loader.get_available_languages(Path(CONTEST_ENV_DIR))
    combined_config = {}

    # 各言語の設定を統合
    for lang in all_languages:
        lang_config = file_loader.load_and_merge_configs(
            system_dir="./config/system",
            env_dir=CONTEST_ENV_DIR,
            language=lang
        )
        combined_config.update(lang_config)

    root = create_config_root_from_dict(combined_config)
    return {
        'file_loader': file_loader,
        'env_config': combined_config,
        'root': root,
    }


def _create_initial_context(context_data, env_config, infrastructure):
    """Create and configure initial execution context."""
    context = _create_execution_config(
        command_type=context_data["command"],
        language=context_data["language"],
        contest_name=context_data["contest_name"],
        problem_name=context_data["problem_name"],
        env_type=context_data["env_type"],
        infrastructure=infrastructure
    )
    context.resolver = env_config['root']
    return context


def _handle_contest_management(context, infrastructure):
    """Handle contest backup and initialization."""
    if context.language and context.contest_name and context.problem_name:
        try:
            contest_manager = infrastructure.resolve("contest_manager")
            contest_manager.handle_contest_change(
                context.language,
                context.contest_name,
                context.problem_name
            )
            contest_manager.initialize_contest_current(
                context.language,
                context.contest_name,
                context.problem_name
            )
        except Exception as e:
            logger = infrastructure.resolve("unified_logger")
            logger.warning(f"Contest management failed: {e}")
    return context


def _finalize_environment_configuration(context, env_config, infrastructure):
    """Apply environment JSON and finalize configuration."""
    return context


def _apply_remaining_arguments_flexibly(args, context):
    """残った引数を柔軟に問題名・コンテスト名として適用"""
    # 最大2つまでの引数を問題名・コンテスト名として処理
    remaining_args = args[:2]  # 2つまでに制限

    # 最後の引数を問題名として設定（既存値がない場合のみ）
    if len(remaining_args) >= 1 and not context.problem_name:
        context.problem_name = remaining_args[-1]

    # 最初の引数をコンテスト名として設定（既存値がない場合のみ）
    if len(remaining_args) >= 2 and not context.contest_name:
        context.contest_name = remaining_args[0]

    return context


def _setup_context_persistence_and_docker(context, args, infrastructure):
    """Setup context persistence and Docker configuration."""
    # 引数が残っている場合は、より寛容に処理
    if args:
        # 未処理の引数を問題名・コンテスト名として最後の試行
        context = _apply_remaining_arguments_flexibly(args, context)
        args = []  # 処理済みとしてクリア

    _save_current_context_sqlite(infrastructure, {
        "command": context.command_type,
        "language": context.language,
        "env_type": context.env_type,
        "contest_name": context.contest_name,
        "problem_name": context.problem_name,
    })

    # oj.Dockerfileのパスを依存性注入で取得
    os_provider = infrastructure.resolve(DIKey.OS_PROVIDER)
    current_file_dir = os_provider.path_dirname(__file__)
    oj_dockerfile_path = os_provider.path_join(current_file_dir, "oj.Dockerfile")
    dockerfile_loader = make_dockerfile_loader(infrastructure)
    resolver = DockerfileResolver(
        dockerfile_path=None,
        oj_dockerfile_path=oj_dockerfile_path,
        dockerfile_loader=dockerfile_loader
    )
    context.dockerfile_resolver = resolver


def _validate_and_return_context(context):
    """Validate execution data and return context."""
    is_valid, error_message = context.validate_execution_data()
    if not is_valid:
        raise ValueError(error_message)
    return context
