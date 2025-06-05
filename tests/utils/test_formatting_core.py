"""
統合フォーマット処理ライブラリのテスト

既存の3つのフォーマット実装から統合されたライブラリの動作を検証
"""
import pytest
from typing import Dict, List, Tuple

from src.utils.formatting.core import (
    FormattingCore,
    FormatOperationResult,
    extract_format_keys,
    extract_template_keys,
    format_with_missing_keys,
    safe_format_template
)


class TestFormattingCore:
    """FormattingCoreクラスの基本機能テスト"""
    
    def test_extract_template_keys_simple(self):
        """基本的なテンプレートキー抽出"""
        result = FormattingCore.extract_template_keys("Hello {name}!")
        assert result == ["name"]
    
    def test_extract_template_keys_multiple(self):
        """複数キーの抽出"""
        result = FormattingCore.extract_template_keys("/path/{foo}/{bar}.py")
        assert result == ["foo", "bar"]
    
    def test_extract_template_keys_empty(self):
        """キーなしテンプレート"""
        result = FormattingCore.extract_template_keys("Hello World!")
        assert result == []
    
    def test_extract_template_keys_strict_success(self):
        """詳細モード（成功）でのキー抽出"""
        result = FormattingCore.extract_template_keys("Hello {name}!", strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert len(result.errors) == 0
        assert result.metadata["keys_found"] == 1
    
    def test_extract_template_keys_strict_failure(self):
        """詳細モード（失敗）でのキー抽出"""
        result = FormattingCore.extract_template_keys("", strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is False
        assert "Template must be a non-empty string" in result.errors
    
    def test_extract_template_keys_advanced_format(self):
        """高度なフォーマット指定子の処理"""
        result = FormattingCore.extract_template_keys(
            "{name:>10} {value:.2f}", 
            advanced=True, 
            strict=False
        )
        assert result == ["name", "value"]
    
    def test_extract_template_keys_invalid_names(self):
        """無効なキー名の処理"""
        # 数字で始まるキー名は無効
        result = FormattingCore.extract_template_keys(
            "{1invalid} {valid_name}", 
            strict=True
        )
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert len(result.warnings) > 0
        # valid_nameのみが抽出される
    
    def test_safe_format_simple(self):
        """基本的な安全フォーマット"""
        result, missing = FormattingCore.safe_format(
            "Hello {name}!", 
            {"name": "World"}, 
            strict=False
        )
        assert result == "Hello World!"
        assert missing == []
    
    def test_safe_format_missing_keys(self):
        """欠損キーありのフォーマット"""
        result, missing = FormattingCore.safe_format(
            "Hello {name}! Age: {age}", 
            {"name": "World"}, 
            strict=False
        )
        assert result == "Hello World! Age: {age}"
        assert missing == ["age"]
    
    def test_safe_format_strict_success(self):
        """詳細モード（成功）での安全フォーマット"""
        result = FormattingCore.safe_format(
            "Hello {name}!", 
            {"name": "World"}, 
            strict=True
        )
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert result.result == "Hello World!"
        assert result.missing_keys == []
    
    def test_safe_format_strict_missing_not_allowed(self):
        """詳細モード（欠損キー不許可）"""
        result = FormattingCore.safe_format(
            "Hello {name}! Age: {age}", 
            {"name": "World"}, 
            strict=True,
            allow_missing=False
        )
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is False
        assert "Missing required keys" in result.errors[0]
        assert "age" in result.missing_keys
    
    def test_safe_format_type_conversion(self):
        """型変換の処理"""
        result = FormattingCore.safe_format(
            "Value: {value}, None: {none_val}", 
            {"value": 123, "none_val": None}, 
            strict=True
        )
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert "Value: 123, None: " in result.result
        assert len(result.warnings) > 0  # None値変換の警告
    
    def test_safe_format_invalid_template(self):
        """無効なテンプレートの処理"""
        with pytest.raises(ValueError, match="Template must be a string"):
            FormattingCore.safe_format(None, {}, strict=False)
    
    def test_safe_format_invalid_dict(self):
        """無効な辞書の処理"""
        with pytest.raises(ValueError, match="Format dictionary must be a dict"):
            FormattingCore.safe_format("Hello {name}!", "not_a_dict", strict=False)
    
    def test_validate_template_valid(self):
        """有効なテンプレートの検証"""
        result = FormattingCore.validate_template("Hello {name}!")
        assert result is True
    
    def test_validate_template_invalid_braces(self):
        """括弧不整合のテンプレート検証"""
        result = FormattingCore.validate_template("Hello {name!", strict=False)
        assert result is False
    
    def test_validate_template_strict_valid(self):
        """詳細モード（有効）での検証"""
        result = FormattingCore.validate_template("Hello {name}!", strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert result.result == "True"
    
    def test_validate_template_strict_invalid(self):
        """詳細モード（無効）での検証"""
        result = FormattingCore.validate_template("Hello {name!", strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_merge_format_dicts_simple(self):
        """基本的な辞書マージ"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        
        result = FormattingCore.merge_format_dicts(dict1, dict2, strict=False)
        
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert result == expected
    
    def test_merge_format_dicts_conflicts(self):
        """競合ありの辞書マージ"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 20, "c": 3}
        
        result = FormattingCore.merge_format_dicts(dict1, dict2, strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        assert len(result.warnings) > 0  # 競合の警告
        assert "Overwriting key 'b'" in result.warnings[0]
    
    def test_merge_format_dicts_empty(self):
        """空辞書のマージ"""
        result = FormattingCore.merge_format_dicts(strict=False)
        assert result == {}
    
    def test_merge_format_dicts_invalid_input(self):
        """無効な入力での辞書マージ"""
        with pytest.raises(ValueError, match="Failed to merge dictionaries"):
            FormattingCore.merge_format_dicts({"a": 1}, "not_a_dict", strict=False)


class TestCompatibilityFunctions:
    """互換性関数のテスト"""
    
    def test_extract_format_keys_compatibility(self):
        """extract_format_keys互換性"""
        result = extract_format_keys("Hello {name}!")
        assert result == ["name"]
    
    def test_extract_template_keys_compatibility(self):
        """extract_template_keys互換性"""
        result = extract_template_keys("/path/{foo}/{bar}.py")
        assert result == ["foo", "bar"]
    
    def test_format_with_missing_keys_compatibility(self):
        """format_with_missing_keys互換性"""
        result, missing = format_with_missing_keys("Hello {name}! Age: {age}", name="World")
        
        assert result == "Hello World! Age: {age}"
        assert missing == ["age"]
    
    def test_safe_format_template_compatibility(self):
        """safe_format_template互換性"""
        result, missing = safe_format_template("Hello {name}!", name="World")
        
        assert result == "Hello World!"
        assert missing == []


class TestEdgeCases:
    """エッジケースのテスト"""
    
    def test_unicode_templates(self):
        """Unicode文字を含むテンプレート"""
        result, missing = FormattingCore.safe_format(
            "こんにちは {名前}さん！", 
            {"名前": "世界"}, 
            strict=False
        )
        assert result == "こんにちは 世界さん！"
        assert missing == []
    
    def test_very_long_template(self):
        """非常に長いテンプレート"""
        long_template = "Hello " + "{name}" * 1000 + "!"
        keys = FormattingCore.extract_template_keys(long_template, strict=False)
        assert len(keys) == 1000
        assert all(key == "name" for key in keys)
    
    def test_complex_format_strings(self):
        """複雑なフォーマット文字列"""
        template = "{name:>10} {value:.2f} {percent:>6.1%}"
        result = FormattingCore.extract_template_keys(template, advanced=True, strict=False)
        assert result == ["name", "value", "percent"]
    
    def test_nested_braces(self):
        """ネストした括弧（実際には有効な構文）"""
        result = FormattingCore.validate_template("Hello {{name}}", strict=False)
        # {{}} は有効なエスケープ文字なので True になる
        assert result is True
    
    def test_empty_keys(self):
        """空のキー"""
        result = FormattingCore.extract_template_keys("Hello {}!", strict=True)
        
        assert isinstance(result, FormatOperationResult)
        assert result.success is True
        # 空のキーは正規表現で抽出されないため、キー数が0になる
        assert result.metadata["keys_found"] == 0
    
    def test_special_characters_in_values(self):
        """値に特殊文字を含む場合"""
        result, missing = FormattingCore.safe_format(
            "Message: {msg}", 
            {"msg": "Hello\nWorld\t{test}"}, 
            strict=False
        )
        assert result == "Message: Hello\nWorld\t{test}"
        assert missing == []
    
    def test_large_format_dict(self):
        """大きなフォーマット辞書"""
        large_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        template = "First: {key_0}, Last: {key_999}"
        
        result, missing = FormattingCore.safe_format(template, large_dict, strict=False)
        assert result == "First: value_0, Last: value_999"
        assert missing == []


class TestPerformance:
    """パフォーマンステスト"""
    
    def test_caching_effectiveness(self):
        """キャッシングの効果"""
        template = "Hello {name}! Welcome to {place}!"
        
        # 同じテンプレートを複数回処理
        for _ in range(10):
            keys = FormattingCore.extract_template_keys(template, strict=False)
            assert keys == ["name", "place"]
        
        # キャッシュヒットにより高速になることを期待
        # （実際の時間測定は省略、機能テストのみ）
    
    def test_regex_pattern_reuse(self):
        """正規表現パターンの再利用"""
        templates = [
            "Hello {name}!",
            "Age: {age}",
            "Location: {city}, {country}"
        ]
        
        for template in templates:
            keys = FormattingCore.extract_template_keys(template, strict=False)
            assert isinstance(keys, list)


if __name__ == "__main__":
    pytest.main([__file__])