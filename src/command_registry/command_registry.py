from dataclasses import dataclass
from typing import List, Dict, Optional
import argparse

from .user_input_parser import UserInputParseResult

@dataclass
class CommandDefinition:
    name: str
    aliases: List[str]
    description: str
    run: List[dict]

@dataclass
class ExecutionContext:
    command_name: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict
    contest_current_path: str
    old_system_info: dict

    @classmethod
    def from_parse_result(cls, parse_result: 'UserInputParseResult') -> 'ExecutionContext':
        """
        UserInputParseResultからExecutionContextを生成する
        
        Args:
            parse_result: パース結果
            
        Returns:
            ExecutionContext
        """
        return cls(
            command_name=parse_result.command,
            language=parse_result.language,
            contest_name=parse_result.contest_name,
            problem_name=parse_result.problem_name,
            env_type=parse_result.env_type,
            env_json=parse_result.env_json,
            contest_current_path=parse_result.contest_current_path,
            old_system_info=parse_result.old_system_info
        )

class CommandDefinitionRegistry:
    def __init__(self, commands: Dict[str, CommandDefinition], env_json: dict):
        self.commands = commands
        self.alias_map = self._build_alias_map()
        self._json = env_json  # env.json全体を保持

    @classmethod
    def from_env_json(cls, env_json: dict, language: str) -> "CommandDefinitionRegistry":
        commands = {}
        lang_commands = env_json.get(language, {}).get("commands", {})
        for cmd_name, cmd_data in lang_commands.items():
            commands[cmd_name] = CommandDefinition(
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

    def find_command_definition(self, name_or_alias: str) -> Optional[CommandDefinition]:
        """
        コマンド名またはエイリアスからコマンド定義を検索する
        
        Args:
            name_or_alias: コマンド名またはエイリアス
            
        Returns:
            CommandDefinition または None（コマンドが見つからない場合）
        """
        cmd_name = self.alias_map.get(name_or_alias)
        if cmd_name:
            return self.commands[cmd_name]
        return None