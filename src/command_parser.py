"""
仕様書:
- CLIコマンドを受け取り、パースする
- online-judge-tools用のコマンドに変換する
- main.py {contest_name} {command} {problem_name} {language_name} の順不同引数に対応
- 正規表現でコマンド一致条件を設定し、一致したものを当てはめる
- コマンドは右から順番、parse順に確認し、適用済みの要素は検証をスキップする
- parse順: problem_name → contest_name → language_name
- 定数はこのコメント下に記載
"""

# 定数
CONTEST_NAMES = ["abc", "arc", "agc", "ahc"]
COMMANDS = {
    "login": {"aliases": []},
    "open": {"aliases": ["o"]},
    "test": {"aliases": ["t"]},
    "submit": {"aliases": ["s"]},
}
PROBLEM_NAMES = ["a", "b", "c", "d", "e", "f", "g", "ex"]
LANGUAGES = {
    "python": {"aliases": ["python3"]},
    "pypy": {"aliases": ["pypy3", "py"]},
    "rust": {"aliases": ["rs", "rustc"]},
}
EXEC_MODES = ["docker", "local"]

import argparse
from src.language_env.info_json_manager import InfoJsonManager
from src.path_manager.unified_path_manager import UnifiedPathManager

# --- CLIコマンドパース用関数 ---
def parse_args():
    parser = argparse.ArgumentParser(description="競技プログラミング支援ツール CLI")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args()

class CommandParser:
    @property
    def default_parsed(self):
        return {
            "contest_name": None,
            "command": None,
            "problem_name": None,
            "language_name": None,
            "exec_mode": None
        }

    def __init__(self):
        self.parsed = self.default_parsed.copy()
        self.upm = UnifiedPathManager()

    def parse(self, args):
        # 引数を順不同でパースし、各要素を特定
        self.parsed = self.default_parsed.copy()
        used = set()
        # 右から順に判定
        for i, arg in enumerate(reversed(args)):
            # exec_mode
            if self.parsed["exec_mode"] is None and arg in EXEC_MODES:
                self.parsed["exec_mode"] = arg
                used.add(len(args)-1-i)
                continue
            # problem_name
            if self.parsed["problem_name"] is None and arg in PROBLEM_NAMES:
                self.parsed["problem_name"] = arg
                used.add(len(args)-1-i)
                continue
            # contest_name（CONTEST_NAMESのどれかにstartswithで反応すればOK）
            if self.parsed["contest_name"] is None:
                for cname in CONTEST_NAMES:
                    if arg.startswith(cname) or cname.startswith(arg):
                        self.parsed["contest_name"] = arg
                        used.add(len(args)-1-i)
                        break
                if self.parsed["contest_name"] is not None:
                    continue
            # language_name
            for lang, v in LANGUAGES.items():
                if self.parsed["language_name"] is None and (arg == lang or arg in v["aliases"]):
                    self.parsed["language_name"] = lang
                    used.add(len(args)-1-i)
                    break
            # command
            for cmd, v in COMMANDS.items():
                if self.parsed["command"] is None and (arg == cmd or arg in v["aliases"]):
                    self.parsed["command"] = cmd
                    used.add(len(args)-1-i)
                    break
        # Noneでない要素のみ表示
        filtered = {k: v for k, v in self.parsed.items() if v is not None}
        # 未特定の要素があれば警告（出力しないように変更）
        # for k, v in self.parsed.items():
        #     if v is None:
        #         print(f"警告: {k}が特定できませんでした。") 

    def get_effective_args(self, info_json_path=None):
        """
        system_info.jsonの値も考慮して最終的な値（contest_name, problem_name, language_name, command, exec_mode）を返す。
        contest_name, problem_name, language_name, exec_modeのいずれかがNoneならsystem_info.jsonから補完する。
        """
        effective = self.parsed.copy()
        # system_info.jsonがあれば補完
        try:
            if info_json_path is None:
                info_json_path = self.upm.info_json()
            manager = InfoJsonManager(info_json_path)
            info = manager.data
            for k in ["contest_name", "problem_name", "language_name", "exec_mode"]:
                if effective[k] is None:
                    effective[k] = info.get(k)
        except Exception:
            pass
        return effective
