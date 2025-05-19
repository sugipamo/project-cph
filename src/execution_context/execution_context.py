from dataclasses import dataclass
from typing import Dict

from .user_input_parser import UserInputParseResult

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

    def get_env_config(self) -> dict:
        return self.env_json.get('env', {})

    def get_language_config(self) -> dict:
        return self.env_json.get('language', {})

    def get_command_config(self) -> dict:
        return self.env_json.get('command', {})

    def get_contest_config(self) -> dict:
        return self.env_json.get('contest', {})

    def get_problem_config(self) -> dict:
        return self.env_json.get('problem', {})

    def get_old_system_info(self) -> dict:
        return self.old_system_info 