import os
import json
from typing import List, Dict, Optional, Tuple, Callable
from .execution_context import ExecutionContext

CONTEST_ENV_DIR = "contest_env"
SYSTEM_INFO_PATH = "system_info.json"

class SystemInfoProvider:
    """
    system_info.jsonの読み書きを抽象化するプロバイダ。
    テストや他用途で差し替え可能。
    """
    def load(self) -> dict:
        raise NotImplementedError
    def save(self, info: dict):
        raise NotImplementedError

class LocalSystemInfoProvider(SystemInfoProvider):
    def __init__(self, path: str = SYSTEM_INFO_PATH):
        self.path = path
    def load(self) -> dict:
        if not os.path.exists(self.path):
            # ファイルがなければ全てNoneで返す
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
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
    def save(self, info: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

class UserInputParser:
    """
    CLI等から渡される引数リストをパースし、必須情報を抽出するクラス。
    """
    def __init__(self, system_info_provider, dockerfile_loader):
        self.system_info_provider = system_info_provider
        self.dockerfile_loader = dockerfile_loader

    @staticmethod
    def _default_dockerfile_loader(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    @classmethod
    def from_args(cls, args: List[str]) -> ExecutionContext:
        system_info_provider = LocalSystemInfoProvider()
        dockerfile_loader = cls._default_dockerfile_loader
        return cls(system_info_provider, dockerfile_loader).parse_and_validate(args)

    def parse_and_validate(self, args: List[str]) -> ExecutionContext:
        # 引数をパース
        context = self.parse(args)
        if not context:
            raise ValueError("引数のパースに失敗しました")

        # パース結果をバリデーション
        is_valid, error_message = context.validate()
        if not is_valid:
            raise ValueError(error_message)

        return context
        
    def parse(self, args: list) -> ExecutionContext:
        # 1. contextをNoneで初期化
        context = ExecutionContext(
            command_type=None,
            language=None,
            contest_name=None,
            problem_name=None,
            env_type=None,
            env_json=None,
            contest_current_path=None,
            workspace_path=None,
            dockerfile=None,
            oj_dockerfile=None,
            old_execution_context=None,
        )
        # 2. system_info.jsonの内容をcontextへ反映
        context = self._apply_system_info(context)
        # 2.5. contextのコピーをold_execution_contextにセット
        context = self._apply_old_execution_context(context)
        # 3. contest_env配下のenv.jsonを全て読み込み
        env_jsons = self._load_all_env_jsons(CONTEST_ENV_DIR)
        # 4. 言語特定
        args, context = self._apply_language(args, context, env_jsons)
        # 5. env_type特定
        args, context = self._apply_env_type(args, context)
        # 6. コマンド特定
        args, context = self._apply_command(args, context)
        # 7. 残りの引数からproblem_name, contest_nameを特定
        args, context = self._apply_names(args, context)
        # 8. contest_current_path特定
        context = self._apply_contest_current_path(context)
        # 8.5. workspace_path特定
        context = self._apply_workspace_path(args, context)
        # 9. env_jsonをcontextにセット
        context = self._apply_env_json(context, env_jsons)
        # 9.5. dockerfileの内容をセット
        context = self._apply_dockerfile(context)
        # 9.6. oj.Dockerfileの内容をセット
        context = self._apply_oj_dockerfile(context)
        # 10. system_info.jsonへ保存
        self._save_context_to_system_info(context)
        return context

    def _apply_system_info(self, context: ExecutionContext) -> ExecutionContext:
        system_info = self.system_info_provider.load()
        context.command_type = system_info["command"]
        context.language = system_info["language"]
        context.env_type = system_info["env_type"]
        context.contest_name = system_info["contest_name"]
        context.problem_name = system_info["problem_name"]
        context.contest_current_path = system_info["contest_current_path"]
        context.env_json = system_info["env_json"]
        return context

    def _apply_old_execution_context(self, context: ExecutionContext) -> ExecutionContext:
        # ExecutionContextのコピーを作成してold_execution_contextにセット
        import copy
        context.old_execution_context = copy.deepcopy(context)
        return context

    def _validate_env_json(self, data: dict, path: str):
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

    def _load_all_env_jsons(self, base_dir: str) -> List[dict]:
        env_jsons = []
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == "env.json":
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self._validate_env_json(data, path)
                        env_jsons.append(data)
                    except Exception as e:
                        raise RuntimeError(f"{path} の読み込みまたはバリデーションに失敗: {e}")
        return env_jsons

    def _apply_language(self, args: list, context: ExecutionContext, env_jsons: List[dict]) -> tuple:
        language_alias_map = self._extract_language_and_aliases(env_jsons)
        for idx, arg in enumerate(args):
            for lang, aliases in language_alias_map.items():
                if arg == lang or arg in aliases:
                    for env_json in env_jsons:
                        if lang in env_json:
                            context.language = lang
                            context.env_json = env_json
                            new_args = args[:idx] + args[idx+1:]
                            return new_args, context
        return args, context

    def _extract_language_and_aliases(self, env_jsons: List[dict]) -> Dict[str, List[str]]:
        result = {}
        for env_json in env_jsons:
            for lang, conf in env_json.items():
                aliases = conf.get("aliases", [])
                result[lang] = aliases
        return result

    def _apply_env_type(self, args: list, context: ExecutionContext) -> tuple:
        if not context.env_json or not context.language:
            return args, context
        env_types = context.env_json[context.language]["env_types"] if "env_types" in context.env_json[context.language] else {}
        for idx, arg in enumerate(args):
            for env_type_name, env_type_conf in env_types.items():
                aliases = env_type_conf["aliases"] if "aliases" in env_type_conf else []
                if arg == env_type_name or arg in aliases:
                    context.env_type = env_type_name
                    new_args = args[:idx] + args[idx+1:]
                    return new_args, context
        return args, context

    def _apply_command(self, args: list, context: ExecutionContext) -> tuple:
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

    def _apply_names(self, args: list, context: ExecutionContext) -> tuple:
        # 残り引数が2つまでなら、problem_name, contest_nameに割り当て
        if len(args) > 2:
            raise ValueError(f"引数が多すぎます: {args}")
        
        # 意図した動きなので直さないこと。
        keys = ["problem_name", "contest_name"]
        for key, arg in zip(keys, reversed(args)):
            setattr(context, key, arg)
        return [], context

    def _apply_contest_current_path(self, context: ExecutionContext) -> ExecutionContext:
        if context.env_json and context.language:
            contest_current_path = context.env_json[context.language]["contest_current_path"] if "contest_current_path" in context.env_json[context.language] else None
            if contest_current_path:
                context.contest_current_path = contest_current_path
        if not context.contest_current_path:
            context.contest_current_path = "./contest_current"
        return context

    def _apply_env_json(self, context: ExecutionContext, env_jsons: List[dict]) -> ExecutionContext:
        # 既にenv_jsonがセットされていれば何もしない
        if context.env_json:
            return context
        # languageが特定されていればenv_jsonをセット
        if context.language:
            for env_json in env_jsons:
                if context.language in env_json:
                    context.env_json = env_json
                    break
        return context

    def _apply_dockerfile(self, context: ExecutionContext) -> ExecutionContext:
        dockerfile_path = None
        if context.env_json and context.language:
            dockerfile_path = context.env_json[context.language]["dockerfile_path"] if context.language in context.env_json and "dockerfile_path" in context.env_json[context.language] else None
        if dockerfile_path:
            try:
                context.dockerfile = self.dockerfile_loader(dockerfile_path)
            except Exception:
                context.dockerfile = None
        return context

    def _apply_oj_dockerfile(self, context: ExecutionContext) -> ExecutionContext:
        import os
        oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
        try:
            context.oj_dockerfile = self.dockerfile_loader(oj_dockerfile_path)
        except Exception:
            context.oj_dockerfile = None
        return context

    def _apply_workspace_path(self, args, context):
        import os
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

    def _save_context_to_system_info(self, context: ExecutionContext):
        info = {
            "command": context.command_type,
            "language": context.language,
            "env_type": context.env_type,
            "contest_name": context.contest_name,
            "problem_name": context.problem_name,
            "contest_current_path": context.contest_current_path,
            "env_json": context.env_json
        }
        self.system_info_provider.save(info)