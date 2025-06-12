"""バリデーション機能の提供"""
from typing import Tuple

from ..core.execution_configuration import ExecutionConfiguration


class ConfigurationValidationService:
    """ExecutionConfigurationのバリデーション機能"""

    def __init__(self, config: ExecutionConfiguration):
        self.config = config

    def validate_execution_data(self) -> Tuple[bool, str]:
        """実行データの検証

        Returns:
            (is_valid, error_message): 検証結果とエラーメッセージ
        """
        # 基本的な検証
        if not self.config.language:
            return False, "Language is required"
        if not self.config.contest_name:
            return False, "Contest name is required"
        if not self.config.problem_name:
            return False, "Problem name is required"
        return True, ""

    def validate_paths(self) -> Tuple[bool, str]:
        """パス設定の検証"""
        if not self.config.paths.workspace:
            return False, "Workspace path is required"
        if not self.config.paths.contest_current:
            return False, "Contest current path is required"
        return True, ""

    def validate_runtime_config(self) -> Tuple[bool, str]:
        """実行時設定の検証"""
        if not self.config.runtime_config.language_id:
            return False, "Language ID is required"
        if not self.config.runtime_config.run_command:
            return False, "Run command is required"
        if self.config.runtime_config.timeout_seconds <= 0:
            return False, "Timeout must be positive"
        return True, ""

    def validate_all(self) -> Tuple[bool, str]:
        """全設定の包括的な検証"""
        validations = [
            self.validate_execution_data(),
            self.validate_paths(),
            self.validate_runtime_config()
        ]

        for is_valid, error_message in validations:
            if not is_valid:
                return False, error_message

        return True, ""
