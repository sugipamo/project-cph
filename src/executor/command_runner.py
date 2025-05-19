from typing import Optional, List
from src.command_registry.command_registry import CommandDefinitionRegistry
from src.command_registry.user_input_parser import UserInputParser, UserInputParseResult

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    def __init__(self):
        self.parser = None
        self.registry = None
        self._initialized = False

    def initialize(self, args: List[str]) -> None:
        """
        実行環境を初期化する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: 初期化に失敗した場合
        """
        if self._initialized:
            return

        # パーサーの初期化
        parser = UserInputParser()
        parse_result = parser.parse(args)  # 最初のパースでenv_jsonを取得
        
        # パース結果の検証
        is_valid, error_message = parse_result.validate()
        if not is_valid:
            raise ValueError(error_message)
            
        # レジストリの初期化
        registry = CommandDefinitionRegistry.from_env_json(parse_result.env_json, parse_result.language)
        
        # パーサーにレジストリを設定
        self.parser = UserInputParser(registry)
        self.registry = registry
        self._initialized = True

    def execute(self, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: パースに失敗した場合
            RuntimeError: 初期化されていない場合
        """
        if not self._initialized:
            raise RuntimeError("CommandRunnerが初期化されていません。initialize()を先に呼び出してください。")
        
        # 引数をパースして検証
        parse_result = self.parser.parse_and_validate(args)
        
        # コマンド定義を取得
        cmd_def = self.registry.find_command_definition(parse_result.command)
        
        # TODO: コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {parse_result.language}")
        print(f"コンテスト: {parse_result.contest_name}")
        print(f"問題: {parse_result.problem_name}") 