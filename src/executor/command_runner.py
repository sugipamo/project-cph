from typing import Optional, List
from src.command_registry.command_registry import CommandDefinitionRegistry
from src.command_registry.user_input_parser import UserInputParser, UserInputParseResult

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    @classmethod
    def run(cls, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: パースに失敗した場合
        """
        # パーサーの初期化
        parser = UserInputParser()
        parse_result = parser.parse(args)
        
        # パース結果の検証
        is_valid, error_message = parse_result.validate()
        if not is_valid:
            raise ValueError(error_message)
            
        # レジストリの初期化
        registry = CommandDefinitionRegistry.from_env_json(parse_result.env_json, parse_result.language)
        
        # パーサーにレジストリを設定
        parser = UserInputParser(registry)
        
        # 引数をパースして検証
        parse_result = parser.parse_and_validate(args)
        
        # コマンド定義を取得
        cmd_def = registry.find_command_definition(parse_result.command)
        
        # TODO: コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {parse_result.language}")
        print(f"コンテスト: {parse_result.contest_name}")
        print(f"問題: {parse_result.problem_name}") 