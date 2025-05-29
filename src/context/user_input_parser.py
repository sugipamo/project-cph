import os
import json
import copy
from typing import List, Dict, Optional, Tuple, Callable
from .execution_context import ExecutionContext
from .config_resolver import ConfigResolver

CONTEST_ENV_DIR = "contest_env"
SYSTEM_INFO_PATH = "system_info.json"

def _load_system_info(operations, path=SYSTEM_INFO_PATH):
    file_driver = operations.resolve("file_driver")
    from src.operations.file.file_request import FileRequest, FileOpType
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

def _save_system_info(operations, info, path=SYSTEM_INFO_PATH):
    file_driver = operations.resolve("file_driver")
    from src.operations.file.file_request import FileRequest, FileOpType
    import json
    req = FileRequest(FileOpType.WRITE, path, content=json.dumps(info, ensure_ascii=False, indent=2))
    req.execute(driver=file_driver)

def _validate_env_json(data: dict, path: str):
    if not isinstance(data, dict):
        raise ValueError(f"{path}: env.jsonのトップレベルはdictである必要があります")
    for lang, conf in data.items():
        if not isinstance(conf, dict):
            raise ValueError(f"{path}: {lang}の値はdictである必要があります")
        if "commands" not in conf or not isinstance(conf["commands"], dict):
            raise ValueError(f"{path}: {lang}にcommands(dict)がありません")
        if "env_types" not in conf or not isinstance(conf["env_types"], dict):
            raise ValueError(f"{path}: {lang}にenv_types(dict)がありません")
        if "aliases" in conf and not isinstance(conf["aliases"], list):
            raise ValueError(f"{path}: {lang}のaliasesはlistである必要があります")

def _load_all_env_jsons(base_dir: str, operations) -> List[dict]:
    env_jsons = []
    file_driver = operations.resolve("file_driver")
    from src.operations.file.file_request import FileRequest, FileOpType

    for path in file_driver.list_files(base_dir):
        if str(path).endswith("env.json"):
            req = FileRequest(FileOpType.READ, path)
            result = req.execute(driver=file_driver)
            if not result.content:
                continue
            data = json.loads(result.content)
            _validate_env_json(data, path)
            env_jsons.append(data)
    return env_jsons

def _apply_language(args, context, resolver):
    # resolverが渡されていればそれを使って言語候補を取得
    language_nodes = resolver.resolve_by_match_desc(["*"])
    for idx, arg in enumerate(args):
        for node in language_nodes:
            if arg in node.matches:
                context.language = node.key
                new_args = args[:idx] + args[idx+1:]
                return new_args, context
    return args, context

def _apply_env_type(args, context, resolver: ConfigResolver):
    type_env_nodes = resolver.resolve_by_match_desc([context.language, "env_types"])
    for idx, arg in enumerate(args):
        for type_env_node in type_env_nodes:
            for node in type_env_node.next_nodes:
                if arg in node.matches:
                    context.env_type = node.key
                    new_args = args[:idx] + args[idx+1:]
                    return new_args, context
    return args, context

def _apply_command(args, context, resolver: ConfigResolver):
    command_nodes = resolver.resolve_by_match_desc([context.language, "commands"])
    for idx, arg in enumerate(args):
        for command_node in command_nodes:
            for node in command_node.next_nodes:
                if arg in node.matches:
                    context.command_type = node.key
                    new_args = args[:idx] + args[idx+1:]
                    return new_args, context
    return args, context

def _apply_problem_name(args, context):
    if args:
        context.problem_name = args.pop()
    return args, context

def _apply_contest_name(args, context):
    if args:
        context.contest_name = args.pop()
    return args, context

def _apply_env_json(context, env_jsons):
    if context.env_json:
        return context
    if context.language:
        for env_json in env_jsons:
            if context.language in env_json:
                context.env_json = env_json
                break
    return context

def _apply_dockerfile(context, dockerfile_loader):
    dockerfile_path = None
    if context.env_json and context.language and context.env_type:
        env_types = context.env_json[context.language].get("env_types", {})
        env_type_conf = env_types.get(context.env_type, {})
        dockerfile_path = env_type_conf.get("dockerfile_path")
    if dockerfile_path:
        try:
            print("[debug] dockerfile_path", dockerfile_path)
            context.dockerfile = dockerfile_loader(dockerfile_path)
        except Exception:
            context.dockerfile = None
    return context

def _apply_oj_dockerfile(context):
    oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
    with open(oj_dockerfile_path, "r") as f:
        context.oj_dockerfile = f.read()
    return context

def make_dockerfile_loader(operations):
    def loader(path: str) -> str:
        file_driver = operations.resolve("file_driver")
        from src.operations.file.file_request import FileRequest, FileOpType
        req = FileRequest(FileOpType.READ, path)
        result = req.execute(driver=file_driver)
        return result.content
    return loader

def parse_user_input(
    args: List[str],
    operations,
    dockerfile_loader: Callable[[str], str] = None
) -> ExecutionContext:
    """
    引数リストからExecutionContextを生成するトップレベル関数。
    テスト用に依存注入も可能。
    """
    if dockerfile_loader is None:
        dockerfile_loader = make_dockerfile_loader(operations)

    system_info = _load_system_info(operations)
    context = ExecutionContext(
        command_type=system_info["command"],
        language=system_info["language"],
        contest_name=system_info["contest_name"],
        problem_name=system_info["problem_name"],
        env_type=system_info["env_type"],
        env_json=system_info["env_json"],
    )
    # old_execution_context
    context.old_execution_context = copy.deepcopy(context)
    # env.json読み込み
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR, operations)
    # env_jsonsをマージして1つのdictにまとめる
    merged_env_json = {}
    for env_json in env_jsons:
        merged_env_json.update(env_json)
    resolver = ConfigResolver.from_dict(merged_env_json)
    context.resolver = resolver
    # 言語特定
    args, context = _apply_language(args, context, resolver)
    # env_jsonをcontextにセット（既にセット済みならスキップ）
    context = _apply_env_json(context, env_jsons)
    # env_type特定
    args, context = _apply_env_type(args, context, resolver)
    # コマンド特定
    args, context = _apply_command(args, context, resolver)
    # 残りの引数からproblem_name, contest_nameを特定
    args, context = _apply_problem_name(args, context)
    args, context = _apply_contest_name(args, context)
    if args:
        raise ValueError(f"引数が多すぎます: {args}")
    # dockerfileの内容をセット
    context = _apply_dockerfile(context, dockerfile_loader)
    # oj.Dockerfileの内容をセット
    context = _apply_oj_dockerfile(context)
    # system_info.jsonへ保存
    _save_system_info(operations, {
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