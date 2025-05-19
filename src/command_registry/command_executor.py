from typing import Optional, List
from .command_registry import CommandDefinitionRegistry
from .user_input_parser import UserInputParser, UserInputParseResult

class CommandExecutor:
    """
    コマンドライン引数からコマンドを実行するエントリーポイントとなるクラス
    """
    def __init__(self, parser: UserInputParser, registry: CommandDefinitionRegistry):
        self.parser = parser
        self.registry = registry

    def execute(self, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
        """
        # 引数をパース
        parse_result = self.parser.parse(args)
        if not parse_result:
            return

        # パース結果をバリデーション
        is_valid, error_message = parse_result.validate()
        if not is_valid:
            print(f"エラー: {error_message}")
            return

        # コマンド定義を取得
        cmd_def = self.registry.find_command_definition(parse_result.command)
        if not cmd_def:
            print(f"コマンド '{parse_result.command}' の定義が見つかりません")
            return

        # TODO: コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {parse_result.language}")
        print(f"コンテスト: {parse_result.contest_name}")
        print(f"問題: {parse_result.problem_name}") 