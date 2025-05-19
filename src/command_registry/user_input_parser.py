import os
import json
from typing import List, Dict, Optional, Tuple

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
                "env_json": None
            }
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
    def save(self, info: dict):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

class UserInputParser:
    """
    CLI等から渡される引数リストをパースし、必須情報を抽出・バリデーションするクラス。
    """
    @classmethod
    def parse(cls, args: list, system_info_provider: Optional[SystemInfoProvider] = None) -> 'UserInputParseResult':
        """
        contest_env配下のenv.jsonを全て読み込み、
        言語・env_type・コマンドを特定し、使用済みindexをused_flagsで管理する。
        未指定項目はsystem_info.jsonから補完する。
        パース結果にはcontest_current_pathと旧system_infoも含める。
        """
        if system_info_provider is None:
            system_info_provider = LocalSystemInfoProvider()

        old_system_info = system_info_provider.load()
        # system_infoをコピーして道中で直接値を更新
        system_info = dict(old_system_info)  # コピー

        # system_info.jsonの情報を復元
        if old_system_info:
            # 前回の値を復元（引数で上書きされる可能性あり）
            system_info.update({
                "command": old_system_info.get("command"),
                "language": old_system_info.get("language"),
                "env_type": old_system_info.get("env_type"),
                "contest_name": old_system_info.get("contest_name"),
                "problem_name": old_system_info.get("problem_name"),
                "contest_current_path": old_system_info.get("contest_current_path"),
                "env_json": old_system_info.get("env_json")
            })

        env_jsons = cls.load_all_env_jsons(CONTEST_ENV_DIR)
        language_alias_map = cls.extract_language_and_aliases(env_jsons)
        used_flags = [False] * len(args)
        matched_env_json, lang_idx = cls.find_env_json_by_language(args + [old_system_info["language"]], language_alias_map, env_jsons)
        lang = None
        if matched_env_json:
            lang = next(iter(matched_env_json.keys()))

        if lang_idx is not None:
            if lang_idx < len(args):
                used_flags[lang_idx] = True
            system_info["language"] = lang

        matched_env_type, env_type_idx = cls.find_env_type_by_args(args, matched_env_json, used_flags)
        if env_type_idx is not None:
            used_flags[env_type_idx] = True
            system_info["env_type"] = matched_env_type

        matched_command, cmd_idx = cls.find_command_by_args(args, matched_env_json, used_flags)
        if cmd_idx is not None:
            used_flags[cmd_idx] = True
            system_info["command"] = matched_command

        unused_args = [arg for arg, used in zip(args, used_flags) if not used]
        if len(unused_args) > 2:
            raise ValueError(f"引数が多すぎます: {unused_args}")
        
        for key, arg in zip(["problem_name", "contest_name"], reversed(unused_args)):
            system_info[key] = arg

        # contest_current_pathの特定
        contest_current_path = None
        if matched_env_json:
            contest_current_path = matched_env_json[lang].get("contest_current_path")
        if not contest_current_path:
            contest_current_path = "./contest_current"
        system_info["contest_current_path"] = contest_current_path
        # パース結果を返す
        result = UserInputParseResult(
            command=system_info.get("command"),
            language=system_info.get("language"),
            env_type=system_info.get("env_type"),
            contest_name=system_info.get("contest_name"),
            problem_name=system_info.get("problem_name"),
            env_json=matched_env_json,
            contest_current_path=system_info.get("contest_current_path"),
            old_system_info=old_system_info
        )
        system_info_provider.save(system_info)

        return result

    @classmethod
    def load_all_env_jsons(cls, base_dir: str) -> List[dict]:
        """
        base_dir配下の全てのenv.jsonを再帰的に探索し、リストで返す。
        """
        env_jsons = []
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == "env.json":
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            env_jsons.append(json.load(f))
                    except Exception as e:
                        print(f"[WARN] {path} の読み込みに失敗: {e}")
        return env_jsons

    @classmethod
    def extract_language_and_aliases(cls, env_jsons: List[dict]) -> Dict[str, List[str]]:
        """
        env.jsonリストから言語名とそのエイリアス一覧を抽出する。
        戻り値: { 言語名: [エイリアス, ...] }
        """
        result = {}
        for env_json in env_jsons:
            for lang, conf in env_json.items():
                aliases = conf.get("aliases", [])
                result[lang] = aliases
        return result

    @classmethod
    def find_env_json_by_language(cls, args: list, language_alias_map: Dict[str, List[str]], env_jsons: List[dict]) -> Tuple[Optional[dict], Optional[int]]:
        """
        入力引数(args)の中から言語名またはエイリアスに一致するものを探し、
        該当するenv.json（dict）と使用したindexを返す。
        """
        for idx, arg in enumerate(args):
            for lang, aliases in language_alias_map.items():
                if arg == lang or arg in aliases:
                    for env_json in env_jsons:
                        if lang in env_json:
                            return env_json, idx
        return None, None

    @classmethod
    def find_env_type_by_args(cls, args: list, env_json: dict, used_flags: List[bool]) -> Tuple[Optional[str], Optional[int]]:
        """
        env_jsonのenv_typesからenv_type名・エイリアスを取得し、
        args内で未使用かつ一致するものがあれば(env_type名, index)を返す。
        """
        if not env_json:
            return None, None
        lang = next(iter(env_json.keys()))
        env_types = env_json[lang].get("env_types", {})
        for idx, arg in enumerate(args):
            if used_flags[idx]:
                continue
            for env_type_name, env_type_conf in env_types.items():
                aliases = env_type_conf.get("aliases", [])
                if arg == env_type_name or arg in aliases:
                    return env_type_name, idx
        return None, None

    @classmethod
    def find_command_by_args(cls, args: list, env_json: dict, used_flags: List[bool]) -> Tuple[Optional[str], Optional[int]]:
        """
        env_jsonのcommandsからコマンド名・エイリアスを取得し、
        args内で未使用かつ一致するものがあれば(command名, index)を返す。
        """
        if not env_json:
            return None, None
        lang = next(iter(env_json.keys()))
        commands = env_json[lang].get("commands", {})
        for idx, arg in enumerate(args):
            if used_flags[idx]:
                continue
            for cmd_name, cmd_conf in commands.items():
                aliases = cmd_conf.get("aliases", [])
                if arg == cmd_name or arg in aliases:
                    return cmd_name, idx
        return None, None

class UserInputParseResult:
    """
    パース結果（必須情報）を保持するデータクラス。
    contest_current_path, old_system_infoも含める。
    """
    def __init__(self, command: str, language: str, env_type: str, contest_name: str, problem_name: str, env_json: dict, contest_current_path: str, old_system_info: dict):
        self.command = command
        self.language = language
        self.env_type = env_type
        self.contest_name = contest_name
        self.problem_name = problem_name
        self.env_json = env_json
        self.contest_current_path = contest_current_path
        self.old_system_info = old_system_info

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        基本的なバリデーションを行う
        
        Returns:
            Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
        """
        # 必須項目の存在チェック
        missing_fields = []
        if not self.command:
            missing_fields.append("コマンド")
        if not self.language:
            missing_fields.append("言語")
        if not self.contest_name:
            missing_fields.append("コンテスト名")
        if not self.problem_name:
            missing_fields.append("問題名")
            
        if missing_fields:
            return False, f"以下の項目が指定されていません: {', '.join(missing_fields)}"
            
        # env_jsonの存在チェック
        if not self.env_json:
            return False, "環境設定ファイル(env.json)が見つかりません"
            
        # 言語がenv_jsonに存在するかチェック
        if self.language not in self.env_json:
            return False, f"指定された言語 '{self.language}' は環境設定ファイルに存在しません"
            
        return True, None

class EnvJsonInfo:
    """
    1つのenv.jsonから抽出した言語名・エイリアス・env_type・command等の情報をまとめて保持する補助クラス。
    """
    def __init__(self, language: str, language_aliases: List[str], env_types: Dict[str, List[str]], commands: Dict[str, List[str]], raw_json: dict):
        self.language = language
        self.language_aliases = language_aliases
        self.env_types = env_types  # env_type名→エイリアス
        self.commands = commands    # command名→エイリアス
        self.raw_json = raw_json 