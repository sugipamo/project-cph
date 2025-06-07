"""
純粋関数のテストケース

pure_functions.pyモジュールの関数をテストして、
純粋関数としての動作（同一入力→同一出力、副作用なし）を確認。
"""
import pytest
from src.utils.helpers import (
    format_string_pure,
    extract_missing_keys_pure,
    is_potential_script_path_pure,
    validate_file_path_format_pure,
    build_docker_run_command_pure,
    build_docker_build_command_pure,
    build_docker_stop_command_pure,
    build_docker_remove_command_pure,
    build_docker_ps_command_pure,
    build_docker_inspect_command_pure,
    build_docker_cp_command_pure,
    validate_docker_image_name_pure,
    parse_container_names_pure,
    # validate_step_configuration_pure,  # Not available
    # merge_configurations_pure,  # Not available
    # calculate_duration_seconds_pure,  # Not available
    # format_duration_human_readable_pure,  # Not available
    # calculate_success_rate_pure,  # Not available
    # flatten_nested_lists_pure,  # Not available
    # group_by_key_pure,  # Not available
    # filter_by_criteria_pure,  # Not available
    # compose,  # Not available
    # pipe  # Not available
)


class TestStringFormatting:
    """文字列フォーマット関連の純粋関数テスト"""

    def test_format_string_pure_basic(self):
        """基本的な文字列フォーマットのテスト"""
        template = "Hello {name}"
        context = {"name": "World"}
        result = format_string_pure(template, context)
        assert result == "Hello World"

    def test_format_string_pure_multiple_variables(self):
        """複数変数のフォーマットテスト"""
        template = "{greeting} {name}, today is {day}"
        context = {"greeting": "Hi", "name": "Alice", "day": "Monday"}
        result = format_string_pure(template, context)
        assert result == "Hi Alice, today is Monday"

    def test_format_string_pure_missing_keys(self):
        """存在しないキーのフォーマットテスト"""
        template = "Hello {missing_key}"
        context = {"name": "World"}
        result = format_string_pure(template, context)
        # 存在しないキーはそのまま残る
        assert result == "Hello {missing_key}"

    def test_format_string_pure_non_string(self):
        """文字列以外の入力テスト"""
        result = format_string_pure(123, {"key": "value"})
        assert result == 123  # 文字列以外はそのまま返される

    def test_extract_missing_keys_pure(self):
        """テンプレートから不足キーを抽出するテスト"""
        template = "Hello {name}, your age is {age}"
        available_keys = {"name"}
        missing = extract_missing_keys_pure(template, available_keys)
        assert missing == ["age"]


class TestPathValidation:
    """パス検証関連の純粋関数テスト"""

    def test_validate_file_path_format_pure_valid(self):
        """有効なファイルパスのテスト"""
        valid, error = validate_file_path_format_pure("./src/main.py")
        assert valid is True
        assert error is None

    def test_validate_file_path_format_pure_absolute_path(self):
        """絶対パスのテスト"""
        valid, error = validate_file_path_format_pure("/home/user/file.txt")
        assert valid is True
        assert error is None

    def test_validate_file_path_format_pure_relative_path(self):
        """相対パスのテスト"""
        valid, error = validate_file_path_format_pure("../config/settings.json")
        # Relative paths with .. are rejected as path traversal
        assert valid is False
        assert "path traversal" in error.lower()

    def test_validate_file_path_format_pure_invalid_dangerous_chars(self):
        """危険な文字を含むパスのテスト"""
        valid, error = validate_file_path_format_pure("path|dangerous")
        assert not valid
        assert "dangerous characters" in error


class TestPureFunctionProperties:
    """純粋関数の性質テスト"""

    def test_pure_function_deterministic(self):
        """純粋関数は決定的である（同じ入力→同じ出力）"""
        template = "Hello {name}"
        context = {"name": "World"}
        
        # 同じ入力で複数回実行
        result1 = format_string_pure(template, context)
        result2 = format_string_pure(template, context)
        result3 = format_string_pure(template, context)
        
        # 結果はすべて同じ
        assert result1 == result2 == result3 == "Hello World"

    def test_pure_function_no_side_effects(self):
        """純粋関数は副作用がない（入力を変更しない）"""
        original_context = {"name": "Alice", "age": "25"}
        context_copy = original_context.copy()
        
        format_string_pure("Hello {name}", context_copy)
        
        # 元の辞書は変更されていない
        assert context_copy == original_context

    def test_pure_function_composability(self):
        """純粋関数は合成可能である"""
        # 複数の純粋関数を組み合わせて新しい機能を作る
        def complex_format(template, context):
            # まず基本的なフォーマットを実行
            formatted = format_string_pure(template, context)
            # さらに別の変換を適用
            return formatted.upper()
        
        result = complex_format("Hello {name}", {"name": "world"})
        assert result == "HELLO WORLD"