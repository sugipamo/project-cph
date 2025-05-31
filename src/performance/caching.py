"""
Performance-oriented caching implementations
"""
import re
import time
import threading
from typing import Dict, Any, Optional, Pattern, Tuple, Callable
from functools import lru_cache, wraps


class PatternCache:
    """High-performance regex pattern cache"""
    
    def __init__(self, max_patterns: int = 1000):
        self._cache: Dict[str, Pattern] = {}
        self._max_patterns = max_patterns
        self._access_count: Dict[str, int] = {}
        self._lock = threading.RLock()
    
    def get_pattern(self, pattern_str: str, flags: int = 0) -> Pattern:
        """Get compiled regex pattern with caching"""
        cache_key = f"{pattern_str}:{flags}"
        
        with self._lock:
            if cache_key in self._cache:
                self._access_count[cache_key] = self._access_count.get(cache_key, 0) + 1
                return self._cache[cache_key]
            
            # Compile new pattern
            compiled = re.compile(pattern_str, flags)
            
            # Evict least used patterns if cache is full
            if len(self._cache) >= self._max_patterns:
                self._evict_least_used()
            
            self._cache[cache_key] = compiled
            self._access_count[cache_key] = 1
            
            return compiled
    
    def _evict_least_used(self):
        """Evict 20% of least used patterns"""
        if not self._access_count:
            return
        
        # Sort by access count and remove bottom 20%
        sorted_patterns = sorted(self._access_count.items(), key=lambda x: x[1])
        evict_count = max(1, len(sorted_patterns) // 5)
        
        for pattern_key, _ in sorted_patterns[:evict_count]:
            self._cache.pop(pattern_key, None)
            self._access_count.pop(pattern_key, None)
    
    def clear(self):
        """Clear all cached patterns"""
        with self._lock:
            self._cache.clear()
            self._access_count.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                'pattern_count': len(self._cache),
                'max_patterns': self._max_patterns,
                'total_accesses': sum(self._access_count.values()),
                'most_used': max(self._access_count.items(), key=lambda x: x[1]) if self._access_count else None
            }


class TemplateCache:
    """High-performance template processing cache"""
    
    def __init__(self, max_size: int = 2048, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached template processing result"""
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            result, timestamp = self._cache[cache_key]
            
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                self._cache.pop(cache_key, None)
                self._access_times.pop(cache_key, None)
                return None
            
            self._access_times[cache_key] = time.time()
            return result
    
    def cache_result(self, cache_key: str, result: Any):
        """Cache template processing result"""
        with self._lock:
            # Evict if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            current_time = time.time()
            self._cache[cache_key] = (result, current_time)
            self._access_times[cache_key] = current_time
    
    def _evict_oldest(self):
        """Evict oldest accessed entries"""
        if not self._access_times:
            return
        
        # Remove 20% of oldest entries
        sorted_entries = sorted(self._access_times.items(), key=lambda x: x[1])
        evict_count = max(1, len(sorted_entries) // 5)
        
        for cache_key, _ in sorted_entries[:evict_count]:
            self._cache.pop(cache_key, None)
            self._access_times.pop(cache_key, None)
    
    def create_cache_key(self, template: str, context: Dict[str, Any]) -> str:
        """Create cache key from template and context"""
        # Create a hash-based key for better performance
        import hashlib
        context_str = str(sorted(context.items()))
        content = f"{template}:{context_str}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def clear(self):
        """Clear template cache"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for _, timestamp in self._cache.values()
                if current_time - timestamp > self.ttl_seconds
            )
            
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'expired_entries': expired_count,
                'hit_potential': len(self._cache) - expired_count,
                'ttl_seconds': self.ttl_seconds
            }


class ConfigCache:
    """Enhanced configuration cache with dependency tracking"""
    
    def __init__(self, max_size: int = 1024, enable_dependencies: bool = True):
        self.max_size = max_size
        self.enable_dependencies = enable_dependencies
        self._cache: Dict[str, Tuple[Any, float, float]] = {}  # value, access_time, creation_time
        self._dependencies: Dict[str, set] = {}  # key -> set of dependent keys
        self._file_mtimes: Dict[str, float] = {}  # file_path -> mtime
        self._lock = threading.RLock()
    
    def get_cached_config(self, cache_key: str, file_paths: Optional[list] = None) -> Optional[Any]:
        """Get cached configuration with file modification checking"""
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            # Check file modifications if file paths provided
            if file_paths and not self._files_unchanged(file_paths):
                self.invalidate(cache_key)
                return None
            
            config, _, creation_time = self._cache[cache_key]
            
            # Update access time
            self._cache[cache_key] = (config, time.time(), creation_time)
            
            return config
    
    def cache_config(self, cache_key: str, config: Any, file_paths: Optional[list] = None,
                    dependencies: Optional[list] = None):
        """Cache configuration with file and dependency tracking"""
        with self._lock:
            # Evict if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            current_time = time.time()
            self._cache[cache_key] = (config, current_time, current_time)
            
            # Track file modifications
            if file_paths:
                for file_path in file_paths:
                    try:
                        import os
                        self._file_mtimes[file_path] = os.path.getmtime(file_path)
                    except (OSError, ValueError):
                        continue
            
            # Track dependencies
            if dependencies and self.enable_dependencies:
                self._dependencies[cache_key] = set(dependencies)
    
    def _files_unchanged(self, file_paths: list) -> bool:
        """Check if files have not been modified"""
        try:
            import os
            for file_path in file_paths:
                if file_path not in self._file_mtimes:
                    return False
                
                current_mtime = os.path.getmtime(file_path)
                if current_mtime != self._file_mtimes[file_path]:
                    return False
            
            return True
        except (OSError, ValueError):
            return False
    
    def invalidate(self, cache_key: str):
        """Invalidate cache entry and dependent entries"""
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            # Invalidate dependent entries
            if self.enable_dependencies:
                for key, deps in list(self._dependencies.items()):
                    if cache_key in deps:
                        self.invalidate(key)
            
            # Clean up dependencies
            self._dependencies.pop(cache_key, None)
    
    def _evict_lru(self):
        """Evict least recently used entries"""
        if not self._cache:
            return
        
        # Sort by access time and remove 20%
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1][1]  # access_time
        )
        evict_count = max(1, len(sorted_entries) // 5)
        
        for cache_key, _ in sorted_entries[:evict_count]:
            self.invalidate(cache_key)
    
    def clear(self):
        """Clear all caches"""
        with self._lock:
            self._cache.clear()
            self._dependencies.clear()
            self._file_mtimes.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        with self._lock:
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'dependency_count': len(self._dependencies),
                'tracked_files': len(self._file_mtimes),
                'dependencies_enabled': self.enable_dependencies
            }


# Global cache instances
pattern_cache = PatternCache()
template_cache = TemplateCache()
config_cache = ConfigCache()


def cached_pattern(pattern_str: str, flags: int = 0) -> Pattern:
    """Get cached compiled regex pattern"""
    return pattern_cache.get_pattern(pattern_str, flags)


def cached_template_processing(func: Callable) -> Callable:
    """Decorator for caching template processing results"""
    @wraps(func)
    def wrapper(template: str, context: Dict[str, Any], *args, **kwargs):
        cache_key = template_cache.create_cache_key(template, context)
        
        # Try to get cached result
        cached_result = template_cache.get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Process and cache result
        result = func(template, context, *args, **kwargs)
        template_cache.cache_result(cache_key, result)
        
        return result
    
    return wrapper