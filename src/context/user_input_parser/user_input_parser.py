import glob
import json
import os

from src.context.dockerfile_resolver import DockerfileResolver

# from .execution_context import ExecutionContext  # 新システムで置き換え済み
from src.context.parsers.validation_service import ValidationService
from src.context.resolver.config_resolver import create_config_root_from_dict, resolve_by_match_desc

# 新設定システムの統合
from src.context.user_input_parser.user_input_parser_integration import (
    create_new_execution_context,
)
from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest

CONTEST_ENV_DIR = "contest_env"


def _load_current_context_sqlite(operations):
    """SQLiteから現在のコンテキスト情報を読み込む"""
    # operations IS the container in this context
    config_loader = SystemConfigLoader(operations)

    context = config_loader.get_current_context()
    config = config_loader.load_config()

    return {
        "command": context.get("command"),
        "language": context.get("language"),
        "env_type": context.get("env_type"),
        "contest_name": context.get("contest_name"),
        "problem_name": context.get("problem_name"),
        "env_json": config.get("env_json"),
    }


def _save_current_context_sqlite(operations, context_info):
    """SQLiteに現在のコンテキスト情報を保存する"""
    # operations IS the container in this context
    config_loader = SystemConfigLoader(operations)

    # 実行コンテキストを更新
    config_loader.update_current_context(
        command=context_info.get("command"),
        language=context_info.get("language"),
        env_type=context_info.get("env_type"),
        contest_name=context_info.get("contest_name"),
        problem_name=context_info.get("problem_name")
    )

    # env_jsonがある場合は保存
    if context_info.get("env_json"):
        config_loader.save_config("env_json", context_info["env_json"], "environment")


def _parse_command_line_args(args, context, root):
    """コマンドライン引数を解析する（柔軟な順序対応）"""
    # 柔軟なスキャン方式で各タイプを検出・削除
    args, context = _scan_and_apply_language(args, context, root)
    args, context = _scan_and_apply_env_type(args, context, root)
    args, context = _scan_and_apply_command(args, context, root)
    args, context = _apply_problem_name(args, context)
    args, context = _apply_contest_name(args, context)

    return args, context


def _scan_and_apply_language(args, context, root):
    """言語を全引数からスキャンして適用 - 引数で指定された場合のみ更新、なければ既存設定を保持"""
    # 実際の言語のみをターゲット（動的に取得）
    from pathlib import Path

    from src.configuration.loaders.configuration_loader import ConfigurationLoader

    config_loader = ConfigurationLoader(
        contest_env_dir=Path("contest_env"),
        system_config_dir=Path("./config/system")
    )
    valid_languages = set(config_loader.get_available_languages())

    for idx, arg in enumerate(args):
        # 第1レベルのノード（言語）のみをチェック
        for lang_node in root.next_nodes:
            # 実際の言語ノードのみ処理
            if lang_node.key in valid_languages and arg in lang_node.matches:
                # 新しいコンテキストを作成
                new_context = create_new_execution_context(
                    command_type=context.command_type,
                    language=lang_node.key,
                    contest_name=context.contest_name,
                    problem_name=context.problem_name,
                    env_type=context.env_type,
                    env_json=context.env_json
                )
                new_args = args[:idx] + args[idx+1:]
                return new_args, new_context

    # 引数に言語指定がない場合は既存設定を保持
    return args, context


def _apply_language(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_language(args, context, root)


def _scan_and_apply_env_type(args, context, root):
    """環境タイプを全引数からスキャンして適用 - 引数で指定された場合のみ更新、なければ既存設定を保持"""
    if context.language:
        env_type_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
        for idx, arg in enumerate(args):
            for env_type_node in env_type_nodes:
                for node in env_type_node.next_nodes:
                    if arg in node.matches:
                        # 新しいコンテキストを作成
                        new_context = create_new_execution_context(
                            command_type=context.command_type,
                            language=context.language,
                            contest_name=context.contest_name,
                            problem_name=context.problem_name,
                            env_type=node.key,
                            env_json=context.env_json
                        )
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, new_context

    # 引数にenv_type指定がない場合は既存設定を保持
    return args, context


def _apply_env_type(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_env_type(args, context, root)


def _scan_and_apply_command(args, context, root):
    """コマンドを全引数からスキャンして適用"""
    if context.language:
        command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
        for idx, arg in enumerate(args):
            for command_node in command_nodes:
                for node in command_node.next_nodes:
                    if arg in node.matches:
                        # 新しいコンテキストを作成
                        new_context = create_new_execution_context(
                            command_type=node.key,
                            language=context.language,
                            contest_name=context.contest_name,
                            problem_name=context.problem_name,
                            env_type=context.env_type,
                            env_json=context.env_json
                        )
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, new_context

    return args, context


def _apply_command(args, context, root):
    """後方互換性のための既存関数（非推奨）"""
    return _scan_and_apply_command(args, context, root)


def _apply_problem_name(args, context):
    """問題名の適用"""
    if args:
        problem_name = args.pop()
        # 新しいコンテキストを作成
        new_context = create_new_execution_context(
            command_type=context.command_type,
            language=context.language,
            contest_name=context.contest_name,
            problem_name=problem_name,
            env_type=context.env_type,
            env_json=context.env_json
        )
        return args, new_context

    return args, context


def _apply_contest_name(args, context):
    """コンテスト名の適用"""
    if args:
        contest_name = args.pop()
        # 新しいコンテキストを作成
        new_context = create_new_execution_context(
            command_type=context.command_type,
            language=context.language,
            contest_name=contest_name,
            problem_name=context.problem_name,
            env_type=context.env_type,
            env_json=context.env_json
        )
        return args, new_context

    return args, context


def _load_shared_config(base_dir: str, operations):
    """共有設定を読み込む"""
    file_driver = operations.resolve("file_driver")
    shared_path = os.path.join(base_dir, "shared", "env.json")

    try:
        req = FileRequest(FileOpType.READ, shared_path)
        result = req.execute_operation(driver=file_driver)
        return json.loads(result.content)
    except Exception:
        return None


def _load_all_env_jsons(base_dir: str, operations) -> list:
    """環境設定JSONファイルを全て読み込む"""
    env_jsons = []
    file_driver = operations.resolve("file_driver")

    req = FileRequest(FileOpType.EXISTS, base_dir)
    result = req.execute_operation(driver=file_driver)
    if not result.exists:
        return env_jsons

    # 共有設定を読み込み
    shared_config = _load_shared_config(base_dir, operations)

    pattern = os.path.join(base_dir, "*", "env.json")
    env_json_paths = glob.glob(pattern)

    for path in env_json_paths:
        try:
            # 特殊フォルダは除外（バリデーション対象外）
            dir_name = os.path.basename(os.path.dirname(path))
            excluded_dirs = {'shared', '__common__', 'common', 'base'}
            if dir_name in excluded_dirs:
                continue

            req = FileRequest(FileOpType.READ, path)
            result = req.execute_operation(driver=file_driver)
            data = json.loads(result.content)

            # 共有設定を考慮してバリデーション
            ValidationService.validate_env_json(data, path, shared_config)
            env_jsons.append(data)
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")

    return env_jsons


def _merge_with_shared_config(env_json, shared_config):
    """env.jsonとshared設定をマージ"""
    if not shared_config or "shared" not in shared_config:
        return env_json

    shared_data = shared_config["shared"]
    merged_json = env_json.copy()

    # shared設定を直接追加
    merged_json["shared"] = shared_data

    # 各言語設定に共有設定をマージ
    for lang, lang_config in merged_json.items():
        if not isinstance(lang_config, dict) or lang == "shared":
            continue

        # パス設定をマージ
        paths_key = "paths" if "paths" in shared_data else "basic_paths"
        if paths_key in shared_data:
            for path_key, path_value in shared_data[paths_key].items():
                if path_key not in lang_config:
                    lang_config[path_key] = path_value

        # env_typesにsharedのlocal設定をマージ
        if "local" in shared_data and "env_types" not in lang_config:
            lang_config["env_types"] = {"local": shared_data["local"]}
        elif "local" in shared_data and "env_types" in lang_config and "local" not in lang_config["env_types"]:
            lang_config["env_types"]["local"] = shared_data["local"]

        # output設定をマージ
        if "output" in shared_data:
            if "output" not in lang_config:
                lang_config["output"] = shared_data["output"].copy()
            else:
                # 既存のoutput設定と共有設定をマージ
                for output_key, output_value in shared_data["output"].items():
                    if output_key not in lang_config["output"]:
                        lang_config["output"][output_key] = output_value

        # commands設定をマージ（重要：ワークフローに必要）
        if "commands" in shared_data:
            if "commands" not in lang_config:
                lang_config["commands"] = shared_data["commands"].copy()
            else:
                # 既存のcommands設定と共有設定をマージ
                for cmd_key, cmd_value in shared_data["commands"].items():
                    if cmd_key not in lang_config["commands"]:
                        lang_config["commands"][cmd_key] = cmd_value

    return merged_json


def _apply_env_json(context, env_jsons, base_dir=None, operations=None):
    """環境JSONをコンテキストに適用"""
    # ConfigurationLoaderを使用して正しい設定を取得
    if context.language and base_dir:
        from pathlib import Path

        from src.configuration.loaders.configuration_loader import ConfigurationLoader
        config_loader = ConfigurationLoader(
            contest_env_dir=Path(base_dir),
            system_config_dir=Path("./config/system")
        )
        # 完全なマージ設定を取得（共有設定をトップレベルで利用）
        merged_config = config_loader.load_merged_config(context.language, {})

        # 言語固有設定に共有設定の重要項目を直接追加
        if context.language in merged_config:
            lang_config = merged_config[context.language]
            # commandsが共有設定にある場合は追加
            if 'commands' in merged_config and 'commands' not in lang_config:
                lang_config['commands'] = merged_config['commands']
            context.env_json = {context.language: lang_config}
        else:
            context.env_json = merged_config
    return context




def make_dockerfile_loader(operations):
    def loader(path: str) -> str:
        file_driver = operations.resolve("file_driver")
        req = FileRequest(FileOpType.READ, path)
        result = req.execute_operation(driver=file_driver)
        return result.content
    return loader


def parse_user_input(
    args: list[str],
    operations
):
    """ユーザー入力を解析してExecutionContextAdapterを生成する。

    Args:
        args: コマンドライン引数のリスト
        operations: DIコンテナで、必要なサービスを解決する

    Returns:
        ExecutionContextAdapter: 解析結果と設定情報を含むコンテキスト

    Raises:
        ValueError: 引数が不正、またはバリデーションエラーの場合
    """
    # 1. Initialize services and load base data
    context_data = _initialize_and_load_base_data(operations)

    # 2. Resolve environment configuration
    env_config = _resolve_environment_configuration(context_data, operations)

    # 3. Create and configure initial context
    context = _create_initial_context(context_data, env_config)

    # 4. Parse command line arguments
    args, context = _parse_command_line_args(args, context, env_config['root'])

    # 5. Handle contest management (removed - backup should be handled by runstep)

    # 6. Finalize environment configuration
    context = _finalize_environment_configuration(context, env_config, operations)

    # 7. Setup persistence and docker
    _setup_context_persistence_and_docker(context, args, operations)

    # 8. Validate and return
    return _validate_and_return_context(context)


def _initialize_and_load_base_data(operations):
    """Initialize services and load base context data."""
    ValidationService()
    current_context_info = _load_current_context_sqlite(operations)
    return current_context_info


def _resolve_environment_configuration(context_data, operations):
    """Load and resolve environment configuration."""
    from pathlib import Path

    from src.configuration.loaders.configuration_loader import ConfigurationLoader

    config_loader = ConfigurationLoader(
        contest_env_dir=Path(CONTEST_ENV_DIR),
        system_config_dir=Path("./config/system")
    )

    # 全言語の設定を統合して言語候補を作成
    all_languages = config_loader.get_available_languages()
    combined_config = {}

    # 各言語の設定を統合
    for lang in all_languages:
        lang_config = config_loader.load_merged_config(lang, {})
        combined_config.update(lang_config)

    root = create_config_root_from_dict(combined_config)
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, operations)

    # Resolve final env_json
    final_env_json = context_data["env_json"]
    if final_env_json is None and context_data["language"]:
        lang_merged_config = config_loader.load_merged_config(context_data["language"], {})
        if context_data["language"] in lang_merged_config:
            final_env_json = {context_data["language"]: lang_merged_config[context_data["language"]]}
        else:
            final_env_json = lang_merged_config

    return {
        'config_loader': config_loader,
        'env_config': combined_config,
        'root': root,
        'env_jsons': env_jsons,
        'final_env_json': final_env_json
    }


def _create_initial_context(context_data, env_config):
    """Create and configure initial execution context."""
    context = create_new_execution_context(
        command_type=context_data["command"],
        language=context_data["language"],
        contest_name=context_data["contest_name"],
        problem_name=context_data["problem_name"],
        env_type=context_data["env_type"],
        env_json=env_config['final_env_json']
    )
    context.resolver = env_config['root']
    return context


def _handle_contest_management(context, operations):
    """Handle contest backup and initialization."""
    if context.language and context.contest_name and context.problem_name:
        try:
            contest_manager = operations.resolve("contest_manager")
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
            print(f"Warning: Contest management failed: {e}")
    return context


def _finalize_environment_configuration(context, env_config, operations):
    """Apply environment JSON and finalize configuration."""
    context = _apply_env_json(context, env_config['env_jsons'], CONTEST_ENV_DIR, operations)
    if context.env_json:
        context.resolver = create_config_root_from_dict(context.env_json)
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


def _setup_context_persistence_and_docker(context, args, operations):
    """Setup context persistence and Docker configuration."""
    # 引数が残っている場合は、より寛容に処理
    if args:
        # 未処理の引数を問題名・コンテスト名として最後の試行
        context = _apply_remaining_arguments_flexibly(args, context)
        args = []  # 処理済みとしてクリア

    _save_current_context_sqlite(operations, {
        "command": context.command_type,
        "language": context.language,
        "env_type": context.env_type,
        "contest_name": context.contest_name,
        "problem_name": context.problem_name,
        "env_json": context.env_json
    })

    oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
    dockerfile_loader = make_dockerfile_loader(operations)
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
