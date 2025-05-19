from dataclasses import dataclass
from typing import Dict

from .user_input_parser import UserInputParseResult

@dataclass
class EnvContext:
    """
    実行環境のコンテキストを保持するクラス
    """
    language: str
    env_type: str
    contest_name: str
    problem_name: str
    contest_current_path: str
    env_json: Dict
    old_system_info: Dict

    @classmethod
    def from_parse_result(cls, parse_result: UserInputParseResult) -> 'EnvContext':
        """
        UserInputParseResultからEnvContextを生成する
        
        Args:
            parse_result: パース結果
            
        Returns:
            EnvContext: 実行環境のコンテキスト
        """
        return cls(
            language=parse_result.language,
            env_type=parse_result.env_type,
            contest_name=parse_result.contest_name,
            problem_name=parse_result.problem_name,
            contest_current_path=parse_result.contest_current_path,
            env_json=parse_result.env_json,
            old_system_info=parse_result.old_system_info
        )

    def get_env_config(self) -> Dict:
        """
        環境設定を取得する
        
        Returns:
            Dict: 環境設定
        """
        return self.env_json.get('env', {})

    def get_language_config(self) -> Dict:
        """
        言語設定を取得する
        
        Returns:
            Dict: 言語設定
        """
        return self.env_json.get('language', {})

    def get_command_config(self) -> Dict:
        """
        コマンド設定を取得する
        
        Returns:
            Dict: コマンド設定
        """
        return self.env_json.get('command', {})

    def get_contest_config(self) -> Dict:
        """
        コンテスト設定を取得する
        
        Returns:
            Dict: コンテスト設定
        """
        return self.env_json.get('contest', {})

    def get_problem_config(self) -> Dict:
        """
        問題設定を取得する
        
        Returns:
            Dict: 問題設定
        """
        return self.env_json.get('problem', {})

    def get_old_system_info(self) -> Dict:
        """
        前回の実行情報を取得する
        
        Returns:
            Dict: 前回の実行情報
        """
        return self.old_system_info