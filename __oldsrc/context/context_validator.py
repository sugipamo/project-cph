"""Execution context validator
"""
from typing import Optional

from src.context.utils.execution_validation_utils import validate_execution_context_data


class ContextValidator:
    """実行コンテキストのバリデーションを担当"""

    @staticmethod
    def validate_execution_context(execution_data) -> tuple[bool, Optional[str]]:
        """基本的なバリデーションを行う

        Args:
            execution_data: バリデーション対象のデータ

        Returns:
            Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
        """
        return validate_execution_context_data(
            execution_data.command_type,
            execution_data.language,
            execution_data.contest_name,
            execution_data.problem_name,
            execution_data.env_json
        )

    @staticmethod
    def validate_required_fields(execution_data) -> tuple[bool, Optional[str]]:
        """必須フィールドのバリデーション

        Args:
            execution_data: バリデーション対象のデータ

        Returns:
            Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
        """
        if not execution_data.language:
            return False, "言語が指定されていません"

        if not execution_data.env_json:
            return False, "環境設定が見つかりません"

        if execution_data.language not in execution_data.env_json:
            return False, f"言語 '{execution_data.language}' の設定が見つかりません"

        return True, None
