"""step_runnerのテスト

シンプルで読みやすいテストを目指す
"""
import os
import tempfile

import pytest

from src.infrastructure.providers.os_provider import SystemOsProvider
from src.workflow.step.step import StepType
from src.workflow.step.step_runner import (
    ExecutionContext,
    create_step,
    evaluate_test_condition,
    expand_file_patterns_in_text,
    expand_template,
    expand_when_condition,
    run_steps,
)


class TestExecutionContext:
    """ExecutionContextのテスト"""

    def test_to_dict(self):
        """to_dict()が正しく辞書を返すことをテスト"""
        context = ExecutionContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            local_workspace_path="/tmp/workspace",
            contest_current_path="/tmp/current"
        )

        result = context.to_dict()

        assert result['contest_name'] == "abc300"
        assert result['problem_name'] == "a"
        assert result['language'] == "python"
        assert result['local_workspace_path'] == "/tmp/workspace"
        assert result['contest_current_path'] == "/tmp/current"


class TestExpandTemplate:
    """テンプレート展開のテスト"""

    def test_simple_expansion(self):
        """基本的なテンプレート展開"""
        context = ExecutionContext("abc300", "a", "python", "/tmp/ws", "/tmp/current")

        result = expand_template("Hello {contest_name} {problem_name}", context)

        assert result == "Hello abc300 a"

    def test_no_template_variables(self):
        """テンプレート変数がない場合"""
        context = ExecutionContext("abc300", "a", "python", "/tmp/ws", "/tmp/current")

        result = expand_template("Hello world", context)

        assert result == "Hello world"

    def test_empty_template(self):
        """空のテンプレート"""
        context = ExecutionContext("abc300", "a", "python", "/tmp/ws", "/tmp/current")

        result = expand_template("", context)

        assert result == ""


class TestFilePatternExpansion:
    """ファイルパターン展開のテスト"""

    def test_simple_pattern_expansion(self):
        """基本的なパターン展開"""
        file_patterns = {"test_files": ["test/*.in"]}

        result = expand_file_patterns_in_text("Move {test_files}", file_patterns, None)

        assert result == "Move test/*.in"

    def test_directory_extraction_for_movetree(self):
        """movetreeの場合のディレクトリ抽出"""
        file_patterns = {"test_files": ["test/*.in"]}

        result = expand_file_patterns_in_text("Move {test_files}", file_patterns, StepType.MOVETREE)

        assert result == "Move test"

    def test_no_patterns(self):
        """パターンがない場合"""
        result = expand_file_patterns_in_text("Move {test_files}", {}, None)

        assert result == "Move {test_files}"  # 変更されない


class TestEvaluateTestCondition:
    """test条件評価のテスト"""

    def test_directory_exists(self):
        """ディレクトリ存在チェック"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result, error = evaluate_test_condition(f"test -d {tmpdir}", SystemOsProvider())

            assert result is True
            assert error is None

    def test_directory_not_exists(self):
        """ディレクトリ非存在チェック"""
        result, error = evaluate_test_condition("test -d /nonexistent/path", SystemOsProvider())

        assert result is False
        assert error is None

    def test_negation(self):
        """否定条件"""
        result, error = evaluate_test_condition("test ! -d /nonexistent/path", SystemOsProvider())

        assert result is True
        assert error is None

    def test_invalid_format(self):
        """無効なフォーマット"""
        result, error = evaluate_test_condition("invalid command", SystemOsProvider())

        assert result is False
        assert "must start with 'test'" in error


class TestCheckWhenCondition:
    """when条件チェックのテスト"""

    def test_no_when_condition(self):
        """when条件がない場合"""
        context = ExecutionContext("abc300", "a", "python", "/tmp/ws", "/tmp/current")

        result, error = expand_when_condition(None, context, SystemOsProvider())

        assert result is True
        assert error is None

    def test_template_expansion_in_when(self):
        """when条件内のテンプレート展開"""
        with tempfile.TemporaryDirectory() as tmpdir:
            context = ExecutionContext("abc300", "a", "python", tmpdir, "/tmp/current")

            result, error = expand_when_condition("test -d {local_workspace_path}", context, SystemOsProvider())

            assert result is True
            assert error is None

    def test_file_pattern_in_when(self):
        """when条件内のファイルパターン"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test")
            os.makedirs(test_dir)

            context = ExecutionContext(
                "abc300", "a", "python", tmpdir, "/tmp/current",
                file_patterns={"test_data": ["test"]}
            )

            result, error = expand_when_condition("test -d {local_workspace_path}/{test_data}", context, SystemOsProvider())

            assert result is True
            assert error is None


class TestCreateStep:
    """ステップ作成のテスト"""

    def test_simple_step_creation(self):
        """基本的なステップ作成"""
        context = ExecutionContext("abc300", "a", "python", "/tmp/ws", "/tmp/current")
        json_step = {
            "type": "mkdir",
            "cmd": ["{contest_current_path}"],
            "name": "Create directory"
        }

        step = create_step(json_step, context)

        assert step.type == StepType.MKDIR
        assert step.cmd == ["/tmp/current"]
        assert step.name == "Create directory"

    def test_step_with_file_patterns(self):
        """ファイルパターンを含むステップ"""
        context = ExecutionContext(
            "abc300", "a", "python", "/tmp/ws", "/tmp/current",
            file_patterns={"test_files": ["test/*.in"]}
        )
        json_step = {
            "type": "movetree",
            "cmd": ["{local_workspace_path}/{test_files}", "{contest_current_path}/{test_files}"]
        }

        step = create_step(json_step, context)

        assert step.type == StepType.MOVETREE
        assert step.cmd == ["/tmp/ws/test", "/tmp/current/test"]  # ディレクトリ部分のみ


