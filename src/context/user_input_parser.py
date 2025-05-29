import os
import json
import copy
from typing import List, Dict, Optional, Tuple, Callable
from .execution_context import ExecutionContext
from src.context.resolver.config_resolver import create_config_root_from_dict, resolve_by_match_desc

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

def _load_all_env_jsons(base_dir: str, operations) -> list:
    env_jsons = []
    file_driver = operations.resolve("file_driver")
    from src.operations.file.file_request import FileRequest, FileOpType

    files = file_driver.list_files(base_dir)
    print(f"[DEBUG] _load_all_env_jsons: list_files({base_dir}) -> {files}")
    for path in files:
        print(f"[DEBUG] _load_all_env_jsons: path={path} type={type(path)}")
        if str(path).endswith("env.json"):
            req = FileRequest(FileOpType.READ, path)
            print(f"[DEBUG] _load_all_env_jsons: FileRequest path={req.path} type={type(req.path)}")
            result = req.execute(driver=file_driver)
            if not result.content:
                continue
            import json as _json
            try:
                env_json = _json.loads(result.content)
                print(f"[DEBUG] _load_all_env_jsons: loaded env_json={env_json}")
                env_jsons.append(env_json)
            except Exception as e:
                print(f"[DEBUG] _load_all_env_jsons: JSON decode error: {e} content={result.content}")
    print(f"[DEBUG] _load_all_env_jsons: env_jsons={env_jsons}")
    return env_jsons

def _apply_language(args, context, root):
    print(f"[DEBUG] _apply_language: in args={args} context.language={context.language}")
    language_nodes = resolve_by_match_desc(root, ["*"])
    print(f"[DEBUG] _apply_language: language_nodes={[repr(n) for n in language_nodes]}")
    for idx, arg in enumerate(args):
        for node in language_nodes:
            if arg in node.matches:
                context.language = node.key
                new_args = args[:idx] + args[idx+1:]
                print(f"[DEBUG] _apply_language: out args={new_args} context.language={context.language}")
                return new_args, context
    print(f"[DEBUG] _apply_language: out args={args} context.language={context.language}")
    return args, context

def _apply_env_type(args, context, root):
    print(f"[DEBUG] _apply_env_type: in args={args} context.env_type={context.env_type}")
    type_env_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
    for idx, arg in enumerate(args):
        for type_env_node in type_env_nodes:
            for node in type_env_node.next_nodes:
                if arg in node.matches:
                    context.env_type = node.key
                    new_args = args[:idx] + args[idx+1:]
                    print(f"[DEBUG] _apply_env_type: out args={new_args} context.env_type={context.env_type}")
                    return new_args, context
    print(f"[DEBUG] _apply_env_type: out args={args} context.env_type={context.env_type}")
    return args, context

def _apply_command(args, context, root):
    print(f"[DEBUG] _apply_command: in args={args} context.command_type={context.command_type}")
    command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
    for idx, arg in enumerate(args):
        for command_node in command_nodes:
            for node in command_node.next_nodes:
                if arg in node.matches:
                    context.command_type = node.key
                    new_args = args[:idx] + args[idx+1:]
                    print(f"[DEBUG] _apply_command: out args={new_args} context.command_type={context.command_type}")
                    return new_args, context
    print(f"[DEBUG] _apply_command: out args={args} context.command_type={context.command_type}")
    return args, context

def _apply_problem_name(args, context):
    print(f"[DEBUG] _apply_problem_name: in args={args} context.problem_name={context.problem_name}")
    if args:
        context.problem_name = args.pop()
    print(f"[DEBUG] _apply_problem_name: out args={args} context.problem_name={context.problem_name}")
    return args, context

def _apply_contest_name(args, context):
    print(f"[DEBUG] _apply_contest_name: in args={args} context.contest_name={context.contest_name}")
    if args:
        context.contest_name = args.pop()
    print(f"[DEBUG] _apply_contest_name: out args={args} context.contest_name={context.contest_name}")
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
    root = create_config_root_from_dict(merged_env_json)
    context.resolver = root
    # 言語特定
    args, context = _apply_language(args, context, root)
    # env_jsonをcontextにセット（既にセット済みならスキップ）
    context = _apply_env_json(context, env_jsons)
    # env_type特定
    args, context = _apply_env_type(args, context, root)
    # コマンド特定
    args, context = _apply_command(args, context, root)
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