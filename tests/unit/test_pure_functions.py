"""
純粋関数のテストケース

pure_functions.pyモジュールの関数をテストして、
純粋関数としての動作（同一入力→同一出力、副作用なし）を確認。
"""
import pytest

# Docker wrapper functions
from src.utils.docker_wrappers import (
    build_docker_build_command_wrapper,
    build_docker_cp_command_wrapper,
    build_docker_inspect_command_wrapper,
    build_docker_ps_command_wrapper,
    build_docker_remove_command_wrapper,
    build_docker_run_command_wrapper,
    build_docker_stop_command_wrapper,
    validate_docker_image_name_wrapper,
)

# String formatting functions
# Additional functions from string_formatters
from src.utils.string_formatters import (
    extract_missing_template_keys,
    format_template_string,
    is_potential_script_path,
    parse_container_names,
    validate_file_path_format,
)


class TestStringFormatting:
    """文字列フォーマット関連の純粋関数テスト"""

    def test_format_template_string_basic(self):
        """基本的な文字列フォーマットのテスト"""
        template = "Hello {name}"
        context = {"name": "World"}
        result = format_template_string(template, context)
        assert result == "Hello World"

    def test_format_template_string_multiple_variables(self):
        """複数変数のフォーマットテスト"""
        template = "{greeting} {name}, today is {day}"
        context = {"greeting": "Hi", "name": "Alice", "day": "Monday"}
        result = format_template_string(template, context)
        assert result == "Hi Alice, today is Monday"

    def test_format_template_string_missing_keys(self):
        """存在しないキーのフォーマットテスト"""
        template = "Hello {missing_key}"
        context = {"name": "World"}
        result = format_template_string(template, context)
        # 存在しないキーはそのまま残る
        assert result == "Hello {missing_key}"

    def test_format_template_string_non_string(self):
        """文字列以外の入力テスト"""
        result = format_template_string(123, {"key": "value"})
        assert result == 123  # 文字列以外はそのまま返される

    def test_extract_missing_template_keys(self):
        """テンプレートから不足キーを抽出するテスト"""
        template = "Hello {name}, your age is {age}"
        available_keys = {"name"}
        missing = extract_missing_template_keys(template, available_keys)
        assert missing == ["age"]


class TestPathValidation:
    """パス検証関連の純粋関数テスト"""

    def test_validate_file_path_format_valid(self):
        """有効なファイルパスのテスト"""
        valid, error = validate_file_path_format("./src/main.py")
        assert valid is True
        assert error is None

    def test_validate_file_path_format_absolute_path(self):
        """絶対パスのテスト"""
        valid, error = validate_file_path_format("/home/user/file.txt")
        assert valid is True
        assert error is None

    def test_validate_file_path_format_relative_path(self):
        """相対パスのテスト"""
        valid, error = validate_file_path_format("../config/settings.json")
        # Relative paths with .. are rejected as path traversal
        assert valid is False
        assert "path traversal" in error.lower()

    def test_validate_file_path_format_invalid_dangerous_chars(self):
        """危険な文字を含むパスのテスト"""
        valid, error = validate_file_path_format("path|dangerous")
        assert not valid
        assert "dangerous characters" in error


class TestPureFunctionProperties:
    """純粋関数の性質テスト"""

    def test_pure_function_deterministic(self):
        """純粋関数は決定的である（同じ入力→同じ出力）"""
        template = "Hello {name}"
        context = {"name": "World"}

        # 同じ入力で複数回実行
        result1 = format_template_string(template, context)
        result2 = format_template_string(template, context)
        result3 = format_template_string(template, context)

        # 結果はすべて同じ
        assert result1 == result2 == result3 == "Hello World"

    def test_pure_function_no_side_effects(self):
        """純粋関数は副作用がない（入力を変更しない）"""
        original_context = {"name": "Alice", "age": "25"}
        context_copy = original_context.copy()

        format_template_string("Hello {name}", context_copy)

        # 元の辞書は変更されていない
        assert context_copy == original_context

    def test_pure_function_composability(self):
        """純粋関数は合成可能である"""
        # 複数の純粋関数を組み合わせて新しい機能を作る
        def complex_format(template, context):
            # まず基本的なフォーマットを実行
            formatted = format_template_string(template, context)
            # さらに別の変換を適用
            return formatted.upper()

        result = complex_format("Hello {name}", {"name": "world"})
        assert result == "HELLO WORLD"
