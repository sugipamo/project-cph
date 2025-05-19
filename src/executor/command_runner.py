from typing import List
from src.execution_context.user_input_parser import UserInputParser
from src.execution_context.execution_context import ExecutionContext
from src.operations.command_definition_registry import CommandDefinitionRegistry


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
        context = parser.parse_and_validate(args)
        
        # レジストリの初期化
        registry = CommandDefinitionRegistry.from_env_json(context.env_json, context.language)
        
        # コマンド定義を取得
        cmd_def = registry.find_command_definition(context.command_name)
        if not cmd_def:
            raise ValueError(f"コマンド '{context.command_name}' の定義が見つかりません")
        
        # コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {context.language}")
        print(f"コンテスト: {context.contest_name}")
        print(f"問題: {context.problem_name}")
        
        # TODO: コマンドの実行処理を実装
        # cmd_def.runに定義されたコマンドを順次実行
        for cmd in cmd_def.run:
            # コマンドの実行処理を実装
            pass 