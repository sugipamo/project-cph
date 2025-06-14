"""ExecutionConfiguration生成の一元化"""
import argparse
from pathlib import Path
from typing import Any, Dict, List

from ..core.execution_configuration import ExecutionConfiguration
from ..core.execution_paths import ExecutionPaths
from ..core.output_config import OutputConfig
from ..core.runtime_config import RuntimeConfig
from ..loaders.configuration_loader import ConfigurationLoader
from ..registries.language_registry import get_language_registry


class ExecutionConfigurationFactory:
    """ExecutionConfiguration生成の一元化"""

    def __init__(self, config_loader: ConfigurationLoader):
        self.config_loader = config_loader

    def create_from_args(self, args: List[str]) -> ExecutionConfiguration:
        """コマンドライン引数からExecutionConfigurationを生成

        Args:
            args: コマンドライン引数のリスト

        Returns:
            ExecutionConfiguration: 生成された実行設定
        """
        # 1. 引数解析
        parsed_args = self._parse_arguments(args)

        # 2. 設定読み込み
        config_source = self.config_loader.load_source(
            parsed_args.language,
            parsed_args.__dict__
        )

        # 3. ExecutionConfiguration構築
        return self._build_configuration(config_source.get_merged_config(), parsed_args)

    def create_from_context(self, context) -> ExecutionConfiguration:
        """既存ExecutionContextから変換（移行用）

        Args:
            context: 既存のExecutionContext

        Returns:
            ExecutionConfiguration: 変換された実行設定
        """
        basic_info = self._extract_basic_info(context)
        paths = self._create_execution_paths()
        file_patterns = self._extract_file_patterns(context, basic_info['language'])
        runtime_config = self._create_runtime_config(basic_info['language'])
        output_config = self._create_output_config()

        return ExecutionConfiguration(
            contest_name=basic_info['contest_name'],
            problem_name=basic_info['problem_name'],
            language=basic_info['language'],
            env_type=basic_info['env_type'],
            command_type=basic_info['command_type'],
            paths=paths,
            file_patterns=file_patterns,
            runtime_config=runtime_config,
            output_config=output_config
        )

    def _extract_basic_info(self, context) -> dict:
        """Extract basic information from context."""
        return {
            'contest_name': getattr(context, 'contest_name', ''),
            'problem_name': getattr(context, 'problem_name', ''),
            'language': getattr(context, 'language', ''),
            'env_type': getattr(context, 'env_type', 'local'),
            'command_type': getattr(context, 'command_type', '')
        }

    def _create_execution_paths(self) -> ExecutionPaths:
        """Create default execution paths."""
        return ExecutionPaths(
            workspace=Path('./workspace'),
            contest_current=Path('./contest_current'),
            contest_stock=Path('./contest_stock'),
            contest_template=Path('./contest_template'),
            contest_temp=Path('./contest_temp')
        )

    def _extract_file_patterns(self, context, language: str) -> dict:
        """Extract file patterns from context."""
        if hasattr(context, 'env_json') and context.env_json:
            lang_config = context.env_json.get(language, {})
            return lang_config.get('file_patterns', {})
        return {}

    def _create_runtime_config(self, language: str) -> RuntimeConfig:
        """Create runtime configuration for language."""
        language_registry = get_language_registry()
        return RuntimeConfig(
            language_id=language,
            source_file_name=f'main.{language_registry.get_file_extension(language)}',
            run_command=language_registry.get_run_command(language),
            timeout_seconds=30,
            retry_settings={}
        )

    def _create_output_config(self) -> OutputConfig:
        """Create default output configuration."""
        return OutputConfig(
            show_workflow_summary=True,
            show_step_details=True,
            show_execution_completion=True,
            format_preset='default'
        )

    def _parse_arguments(self, args: List[str]) -> argparse.Namespace:
        """コマンドライン引数を解析

        Args:
            args: 引数リスト

        Returns:
            解析結果
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('command_type', help='Command type')
        parser.add_argument('--language', '-l', default='python', help='Programming language')
        parser.add_argument('--contest', '-c', default='', help='Contest name')
        parser.add_argument('--problem', '-p', default='', help='Problem name')
        parser.add_argument('--env-type', '-e', default='local', help='Environment type')

        return parser.parse_args(args)

    def _build_configuration(self, merged_config: Dict[str, Any], parsed_args: argparse.Namespace) -> ExecutionConfiguration:
        """マージされた設定からExecutionConfigurationを構築

        Args:
            merged_config: マージされた設定
            parsed_args: 解析済み引数

        Returns:
            ExecutionConfiguration: 構築された設定
        """
        # 基本情報
        contest_name = getattr(parsed_args, 'contest', '')
        problem_name = getattr(parsed_args, 'problem', '')
        language = parsed_args.language
        env_type = getattr(parsed_args, 'env_type', 'local')
        command_type = parsed_args.command_type

        # パス情報（設定から取得、デフォルト値で補完）
        paths_config = merged_config.get('paths', {})
        paths = ExecutionPaths(
            workspace=Path(paths_config.get('workspace', './workspace')),
            contest_current=Path(paths_config.get('contest_current', './contest_current')),
            contest_stock=Path(paths_config.get('contest_stock', './contest_stock')),
            contest_template=Path(paths_config.get('contest_template', './contest_template')),
            contest_temp=Path(paths_config.get('contest_temp', './contest_temp'))
        )

        # ファイルパターン
        file_patterns = merged_config.get('file_patterns', {})

        # 言語レジストリから設定を取得
        language_registry = get_language_registry()

        # 実行設定
        runtime_settings = merged_config.get('runtime', {})
        runtime_config = RuntimeConfig(
            language_id=runtime_settings.get('language_id', language),
            source_file_name=runtime_settings.get('source_file_name', f'main.{language_registry.get_file_extension(language)}'),
            run_command=runtime_settings.get('run_command', language_registry.get_run_command(language)),
            timeout_seconds=runtime_settings.get('timeout_seconds', 30),
            retry_settings=runtime_settings.get('retry_settings', {})
        )

        # 出力設定
        output_settings = merged_config.get('output', {})
        output_config = OutputConfig(
            show_workflow_summary=output_settings.get('show_workflow_summary', True),
            show_step_details=output_settings.get('show_step_details', True),
            show_execution_completion=output_settings.get('show_execution_completion', True),
            format_preset=output_settings.get('format_preset', 'default')
        )

        return ExecutionConfiguration(
            contest_name=contest_name,
            problem_name=problem_name,
            language=language,
            env_type=env_type,
            command_type=command_type,
            paths=paths,
            file_patterns=file_patterns,
            runtime_config=runtime_config,
            output_config=output_config
        )

