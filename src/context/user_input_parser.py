import os
import copy
from typing import List
from .execution_context import ExecutionContext
from .parsers.system_info_manager import SystemInfoManager
from .parsers.validation_service import ValidationService
from .parsers.input_parser import InputParser
from src.context.resolver.config_resolver import create_config_root_from_dict

CONTEST_ENV_DIR = "contest_env"


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
    
    pattern = os.path.join(base_dir, "*", "env.json")
    env_json_paths = glob.glob(pattern)
    
    for path in env_json_paths:
        try:
            req = FileRequest(FileOpType.READ, path)
            result = req.execute(driver=file_driver)
            data = json.loads(result.content)
            ValidationService.validate_env_json(data, path)
            env_jsons.append(data)
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")
    
    return env_jsons


def _apply_env_json(context, env_jsons):
    """環境JSONをコンテキストに適用"""
    if context.env_json:
        return context
    if context.language:
        for env_json in env_jsons:
            if context.language in env_json:
                context.env_json = env_json
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
    system_info_manager = SystemInfoManager(operations)
    validation_service = ValidationService()
    
    # システム情報読み込み
    system_info = system_info_manager.load_system_info()
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
    
    # コマンドライン引数解析
    args, context = InputParser.parse_command_line(args, context, root)
    
    # 環境JSON適用
    context = _apply_env_json(context, env_jsons)
    
    # 残り引数チェック
    if args:
        raise ValueError(f"引数が多すぎます: {args}")
    
    
    # システム情報保存
    system_info_manager.save_system_info({
        "command": context.command_type,
        "language": context.language,
        "env_type": context.env_type,
        "contest_name": context.contest_name,
        "problem_name": context.problem_name,
        "env_json": context.env_json
    })
    
    # バリデーション
    is_valid, error_message = context.validate()
    if not is_valid:
        raise ValueError(error_message)
    
    return context




if __name__ == "__main__":
    from src.env.build_operations import build_operations
    operations = build_operations()
    print(parse_user_input(["py", "local", "t", "abc300", "a"], operations))