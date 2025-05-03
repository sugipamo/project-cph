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
CONTEST_NAMES = ["abc300", "arc100", "agc001", "ahc100"]
COMMANDS = {
    "login": {"aliases": []},
    "open": {"aliases": ["o"]},
    "test": {"aliases": ["t"]},
    "submit": {"aliases": ["s"]},
}
PROBLEM_NAMES = ["a", "b", "c", "d", "e", "f", "g", "ex"]
LANGUAGES = {
    "python": {"aliases": []},
    "pypy": {"aliases": ["py"]},
    "rust": {"aliases": ["rs"]},
}

import re

class CommandParser:
    @property
    def default_parsed(self):
        return {
            "contest_name": None,
            "command": None,
            "problem_name": None,
            "language_name": None
        }

    def __init__(self):
        self.parsed = self.default_parsed.copy()

    def parse(self, args):
        # 引数を順不同でパースし、各要素を特定
        self.parsed = self.default_parsed.copy()
        used = set()
        # 右から順に判定
        for i, arg in enumerate(reversed(args)):
            # problem_name
            if self.parsed["problem_name"] is None and arg in PROBLEM_NAMES:
                self.parsed["problem_name"] = arg
                used.add(len(args)-1-i)
                continue
            # contest_name
            if self.parsed["contest_name"] is None and arg in CONTEST_NAMES:
                self.parsed["contest_name"] = arg
                used.add(len(args)-1-i)
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
        print(f"パース結果: {self.parsed}")
        # 未特定の要素があれば警告
        for k, v in self.parsed.items():
            if v is None:
                print(f"警告: {k}が特定できませんでした。") 