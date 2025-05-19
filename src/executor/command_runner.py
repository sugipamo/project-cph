from typing import Optional, List, Dict
from dataclasses import dataclass
from src.command_registry.command_registry import CommandDefinitionRegistry, CommandDefinition
from src.command_registry.user_input_parser import UserInputParser, UserInputParseResult
from src.operations.di_container import DIContainer

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

class CommandRunner:
    """
    コマンドを実行するクラス
    """
    def __init__(self, env_context: EnvContext, command_definition: CommandDefinition, di_container: DIContainer):
        self.env_context = env_context
        self.command_definition = command_definition
        self.di_container = di_container

    def run(self) -> None:
        """
        コマンドを実行する
        """
        # 実行情報の表示
        print(f"実行: {self.command_definition.name}")
        print(f"言語: {self.env_context.language}")
        print(f"コンテスト: {self.env_context.contest_name}")
        print(f"問題: {self.env_context.problem_name}")
        
        # コマンドの実行
        for cmd in self.command_definition.run:
            # 実行環境に応じたドライバーを取得
            driver = self.di_container.resolve("docker_driver" if self.env_context.env_type == "docker" else "shell_driver")
            
            # コマンドの実行
            result = driver.execute(cmd)
            if not result.is_success():
                raise RuntimeError(f"コマンド実行エラー: {result.stderr}")

class CommandInitializer:
    """
    コマンドの初期化を行うクラス
    """
    def __init__(self, di_container: DIContainer):
        self.di_container = di_container

    def initialize(self, args: List[str]) -> CommandRunner:
        """
        コマンドを初期化する
        
        Args:
            args: コマンドライン引数
            
        Returns:
            CommandRunner: 初期化されたコマンドランナー
            
        Raises:
            ValueError: パースまたは検証に失敗した場合
        """
        # パーサーの初期化と引数のパース
        parser = UserInputParser()
        parse_result = parser.parse_and_validate(args)
        
        # レジストリの初期化とコマンド定義の取得
        registry = CommandDefinitionRegistry.from_parse_result(parse_result)
        if not registry.validate_command(parse_result.command):
            raise ValueError(f"コマンド '{parse_result.command}' の定義が見つかりません")
        
        cmd_def = registry.find_command_definition(parse_result.command)
        
        # 実行環境のコンテキストを生成
        env_context = EnvContext.from_parse_result(parse_result)
        
        return CommandRunner(env_context, cmd_def, self.di_container) 