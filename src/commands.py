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
    "python": {"aliases": []},
    "pypy": {"aliases": ["py"]},
    "rust": {"aliases": ["rs"]},
}

import re
import argparse
import sys
from pathlib import Path
import asyncio
import json

# --- 定数 ---
CONTEST_STOCKS_DIR = Path("../contest_stocks")
CONTEST_CURRENT_DIR = Path("../contest_current")
CONTEST_TEMPLATE_DIR = Path("../contest_template")

# --- CLIコマンドパース用関数 ---
def parse_args():
    parser = argparse.ArgumentParser(description="競技プログラミング支援ツール CLI")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser.parse_args()

# --- コマンド実装の骨組み ---
async def login():
    """online-judge-toolsでログインする"""
    raise NotImplementedError("loginコマンドの実装が必要です")

async def open_problem(contest_name, problem_name, language_name):
    """問題データ取得・contest_stocksから移動/contest_templateからコピー"""
    raise NotImplementedError("open_problemコマンドの実装が必要です")

async def test_problem(contest_name, problem_name, language_name):
    """独自実装でテストを行う"""
    raise NotImplementedError("test_problemコマンドの実装が必要です")

async def submit_problem(contest_name, problem_name, language_name):
    """online-judge-toolsで提出する"""
    raise NotImplementedError("submit_problemコマンドの実装が必要です")

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
        print(f"パース結果: {self.parsed}")
        # 未特定の要素があれば警告（出力しないように変更）
        # for k, v in self.parsed.items():
        #     if v is None:
        #         print(f"警告: {k}が特定できませんでした。") 

    def get_effective_args(self, info_json_path="contest_current/info.json"):
        """
        info.jsonの値も考慮して最終的な値（contest_name, problem_name, language_name, command）を返す。
        特にcommandがopenの場合はcontest_nameがNoneでもinfo.jsonから必ず補完する。
        """
        effective = self.parsed.copy()
        # info.jsonがあれば補完
        try:
            with open(info_json_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            # openコマンド時はcontest_nameがNoneでも必ず補完
            if effective["command"] == "open":
                if effective["contest_name"] is None:
                    effective["contest_name"] = info.get("contest_name")
            for k in ["problem_name", "language_name"]:
                if effective[k] is None:
                    effective[k] = info.get(k)
        except Exception:
            pass
        return effective 