"""user_input_parser.pyでの新設定システム統合"""
from typing import Any, Dict

from src.configuration.config_manager import TypedExecutionConfiguration, TypeSafeConfigNodeManager


class UserInputParserIntegration:
    """user_input_parser.pyでの新設定システム統合"""

    def __init__(self, contest_env_dir: str = "./contest_env", system_config_dir: str = "./config/system"):
        """初期化

        Args:
            contest_env_dir: contest_env ディレクトリのパス
            system_config_dir: システム設定ディレクトリのパス
        """
        self.config_manager = TypeSafeConfigNodeManager()
        self.contest_env_dir = contest_env_dir
        self.system_config_dir = system_config_dir

    def create_execution_configuration_from_context(self,
                                                   command_type: str,
                                                   language: str,
                                                   contest_name: str,
                                                   problem_name: str,
                                                   env_type: str,
                                                   env_json: Dict[str, Any]) -> TypedExecutionConfiguration:
        """既存のコンテキスト情報から新しいExecutionConfigurationを生成

        Args:
            command_type: コマンドタイプ
            language: プログラミング言語
            contest_name: コンテスト名
            problem_name: 問題名
            env_type: 環境タイプ
            env_json: 環境設定JSON

        Returns:
            TypedExecutionConfiguration: 新しい実行設定
        """
        # 設定を読み込み
        self.config_manager.load_from_files(
            self.system_config_dir, self.contest_env_dir, language
        )

        # TypeSafeConfigNodeManagerで生成
        return self.config_manager.create_execution_config(
            contest_name, problem_name, language, env_type, command_type
        )

    def create_execution_context_adapter(self,
                                       command_type: str,
                                       language: str,
                                       contest_name: str,
                                       problem_name: str,
                                       env_type: str,
                                       env_json: Dict[str, Any]):
        """既存ExecutionContextとの互換性を保つアダプターを生成

        Args:
            command_type: コマンドタイプ
            language: プログラミング言語
            contest_name: コンテスト名
            problem_name: 問題名
            env_type: 環境タイプ
            env_json: 環境設定JSON

        Returns:
            TypedExecutionConfiguration: 新しい実行設定
        """
        # ExecutionConfigurationを生成
        return self.create_execution_configuration_from_context(
            command_type, language, contest_name, problem_name, env_type, env_json
        )

    def validate_new_system_compatibility(self,
                                        old_context,
                                        new_config: TypedExecutionConfiguration) -> bool:
        """旧システムと新システムの互換性を検証

        Args:
            old_context: 既存のExecutionContext
            new_config: 新しい設定

        Returns:
            bool: 互換性があるかどうか
        """
        try:
            # 基本プロパティの一致確認
            if (hasattr(old_context, 'contest_name') and
                old_context.contest_name != new_config.contest_name):
                return False

            return not (hasattr(old_context, 'language') and old_context.language != new_config.language)

        except Exception:
            return False


def create_new_execution_context(command_type: str,
                               language: str,
                               contest_name: str,
                               problem_name: str,
                               env_type: str,
                               env_json: Dict[str, Any],
                               resolver=None) -> TypedExecutionConfiguration:
    """新設定システムを使用してExecutionContextの互換実装を作成

    既存のExecutionContext.__init__と同じシグネチャで、
    新設定システムを使用した実装を提供します。

    Args:
        command_type: コマンドタイプ
        language: プログラミング言語
        contest_name: コンテスト名
        problem_name: 問題名
        env_type: 環境タイプ
        env_json: 環境設定JSON
        resolver: リゾルバー（互換性のため）

    Returns:
        TypedExecutionConfiguration: 新しい実行設定
    """
    integration = UserInputParserIntegration()
    return integration.create_execution_context_adapter(
        command_type, language, contest_name, problem_name, env_type, env_json
    )
