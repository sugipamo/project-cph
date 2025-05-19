from typing import Optional, List
from .command_registry import CommandDefinitionRegistry
from .user_input_parser import UserInputParser, UserInputParseResult

class CommandExecutor:
    """
    コマンドライン引数からコマンドを実行するエントリーポイントとなるクラス
    """
    def __init__(self):
        self.parser = None
        self.registry = None

    def initialize(self, args: List[str]) -> None:
        """
        実行環境を初期化する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: 初期化に失敗した場合
        """
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

    def execute(self, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: パースに失敗した場合
            RuntimeError: 初期化されていない場合
        """
        if not self.parser or not self.registry:
            raise RuntimeError("CommandExecutorが初期化されていません。initialize()を先に呼び出してください。")
        
        # 引数をパースして検証
        parse_result = self.parser.parse_and_validate(args)
        
        # コマンド定義を取得
        cmd_def = self.registry.find_command_definition(parse_result.command)
        
        # TODO: コマンドを実行
        print(f"実行: {cmd_def.name}")
        print(f"言語: {parse_result.language}")
        print(f"コンテスト: {parse_result.contest_name}")
        print(f"問題: {parse_result.problem_name}") 