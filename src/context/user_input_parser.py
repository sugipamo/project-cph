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
            "contest_current_path": None,
            "env_json": None,
            "dockerfile": None
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
        if "contest_current_path" in conf and not isinstance(conf["contest_current_path"], str):
            raise ValueError(f"{path}: {lang}のcontest_current_pathはstrである必要があります")

def _load_all_env_jsons(base_dir: str) -> List[dict]:
    env_jsons = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "env.json":
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    _validate_env_json(data, path)
                    env_jsons.append(data)
                except Exception as e:
                    raise RuntimeError(f"{path} の読み込みまたはバリデーションに失敗: {e}")
    return env_jsons

def _extract_language_and_aliases(env_jsons: List[dict]) -> Dict[str, List[str]]:
    result = {}
    for env_json in env_jsons:
        for lang, conf in env_json.items():
            aliases = conf.get("aliases", [])
            result[lang] = aliases
    return result

def _apply_language(args, context, env_json: dict):
    for idx, arg in enumerate(args):
        if arg in env_json:
            context.language = arg
            new_args = args[:idx] + args[idx+1:]
            return new_args, context
    return args, context

def _apply_env_type(args, context, resolver: ConfigResolver):
    for idx, arg in enumerate(args):
        if arg in env_json[language]["env_types"]:
            context.env_type = arg
            new_args = args[:idx] + args[idx+1:]
            return new_args, context
    return args, context

def _apply_command(args, context):
    if not context.env_json or not context.language:
        return args, context
    commands = context.env_json[context.language]["commands"] if "commands" in context.env_json[context.language] else {}
    for idx, arg in enumerate(args):
        for cmd_name, cmd_conf in commands.items():
            aliases = cmd_conf["aliases"] if "aliases" in cmd_conf else []
            if arg == cmd_name or arg in aliases:
                context.command_type = cmd_name
                new_args = args[:idx] + args[idx+1:]
                return new_args, context
    return args, context

def _apply_names(args, context):
    if len(args) > 2:
        raise ValueError(f"引数が多すぎます: {args}")
    keys = ["problem_name", "contest_name"]
    for key, arg in zip(keys, reversed(args)):
        setattr(context, key, arg)
    return [], context

def _apply_contest_current_path(context):
    if context.env_json and context.language:
        contest_current_path = context.env_json[context.language]["contest_current_path"] if "contest_current_path" in context.env_json[context.language] else None
        if contest_current_path:
            context.contest_current_path = contest_current_path
    if not context.contest_current_path:
        context.contest_current_path = "./contest_current"
    return context

def _apply_workspace_path(args, context):
    ws = None
    if "--workspace" in args:
        idx = args.index("--workspace")
        if idx + 1 < len(args):
            ws = args[idx + 1]
    if not ws and context.env_json and context.language:
        lang_conf = context.env_json[context.language] if context.language in context.env_json else {}
        ws = lang_conf["workspace_path"] if "workspace_path" in lang_conf else None
    if not ws:
        ws = os.getcwd()
    context.workspace_path = ws
    return context

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

def _apply_oj_dockerfile(context, dockerfile_loader):
    oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
    try:
        context.oj_dockerfile = dockerfile_loader(oj_dockerfile_path)
    except Exception:
        context.oj_dockerfile = None
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
    env_jsons = _load_all_env_jsons(CONTEST_ENV_DIR)
    # env_jsonsをマージして1つのdictにまとめる
    merged_env_json = {}
    for env_json in env_jsons:
        merged_env_json.update(env_json)
    resolver = ConfigResolver.from_dict(merged_env_json)
    context.resolver = resolver
    # 言語特定
    args, context = _apply_language(args, context, env_json)
    # env_type特定
    args, context = _apply_env_type(args, context, resolver)
    # コマンド特定
    args, context = _apply_command(args, context)
    # 残りの引数からproblem_name, contest_nameを特定
    args, context = _apply_names(args, context)
    # contest_current_path特定
    context = _apply_contest_current_path(context)
    # workspace_path特定
    context = _apply_workspace_path(args, context)
    # env_jsonをcontextにセット（既にセット済みならスキップ）
    context = _apply_env_json(context, env_jsons)
    # dockerfileの内容をセット
    context = _apply_dockerfile(context, dockerfile_loader)
    # oj.Dockerfileの内容をセット
    context = _apply_oj_dockerfile(context, dockerfile_loader)
    # system_info.jsonへ保存
    _save_system_info(operations, {
        "command": context.command_type,
        "language": context.language,
        "env_type": context.env_type,
        "contest_name": context.contest_name,
        "problem_name": context.problem_name,
        "contest_current_path": context.contest_current_path,
        "env_json": context.env_json
    })
    # バリデーション
    is_valid, error_message = context.validate()
    if not is_valid:
        raise ValueError(error_message)
    return context