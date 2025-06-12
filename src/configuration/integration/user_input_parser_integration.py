"""user_input_parser.pyでの新設定システム統合"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.execution_configuration import ExecutionConfiguration
from ..loaders.configuration_loader import ConfigurationLoader
from ..factories.configuration_factory import ExecutionConfigurationFactory
from ..adapters.execution_context_adapter import ExecutionContextAdapter
from ..expansion.template_expander import TemplateExpander


class UserInputParserIntegration:
    """user_input_parser.pyでの新設定システム統合"""
    
    def __init__(self, contest_env_dir: str = "./contest_env", system_config_dir: str = "./config/system"):
        """初期化
        
        Args:
            contest_env_dir: contest_env ディレクトリのパス
            system_config_dir: システム設定ディレクトリのパス
        """
        self.config_loader = ConfigurationLoader(
            Path(contest_env_dir),
            Path(system_config_dir)
        )
        self.config_factory = ExecutionConfigurationFactory(self.config_loader)
    
    def create_execution_configuration_from_context(self, 
                                                   command_type: str,
                                                   language: str,
                                                   contest_name: str,
                                                   problem_name: str,
                                                   env_type: str,
                                                   env_json: Dict[str, Any]) -> ExecutionConfiguration:
        """既存のコンテキスト情報から新しいExecutionConfigurationを生成
        
        Args:
            command_type: コマンドタイプ
            language: プログラミング言語
            contest_name: コンテスト名
            problem_name: 問題名
            env_type: 環境タイプ
            env_json: 環境設定JSON
            
        Returns:
            ExecutionConfiguration: 新しい実行設定
        """
        # 既存の方法でExecutionContextを作成
        mock_context = type('MockContext', (), {
            'command_type': command_type,
            'language': language,
            'contest_name': contest_name,
            'problem_name': problem_name,
            'env_type': env_type,
            'env_json': env_json
        })()
        
        # 新ファクトリーで変換
        return self.config_factory.create_from_context(mock_context)
    
    def create_execution_context_adapter(self, 
                                       command_type: str,
                                       language: str,
                                       contest_name: str,
                                       problem_name: str,
                                       env_type: str,
                                       env_json: Dict[str, Any]) -> ExecutionContextAdapter:
        """既存ExecutionContextとの互換性を保つアダプターを生成
        
        Args:
            command_type: コマンドタイプ
            language: プログラミング言語
            contest_name: コンテスト名
            problem_name: 問題名
            env_type: 環境タイプ
            env_json: 環境設定JSON
            
        Returns:
            ExecutionContextAdapter: 互換性アダプター
        """
        # ExecutionConfigurationを生成
        config = self.create_execution_configuration_from_context(
            command_type, language, contest_name, problem_name, env_type, env_json
        )
        
        # TemplateExpanderを生成
        expander = TemplateExpander(config)
        
        # アダプターを作成
        return ExecutionContextAdapter(config, expander)
    
    def validate_new_system_compatibility(self, 
                                        old_context,
                                        new_adapter: ExecutionContextAdapter) -> bool:
        """旧システムと新システムの互換性を検証
        
        Args:
            old_context: 既存のExecutionContext
            new_adapter: 新しいアダプター
            
        Returns:
            bool: 互換性があるかどうか
        """
        try:
            # 基本プロパティの一致確認
            if (hasattr(old_context, 'contest_name') and 
                old_context.contest_name != new_adapter.contest_name):
                return False
            
            if (hasattr(old_context, 'language') and 
                old_context.language != new_adapter.language):
                return False
            
            # テンプレート展開の一致確認
            test_template = "{contest_name}/{language}"
            
            if hasattr(old_context, 'format_string'):
                old_result = old_context.format_string(test_template)
                new_result = new_adapter.format_string(test_template)
                
                if old_result != new_result:
                    return False
            
            return True
            
        except Exception:
            return False


def create_new_execution_context(command_type: str,
                               language: str,
                               contest_name: str,
                               problem_name: str,
                               env_type: str,
                               env_json: Dict[str, Any],
                               resolver=None) -> ExecutionContextAdapter:
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
        ExecutionContextAdapter: 互換性アダプター
    """
    integration = UserInputParserIntegration()
    return integration.create_execution_context_adapter(
        command_type, language, contest_name, problem_name, env_type, env_json
    )