from dataclasses import dataclass
from typing import List, Dict, Optional
import argparse

@dataclass
class CommandInfo:
    name: str
    aliases: List[str]
    description: str
    run: List[dict]

@dataclass
class ExecutionContext:
    command: CommandInfo
    language: str
    website: str
    contest_name: str
    problem_name: str

class CommandRegistry:
    def __init__(self, commands: Dict[str, CommandInfo], env_json: dict):
        self.commands = commands
        self.alias_map = self._build_alias_map()
        self._json = env_json  # env.json全体を保持

    @classmethod
    def from_env_json(cls, env_json: dict, language: str) -> "CommandRegistry":
        commands = {}
        lang_commands = env_json.get(language, {}).get("commands", {})
        for cmd_name, cmd_data in lang_commands.items():
            commands[cmd_name] = CommandInfo(
                name=cmd_name,
                aliases=cmd_data.get("aliases", []),
                description=cmd_data.get("description", ""),
                run=cmd_data.get("run", [])
            )
        return cls(commands, env_json)

    def _build_alias_map(self):
        alias_map = {}
        for cmd in self.commands.values():
            for alias in [cmd.name] + cmd.aliases:
                alias_map[alias] = cmd.name
        return alias_map

    def resolve(self, name_or_alias: str, language: str, website: str, contest_name: str, problem_name: str) -> Optional[ExecutionContext]:
        cmd_name = self.alias_map.get(name_or_alias)
        if cmd_name:
            cmd_info = self.commands[cmd_name]
            return ExecutionContext(
                command=cmd_info,
                language=language,
                website=website,
                contest_name=contest_name,
                problem_name=problem_name
            )
        return None

    def parse_user_input(self, user_input: list) -> Optional[ExecutionContext]:
        """
        ユーザー入力の生データ（sys.argvなどのリスト）をパースし、
        必要な情報を抽出してresolveに渡す
        例: ['python3', '-m', 'cph', 't', '--language', 'python', '--website', 'atcoder', '--contest_name', 'abc123', '--problem_name', 'a']
        """
        # python3 -m ... の部分をスキップ
        args = user_input
        if args and args[0] == 'python3':
            args = args[1:]
        if args and args[0] == '-m':
            args = args[2:]  # -m cph をスキップ

        # コマンド名（またはエイリアス）は最初の要素
        if not args:
            return None
        name_or_alias = args[0]
        # 残りはオプション引数としてパース
        parser = argparse.ArgumentParser()
        parser.add_argument('--language', type=str, default=None)
        parser.add_argument('--website', type=str, default=None)
        parser.add_argument('--contest_name', type=str, default=None)
        parser.add_argument('--problem_name', type=str, default=None)
        try:
            parsed, _ = parser.parse_known_args(args[1:])
        except Exception:
            return None
        language = parsed.language
        website = parsed.website
        contest_name = parsed.contest_name
        problem_name = parsed.problem_name
        return self.resolve(name_or_alias, language, website, contest_name, problem_name) 