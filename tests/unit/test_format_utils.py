import pytest
from src.context.utils.format_utils import extract_format_keys, format_with_missing_keys

class TestExtractFormatKeys:
    def test_basic(self):
        s = '/path/{foo}/{bar}.py'
        assert extract_format_keys(s) == ['foo', 'bar']

    def test_no_keys(self):
        s = '/path/foo/bar.py'
        assert extract_format_keys(s) == []

    def test_duplicate_keys(self):
        s = '/path/{foo}/{foo}.py'
        assert extract_format_keys(s) == ['foo', 'foo']

    def test_mixed_keys(self):
        s = '/{a}/{b}_{c}/file_{d}.txt'
        assert extract_format_keys(s) == ['a', 'b', 'c', 'd']

class TestFormatWithMissingKeys:
    def test_all_keys_present(self):
        s = '/path/{foo}/{bar}.py'
        result, missing = format_with_missing_keys(s, foo='A', bar='B')
        assert result == '/path/A/B.py'
        assert missing == []

    def test_some_keys_missing(self):
        s = '/path/{foo}/{bar}.py'
        result, missing = format_with_missing_keys(s, foo='A')
        assert result == '/path/A/{bar}.py'
        assert missing == ['bar']

    def test_no_keys_present(self):
        s = '/path/{foo}/{bar}.py'
        result, missing = format_with_missing_keys(s)
        assert result == '/path/{foo}/{bar}.py'
        assert missing == ['foo', 'bar']

    def test_extra_kwargs(self):
        s = '/path/{foo}/{bar}.py'
        result, missing = format_with_missing_keys(s, foo='A', bar='B', baz='C')
        assert result == '/path/A/B.py'
        assert missing == []

    def test_duplicate_keys(self):
        s = '/{foo}/{foo}.py'
        result, missing = format_with_missing_keys(s, foo='X')
        assert result == '/X/X.py'
        assert missing == [] 