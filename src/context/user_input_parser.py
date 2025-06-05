import os
import copy
from typing import List
from .execution_context import ExecutionContext
from .parsers.validation_service import ValidationService
# Note: SystemInfoManager and InputParser removed - using direct implementation
from src.context.resolver.config_resolver import create_config_root_from_dict

CONTEST_ENV_DIR = "contest_env"


def _load_system_info_direct(operations, path="system_info.json"):
    """システム情報を直接読み込む"""
    import json
    from src.operations.file.file_request import FileRequest
    from src.operations.file.file_op_type import FileOpType
    
    file_driver = operations.resolve("file_driver")
    
    req = FileRequest(FileOpType.EXISTS, path)
    result = req.execute(driver=file_driver)
    
    if not result.exists:
        return {
            "command": None,
            "language": None,
            "env_type": None,
            "contest_name": None,
            "problem_name": None,
            "env_json": None,
        }
    
    req = FileRequest(FileOpType.READ, path)
    result = req.execute(driver=file_driver)
    return json.loads(result.content)


def _save_system_info_direct(operations, info, path="system_info.json"):
    """システム情報を直接保存する"""
    import json
    from src.operations.file.file_request import FileRequest
    from src.operations.file.file_op_type import FileOpType
    
    file_driver = operations.resolve("file_driver")
    
    req = FileRequest(
        FileOpType.WRITE, 
        path, 
        content=json.dumps(info, ensure_ascii=False, indent=2)
    )
    req.execute(driver=file_driver)


def _parse_command_line_direct(args, context, root):
    """コマンドライン引数を直接解析する"""
    from src.context.resolver.config_resolver import resolve_by_match_desc
    
    # 順次処理を適用
    args, context = _apply_language_direct(args, context, root)
    args, context = _apply_env_type_direct(args, context, root)
    args, context = _apply_command_direct(args, context, root)
    args, context = _apply_problem_name_direct(args, context)
    args, context = _apply_contest_name_direct(args, context)
    
    return args, context


def _apply_language_direct(args, context, root):
    """言語の適用"""
    for idx, arg in enumerate(args):
        # 第1レベルのノード（言語）のみをチェック
        for lang_node in root.next_nodes:
            if arg in lang_node.matches:
                context.language = lang_node.key
                new_args = args[:idx] + args[idx+1:]
                return new_args, context
    
    return args, context


def _apply_env_type_direct(args, context, root):
    """環境タイプの適用"""
    from src.context.resolver.config_resolver import resolve_by_match_desc
    
    if context.language:
        env_type_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
        for idx, arg in enumerate(args):
            for env_type_node in env_type_nodes:
                for node in env_type_node.next_nodes:
                    if arg in node.matches:
                        context.env_type = node.key
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, context
    
    return args, context


def _apply_command_direct(args, context, root):
    """コマンドの適用"""
    from src.context.resolver.config_resolver import resolve_by_match_desc
    
    if context.language:
        command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
        for idx, arg in enumerate(args):
            for command_node in command_nodes:
                for node in command_node.next_nodes:
                    if arg in node.matches:
                        context.command_type = node.key
                        new_args = args[:idx] + args[idx+1:]
                        return new_args, context
    
    return args, context


def _apply_problem_name_direct(args, context):
    """問題名の適用"""
    if args:
        context.problem_name = args.pop()
    
    return args, context


def _apply_contest_name_direct(args, context):
    """コンテスト名の適用"""
    if args:
        context.contest_name = args.pop()
    
    return args, context


def _load_shared_config(base_dir: str, operations):
    """共有設定を読み込む"""
    import json
    from src.operations.file.file_request import FileRequest
    from src.operations.file.file_op_type import FileOpType
    
    file_driver = operations.resolve("file_driver")
    shared_path = os.path.join(base_dir, "shared", "env.json")
    
    try:
        req = FileRequest(FileOpType.READ, shared_path)
        result = req.execute(driver=file_driver)
        return json.loads(result.content)
    except Exception:
        return None


def _load_all_env_jsons(base_dir: str, operations) -> list:
    """環境設定JSONファイルを全て読み込む"""
    env_jsons = []
    file_driver = operations.resolve("file_driver")
    from src.operations.file.file_request import FileRequest
    from src.operations.file.file_op_type import FileOpType
    
    req = FileRequest(FileOpType.EXISTS, base_dir)
    result = req.execute(driver=file_driver)
    if not result.exists:
        return env_jsons
    
    import glob
    import json
    
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
            result = req.execute(driver=file_driver)
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
    
    # 各言語設定に共有設定をマージ
    for lang, lang_config in merged_json.items():
        if not isinstance(lang_config, dict):
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
        elif "local" in shared_data and "env_types" in lang_config:
            if "local" not in lang_config["env_types"]:
                lang_config["env_types"]["local"] = shared_data["local"]
    
    return merged_json


def _apply_env_json(context, env_jsons, base_dir=None, operations=None):
    """環境JSONをコンテキストに適用"""
    # Always reprocess to ensure latest shared config is applied
    # if context.env_json:
    #     return context
    if context.language:
        # shared設定を読み込み
        shared_config = None
        if base_dir and operations:
            shared_config = _load_shared_config(base_dir, operations)
            
        for env_json in env_jsons:
            if context.language in env_json:
                # shared設定とマージ
                merged_env_json = _merge_with_shared_config(env_json, shared_config)
                context.env_json = merged_env_json
                break
    return context




def make_dockerfile_loader(operations):
    def loader(path: str) -> str:
        file_driver = operations.resolve("file_driver")
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        req = FileRequest(FileOpType.READ, path)
        result = req.execute(driver=file_driver)
        return result.content
    return loader


def parse_user_input(
    args: List[str],
    operations
) -> ExecutionContext:
    """
    引数リストからExecutionContextを生成するトップレベル関数。
    """

    # システム情報管理とバリデーション初期化
    validation_service = ValidationService()
    
    # システム情報読み込み (direct implementation)
    system_info = _load_system_info_direct(operations)
    context = ExecutionContext(
        command_type=system_info["command"],
        language=system_info["language"],
        contest_name=system_info["contest_name"],
        problem_name=system_info["problem_name"],
        env_type=system_info["env_type"],
        env_json=system_info["env_json"],
    )
    
    # バックアップコンテキスト作成
    context.old_execution_context = copy.deepcopy(context)
    
    # 環境設定読み込みと設定ルート作成
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, operations)
    merged_env_json = {}
    for env_json in env_jsons:
        merged_env_json.update(env_json)
    root = create_config_root_from_dict(merged_env_json)
    context.resolver = root
    
    # コマンドライン引数解析 (direct implementation)
    args, context = _parse_command_line_direct(args, context, root)
    
    # 環境JSON適用（shared設定とマージ）
    context = _apply_env_json(context, env_jsons, CONTEST_ENV_DIR, operations)
    
    # 残り引数チェック
    if args:
        raise ValueError(f"引数が多すぎます: {args}")
    
    
    # システム情報保存 (direct implementation)
    _save_system_info_direct(operations, {
        "command": context.command_type,
        "language": context.language,
        "env_type": context.env_type,
        "contest_name": context.contest_name,
        "problem_name": context.problem_name,
        "env_json": context.env_json
    })
    
    # Dockerfile resolver setup
    from src.context.dockerfile_resolver import DockerfileResolver
    
    # Default OJ Dockerfile path
    oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
    
    # Create Dockerfile resolver with loader
    dockerfile_loader = make_dockerfile_loader(operations)
    resolver = DockerfileResolver(
        dockerfile_path=None,  # No language-specific Dockerfile for now
        oj_dockerfile_path=oj_dockerfile_path,
        dockerfile_loader=dockerfile_loader
    )
    
    context.dockerfile_resolver = resolver
    
    # バリデーション
    is_valid, error_message = context.validate()
    if not is_valid:
        raise ValueError(error_message)
    
    return context




if __name__ == "__main__":
    from src.operations.build_operations import build_operations
    operations = build_operations()
    print(parse_user_input(["py", "local", "t", "abc300", "a"], operations))