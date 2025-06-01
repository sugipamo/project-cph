"""
Test performance caching system
"""
import pytest
import time
import re
from unittest.mock import patch, mock_open

from src.performance.caching import (
    PatternCache, TemplateCache, ConfigCache,
    cached_pattern, cached_template_processing
)


class TestPatternCache:
    """Test regex pattern caching"""
    
    def test_pattern_cache_basic(self):
        """Test basic pattern caching"""
        cache = PatternCache(max_patterns=10)
        
        pattern1 = cache.get_pattern(r'\d+')
        pattern2 = cache.get_pattern(r'\d+')
        
        # Should return the same compiled pattern
        assert pattern1 is pattern2
        assert pattern1.pattern == r'\d+'
    
    def test_pattern_cache_different_flags(self):
        """Test pattern caching with different flags"""
        cache = PatternCache()
        
        pattern1 = cache.get_pattern(r'test', re.IGNORECASE)
        pattern2 = cache.get_pattern(r'test', 0)
        
        # Should be different patterns due to different flags
        assert pattern1 is not pattern2
        assert pattern1.flags & re.IGNORECASE == re.IGNORECASE
        assert pattern2.flags & re.IGNORECASE == 0
    
    def test_pattern_cache_eviction(self):
        """Test pattern cache eviction"""
        cache = PatternCache(max_patterns=2)
        
        # Fill cache
        pattern1 = cache.get_pattern(r'pattern1')
        pattern2 = cache.get_pattern(r'pattern2')
        
        # Access pattern1 more to make it "more used"
        for _ in range(5):
            cache.get_pattern(r'pattern1')
        
        # Add third pattern, should evict least used
        pattern3 = cache.get_pattern(r'pattern3')
        
        # pattern1 should still be cached, pattern2 might be evicted
        stats = cache.stats()
        assert stats['pattern_count'] <= 2
    
    def test_pattern_cache_stats(self):
        """Test pattern cache statistics"""
        cache = PatternCache(max_patterns=5)
        
        cache.get_pattern(r'test1')
        cache.get_pattern(r'test2')
        cache.get_pattern(r'test1')  # Second access
        
        stats = cache.stats()
        
        assert stats['pattern_count'] == 2
        assert stats['max_patterns'] == 5
        assert stats['total_accesses'] == 3
        assert stats['most_used'] is not None
    
    def test_cached_pattern_function(self):
        """Test global cached_pattern function"""
        pattern1 = cached_pattern(r'\w+')
        pattern2 = cached_pattern(r'\w+')
        
        assert pattern1 is pattern2
        assert pattern1.match('hello') is not None


class TestTemplateCache:
    """Test template processing cache"""
    
    def test_template_cache_basic(self):
        """Test basic template caching"""
        cache = TemplateCache(max_size=10, ttl_seconds=3600)
        
        cache_key = cache.create_cache_key("Hello {name}", {"name": "World"})
        
        # Cache miss
        result = cache.get_cached_result(cache_key)
        assert result is None
        
        # Cache result
        cache.cache_result(cache_key, "Hello World")
        
        # Cache hit
        result = cache.get_cached_result(cache_key)
        assert result == "Hello World"
    
    def test_template_cache_ttl(self):
        """Test template cache TTL expiration"""
        cache = TemplateCache(ttl_seconds=0.1)  # Very short TTL
        
        cache_key = cache.create_cache_key("test", {})
        cache.cache_result(cache_key, "result")
        
        # Should be cached
        assert cache.get_cached_result(cache_key) == "result"
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        assert cache.get_cached_result(cache_key) is None
    
    def test_template_cache_eviction(self):
        """Test template cache eviction"""
        cache = TemplateCache(max_size=2, ttl_seconds=3600)
        
        # Fill cache
        key1 = cache.create_cache_key("template1", {})
        key2 = cache.create_cache_key("template2", {})
        
        cache.cache_result(key1, "result1")
        time.sleep(0.01)  # Small delay to ensure different access times
        cache.cache_result(key2, "result2")
        
        # Access key1 to make it more recent
        cache.get_cached_result(key1)
        
        # Add third item, should evict oldest (key2)
        key3 = cache.create_cache_key("template3", {})
        cache.cache_result(key3, "result3")
        
        # key1 should still be there, key2 might be evicted
        assert cache.get_cached_result(key1) == "result1"
        assert cache.get_cached_result(key3) == "result3"
    
    def test_create_cache_key(self):
        """Test cache key creation"""
        cache = TemplateCache()
        
        key1 = cache.create_cache_key("Hello {name}", {"name": "World"})
        key2 = cache.create_cache_key("Hello {name}", {"name": "World"})
        key3 = cache.create_cache_key("Hello {name}", {"name": "Python"})
        
        # Same template and context should produce same key
        assert key1 == key2
        
        # Different context should produce different key
        assert key1 != key3
    
    def test_template_cache_stats(self):
        """Test template cache statistics"""
        cache = TemplateCache(max_size=5, ttl_seconds=10)
        
        key1 = cache.create_cache_key("test1", {})
        cache.cache_result(key1, "result1")
        
        stats = cache.stats()
        
        assert stats['cache_size'] == 1
        assert stats['max_size'] == 5
        assert stats['ttl_seconds'] == 10
        assert stats['expired_entries'] == 0
    
    def test_cached_template_processing_decorator(self):
        """Test cached template processing decorator"""
        call_count = 0
        
        @cached_template_processing
        def process_template(template, context):
            nonlocal call_count
            call_count += 1
            return template.format(**context)
        
        # First call
        result1 = process_template("Hello {name}", {"name": "World"})
        assert result1 == "Hello World"
        assert call_count == 1
        
        # Second call with same args - should use cache
        result2 = process_template("Hello {name}", {"name": "World"})
        assert result2 == "Hello World"
        assert call_count == 1  # No increase
        
        # Different args - should call function
        result3 = process_template("Hi {name}", {"name": "World"})
        assert result3 == "Hi World"
        assert call_count == 2


class TestConfigCache:
    """Test configuration cache"""
    
    def test_config_cache_basic(self):
        """Test basic configuration caching"""
        cache = ConfigCache(max_size=10)
        
        config_data = {"key": "value", "number": 42}
        
        # Cache miss
        result = cache.get_cached_config("test_key")
        assert result is None
        
        # Cache config
        cache.cache_config("test_key", config_data)
        
        # Cache hit
        result = cache.get_cached_config("test_key")
        assert result == config_data
    
    @patch('os.path.getmtime')
    def test_config_cache_file_tracking(self, mock_getmtime):
        """Test configuration cache with file modification tracking"""
        cache = ConfigCache()
        
        # Mock file modification time
        mock_getmtime.return_value = 1000.0
        
        config_data = {"key": "value"}
        file_paths = ["/path/to/config.json"]
        
        cache.cache_config("test_key", config_data, file_paths)
        
        # Should be cached
        result = cache.get_cached_config("test_key", file_paths)
        assert result == config_data
        
        # Simulate file modification
        mock_getmtime.return_value = 2000.0
        
        # Should return None due to file modification
        result = cache.get_cached_config("test_key", file_paths)
        assert result is None
    
    def test_config_cache_dependencies(self):
        """Test configuration cache dependency tracking"""
        cache = ConfigCache(enable_dependencies=True)
        
        # Cache with dependencies
        cache.cache_config("child", {"data": "child"}, dependencies=["parent"])
        cache.cache_config("parent", {"data": "parent"})
        
        # Both should be cached
        assert cache.get_cached_config("child") is not None
        assert cache.get_cached_config("parent") is not None
        
        # Invalidate parent
        cache.invalidate("parent")
        
        # Child should also be invalidated due to dependency
        assert cache.get_cached_config("child") is None
        assert cache.get_cached_config("parent") is None
    
    def test_config_cache_eviction(self):
        """Test configuration cache LRU eviction"""
        cache = ConfigCache(max_size=2)
        
        # Fill cache
        cache.cache_config("key1", {"data": "1"})
        time.sleep(0.01)
        cache.cache_config("key2", {"data": "2"})
        
        # Access key1 to make it more recent
        cache.get_cached_config("key1")
        
        # Add third item, should evict least recently used
        cache.cache_config("key3", {"data": "3"})
        
        # key1 and key3 should be cached, key2 might be evicted
        assert cache.get_cached_config("key1") is not None
        assert cache.get_cached_config("key3") is not None
    
    def test_config_cache_stats(self):
        """Test configuration cache statistics"""
        cache = ConfigCache(max_size=5, enable_dependencies=True)
        
        # Use __file__ which is the current test file - guaranteed to exist
        cache.cache_config("test", {"data": "test"}, 
                          file_paths=[__file__], 
                          dependencies=["dep1"])
        
        stats = cache.stats()
        
        assert stats['cache_size'] == 1
        assert stats['max_size'] == 5
        assert stats['dependencies_enabled'] is True
        assert stats['tracked_files'] == 1
        assert stats['dependency_count'] == 1