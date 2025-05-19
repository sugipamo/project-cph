from typing import Optional, List, Dict
from dataclasses import dataclass
from src.execution_context.user_input_parser import UserInputParser, UserInputParseResult
from src.execution_context.execution_context import ExecutionContext


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
        
        # 引数をパースして検証
        parse_result = parser.parse_and_validate(args)
        
        # レジストリの初期化
        registry = CommandDefinitionRegistry.from_env_json(parse_result.env_json, parse_result.language)
        
        # コマンド定義を取得
        cmd_def = registry.find_command_definition(parse_result.command)
        if not cmd_def:
            raise ValueError(f"コマンド '{parse_result.command}' の定義が見つかりません")
        
        # 実行環境のコンテキストを生成
        env_context = ExecutionContext.from_parse_result(parse_result)
        
        # コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {env_context.language}")
        print(f"コンテスト: {env_context.contest_name}")
        print(f"問題: {env_context.problem_name}")
        
        # TODO: コマンドの実行処理を実装
        # cmd_def.runに定義されたコマンドを順次実行
        for cmd in cmd_def.run:
            # コマンドの実行処理を実装
            pass 