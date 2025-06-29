"""Tests for execution validation utilities."""
import pytest

from src.utils.execution_validation_utils import validate_execution_context_data


class TestValidateExecutionContextData:
    """Test validate_execution_context_data function."""

    def test_valid_context_data(self):
        """Test validation with all valid data."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="python",
            contest_name="contest1",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is True
        assert error is None

    def test_missing_command_type(self):
        """Test validation with missing command type."""
        is_valid, error = validate_execution_context_data(
            command_type="",
            language="python",
            contest_name="contest1",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "コマンド" in error

    def test_missing_language(self):
        """Test validation with missing language."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="",
            contest_name="contest1",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "言語" in error

    def test_missing_contest_name(self):
        """Test validation with missing contest name."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="python",
            contest_name="",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "コンテスト名" in error

    def test_missing_problem_name(self):
        """Test validation with missing problem name."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="python",
            contest_name="contest1",
            problem_name="",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "問題名" in error

    def test_missing_multiple_fields(self):
        """Test validation with multiple missing fields."""
        is_valid, error = validate_execution_context_data(
            command_type="",
            language="",
            contest_name="contest1",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "コマンド" in error
        assert "言語" in error

    def test_empty_env_json(self):
        """Test validation with empty env.json."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="python",
            contest_name="contest1",
            problem_name="problem1",
            env_json={}
        )
        assert is_valid is False
        assert "環境設定ファイル(env.json)が見つかりません" in error

    def test_none_env_json(self):
        """Test validation with None env.json."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="python",
            contest_name="contest1",
            problem_name="problem1",
            env_json=None
        )
        assert is_valid is False
        assert "環境設定ファイル(env.json)が見つかりません" in error

    def test_language_not_in_env_json(self):
        """Test validation with language not in env.json."""
        is_valid, error = validate_execution_context_data(
            command_type="run",
            language="rust",
            contest_name="contest1",
            problem_name="problem1",
            env_json={"python": {"version": "3.9"}}
        )
        assert is_valid is False
        assert "指定された言語 'rust' は環境設定ファイルに存在しません" in error

    def test_all_fields_empty(self):
        """Test validation with all fields empty."""
        is_valid, error = validate_execution_context_data(
            command_type="",
            language="",
            contest_name="",
            problem_name="",
            env_json=None
        )
        assert is_valid is False
        assert "コマンド" in error
        assert "言語" in error
        assert "コンテスト名" in error
        assert "問題名" in error