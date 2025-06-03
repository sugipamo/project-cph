"""
Format utils のテストケース
"""
import pytest
from src.context.utils.format_utils import (
    extract_format_keys,
    extract_template_keys,
    format_with_missing_keys,
    safe_format_template,
    format_with_context,
    build_path_template,
    validate_template_keys
)


class TestExtractFormatKeys:
    """extract_format_keys関数のテスト"""
    
    def test_extract_format_keys_simple(self):
        """シンプルなキー抽出テスト"""
        result = extract_format_keys("/path/{foo}/{bar}.py")
        assert result == ["foo", "bar"]
    
    def test_extract_format_keys_single_key(self):
        """単一キーの抽出テスト"""
        result = extract_format_keys("/path/{foo}/file.txt")
        assert result == ["foo"]
    
    def test_extract_format_keys_no_keys(self):
        """キーなしの文字列テスト"""
        result = extract_format_keys("/path/to/file.txt")
        assert result == []
    
    def test_extract_format_keys_duplicate(self):
        """重複キーの抽出テスト"""
        result = extract_format_keys("/path/{foo}/{foo}/file.txt")
        assert result == ["foo", "foo"]
    
    def test_extract_format_keys_mixed_content(self):
        """混合コンテンツの抽出テスト"""
        result = extract_format_keys("prefix_{key1}_middle_{key2}_suffix")
        assert result == ["key1", "key2"]
    
    def test_extract_format_keys_empty_string(self):
        """空文字列のテスト"""
        result = extract_format_keys("")
        assert result == []
    
    def test_extract_format_keys_cache(self):
        """LRUキャッシュのテスト"""
        # Same input should hit cache
        template = "/path/{foo}/{bar}.py"
        result1 = extract_format_keys(template)
        result2 = extract_format_keys(template)
        
        assert result1 == result2
        assert result1 == ["foo", "bar"]
    
    def test_extract_template_keys_alias(self):
        """extract_template_keys エイリアスのテスト"""
        result1 = extract_format_keys("/path/{foo}/{bar}.py")
        result2 = extract_template_keys("/path/{foo}/{bar}.py")
        
        assert result1 == result2


class TestFormatWithMissingKeys:
    """format_with_missing_keys関数のテスト"""
    
    def test_format_with_missing_keys_all_provided(self):
        """全キーが提供された場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template, foo="A", bar="B")
        
        assert result == "/path/A/B.py"
        assert missing == []
    
    def test_format_with_missing_keys_partial(self):
        """一部キーが不足している場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template, foo="A")
        
        assert result == "/path/A/{bar}.py"
        assert missing == ["bar"]
    
    def test_format_with_missing_keys_none_provided(self):
        """キーが全く提供されない場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        result, missing = format_with_missing_keys(template)
        
        assert result == "/path/{foo}/{bar}.py"
        assert missing == ["foo", "bar"]
    
    def test_format_with_missing_keys_no_placeholders(self):
        """プレースホルダーがない場合のテスト"""
        template = "/path/to/file.txt"
        result, missing = format_with_missing_keys(template, foo="A")
        
        assert result == "/path/to/file.txt"
        assert missing == []
    
    def test_format_with_missing_keys_extra_kwargs(self):
        """余分なkwargsがある場合のテスト"""
        template = "/path/{foo}.py"
        result, missing = format_with_missing_keys(template, foo="A", bar="B", baz="C")
        
        assert result == "/path/A.py"
        assert missing == []
    
    def test_safe_format_template_alias(self):
        """safe_format_template エイリアスのテスト"""
        template = "/path/{foo}/{bar}.py"
        result1, missing1 = format_with_missing_keys(template, foo="A")
        result2, missing2 = safe_format_template(template, foo="A")
        
        assert result1 == result2
        assert missing1 == missing2


class TestFormatWithContext:
    """format_with_context関数のテスト"""
    
    def test_format_with_context_simple(self):
        """シンプルなコンテキストフォーマットテスト"""
        template = "/path/{contest_name}/{problem_name}.py"
        context = {"contest_name": "abc300", "problem_name": "a"}
        
        result = format_with_context(template, context)
        assert result == "/path/abc300/a.py"
    
    def test_format_with_context_non_string_values(self):
        """非文字列値のコンテキストテスト"""
        template = "number_{num}_boolean_{bool}"
        context = {"num": 123, "bool": True}
        
        result = format_with_context(template, context)
        assert result == "number_123_boolean_True"
    
    def test_format_with_context_missing_keys(self):
        """不足キーがある場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        context = {"foo": "A"}
        
        result = format_with_context(template, context)
        assert result == "/path/A/{bar}.py"
    
    def test_format_with_context_non_string_template(self):
        """非文字列テンプレートのテスト"""
        template = 123
        context = {"foo": "bar"}
        
        result = format_with_context(template, context)
        assert result == 123
    
    def test_format_with_context_empty_context(self):
        """空コンテキストのテスト"""
        template = "/path/{foo}/{bar}.py"
        context = {}
        
        result = format_with_context(template, context)
        assert result == "/path/{foo}/{bar}.py"
    
    def test_format_with_context_fallback_handling(self):
        """フォールバック処理のテスト"""
        template = "/path/{contest_name}/{problem_name}.py"
        context = {"contest_name": "abc300", "problem_name": "a"}
        
        # Normal case should work
        result = format_with_context(template, context)
        assert result == "/path/abc300/a.py"
        
        # Test with complex values that might cause format_map to fail
        template_complex = "/path/{key1}/{key2}.py"
        context_complex = {"key1": "value{with}braces", "key2": "normal"}
        
        result_complex = format_with_context(template_complex, context_complex)
        # Should handle the replacement even with complex values
        assert "value{with}braces" in result_complex
        assert "normal" in result_complex
    
    def test_format_with_context_special_characters(self):
        """特殊文字を含むコンテキストのテスト"""
        template = "/path/{name}/{file}.py"
        context = {"name": "test-name_123", "file": "file@name"}
        
        result = format_with_context(template, context)
        assert result == "/path/test-name_123/file@name.py"


class TestBuildPathTemplate:
    """build_path_template関数のテスト"""
    
    def test_build_path_template_simple(self):
        """シンプルなパステンプレート構築テスト"""
        result = build_path_template("/base", "part1", "part2")
        assert result == "/base/part1/part2"
    
    def test_build_path_template_trailing_slash(self):
        """末尾スラッシュありのベースパステスト"""
        result = build_path_template("/base/", "part1", "part2")
        assert result == "/base/part1/part2"
    
    def test_build_path_template_leading_slash_parts(self):
        """先頭スラッシュありのパーツテスト"""
        result = build_path_template("/base", "/part1", "/part2")
        assert result == "/base/part1/part2"
    
    def test_build_path_template_surrounding_slashes(self):
        """前後スラッシュありのパーツテスト"""
        result = build_path_template("/base/", "/part1/", "/part2/")
        assert result == "/base/part1/part2"
    
    def test_build_path_template_no_parts(self):
        """パーツなしのテスト"""
        result = build_path_template("/base")
        assert result == "/base"
    
    def test_build_path_template_empty_parts(self):
        """空パーツのテスト"""
        result = build_path_template("/base", "", "part2")
        assert result == "/base//part2"
    
    def test_build_path_template_single_part(self):
        """単一パーツのテスト"""
        result = build_path_template("/base", "part1")
        assert result == "/base/part1"


class TestValidateTemplateKeys:
    """validate_template_keys関数のテスト"""
    
    def test_validate_template_keys_all_present(self):
        """必要キーが全て存在する場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        required = ["foo", "bar"]
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is True
        assert missing == []
    
    def test_validate_template_keys_some_missing(self):
        """一部キーが不足している場合のテスト"""
        template = "/path/{foo}.py"
        required = ["foo", "bar", "baz"]
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is False
        assert set(missing) == {"bar", "baz"}
    
    def test_validate_template_keys_no_required(self):
        """必要キーがない場合のテスト"""
        template = "/path/{foo}/{bar}.py"
        required = []
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is True
        assert missing == []
    
    def test_validate_template_keys_no_template_keys(self):
        """テンプレートにキーがない場合のテスト"""
        template = "/path/to/file.py"
        required = ["foo", "bar"]
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is False
        assert set(missing) == {"foo", "bar"}
    
    def test_validate_template_keys_extra_template_keys(self):
        """テンプレートに余分なキーがある場合のテスト"""
        template = "/path/{foo}/{bar}/{baz}.py"
        required = ["foo", "bar"]
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is True
        assert missing == []
    
    def test_validate_template_keys_duplicate_required(self):
        """重複する必要キーのテスト"""
        template = "/path/{foo}/{bar}.py"
        required = ["foo", "bar", "foo"]  # foo is duplicated
        
        valid, missing = validate_template_keys(template, required)
        
        assert valid is True
        assert missing == []


class TestMainExecution:
    """__main__ 実行のテスト"""
    
    def test_main_execution_example(self):
        """main実行時の例のテスト"""
        # This test verifies the example code in __main__ works correctly
        s = '/home/cphelper/project-cph/{contest_template_path}/{language_name}/main.py'
        
        # Test extract_format_keys
        keys = extract_format_keys(s)
        assert keys == ['contest_template_path', 'language_name']
        
        # Test format_with_missing_keys
        result, missing = format_with_missing_keys(s, contest_template_path='abc')
        expected_result = '/home/cphelper/project-cph/abc/{language_name}/main.py'
        expected_missing = ['language_name']
        
        assert result == expected_result
        assert missing == expected_missing


class TestEdgeCases:
    """エッジケースのテスト"""
    
    def test_malformed_brackets(self):
        """不正な括弧のテスト"""
        # Single opening bracket
        result = extract_format_keys("path/{incomplete")
        assert result == []
        
        # Single closing bracket
        result = extract_format_keys("path/incomplete}")
        assert result == []
        
        # Nested brackets - regex will find the inner valid placeholder
        result = extract_format_keys("path/{outer{inner}}")
        assert result == ["inner"]  # The regex actually finds 'inner' as valid
    
    def test_empty_placeholder(self):
        """空プレースホルダーのテスト"""
        result = extract_format_keys("path/{}/file")
        assert result == []
    
    def test_special_characters_in_placeholder(self):
        """プレースホルダー内の特殊文字テスト"""
        # Only word characters are allowed in placeholders
        result = extract_format_keys("path/{key-name}/file")
        assert result == []
        
        result = extract_format_keys("path/{key_name}/file")
        assert result == ["key_name"]
        
        result = extract_format_keys("path/{key123}/file")
        assert result == ["key123"]
    
    def test_unicode_handling(self):
        """Unicode文字の処理テスト"""
        template = "/path/{キー}/{key}.py"
        context = {"key": "value"}
        
        result = format_with_context(template, context)
        assert result == "/path/{キー}/value.py"
    
    def test_very_long_template(self):
        """非常に長いテンプレートのテスト"""
        # Test with a very long template to ensure performance
        long_template = "/".join([f"{{key{i}}}" for i in range(100)])
        keys = extract_format_keys(long_template)
        
        assert len(keys) == 100
        assert keys[0] == "key0"
        assert keys[99] == "key99"