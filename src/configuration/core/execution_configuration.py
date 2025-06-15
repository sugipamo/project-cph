"""実行用統一設定（不変） - すべてのコンテキストクラスを統合"""
from dataclasses import dataclass
from typing import Dict, List

from .execution_paths import ExecutionPaths
from .output_config import OutputConfig
from .runtime_config import RuntimeConfig


@dataclass(frozen=True)
class ExecutionConfiguration:
    """実行用統一設定（不変） - すべてのコンテキストクラスを統合"""

    # 基本情報
    contest_name: str
    problem_name: str
    language: str
    env_type: str
    command_type: str

    # パス情報
    paths: ExecutionPaths

    # ファイルパターン
    file_patterns: Dict[str, List[str]]

    # 実行設定
    runtime_config: RuntimeConfig

    # 出力設定
    output_config: OutputConfig

    def to_template_dict(self) -> Dict[str, str]:
        """変数展開用辞書を生成

        Returns:
            変数展開用の辞書
        """
        return {
            "contest_name": self.contest_name,
            "problem_name": self.problem_name,
            "language": self.language,
            "env_type": self.env_type,
            "command_type": self.command_type,
            # Path variables with both formats for compatibility
            "workspace": str(self.paths.workspace),
            "contest_current": str(self.paths.contest_current),
            "contest_stock": str(self.paths.contest_stock),
            "contest_template": str(self.paths.contest_template),
            "contest_temp": str(self.paths.contest_temp),
            # Path variables with _path suffix as expected by JSON configurations
            "workspace_path": str(self.paths.workspace),
            "contest_current_path": str(self.paths.contest_current),
            "contest_stock_path": str(self.paths.contest_stock),
            "contest_template_path": str(self.paths.contest_template),
            "contest_temp_path": str(self.paths.contest_temp),
            # Runtime configuration
            "language_id": self.runtime_config.language_id,
            "source_file_name": self.runtime_config.source_file_name,
            "run_command": self.runtime_config.run_command,
        }

    def get_file_pattern(self, pattern_name: str) -> List[str]:
        """ファイルパターンの取得

        Args:
            pattern_name: パターン名

        Returns:
            ファイルパターンのリスト
        """
        return self.file_patterns.get(pattern_name, [])
