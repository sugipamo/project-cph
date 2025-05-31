"""
Configuration caching system
"""
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from .exceptions import ConfigurationError


class ConfigCache:
    """Configuration caching with file modification tracking"""
    
    def __init__(self, enable_cache: bool = True, cache_ttl: float = 300.0):
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        self._config_cache: Dict[str, Tuple[Dict[str, Any], float, str]] = {}
        self._file_cache: Dict[str, Tuple[float, str]] = {}  # mtime, hash
    
    def get_cache_key(self, file_path: Union[str, Path], context: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for configuration"""
        file_path = str(file_path)
        
        if context:
            # Include context in cache key
            context_str = str(sorted(context.items()))
            content = f"{file_path}:{context_str}"
        else:
            content = file_path
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _get_file_info(self, file_path: Union[str, Path]) -> Tuple[float, str]:
        """Get file modification time and content hash"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            mtime = file_path.stat().st_mtime
            
            # Calculate content hash for change detection
            with open(file_path, 'rb') as f:
                content = f.read()
                content_hash = hashlib.md5(content).hexdigest()
            
            return mtime, content_hash
        
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read file info for {file_path}: {str(e)}"
            ) from e
    
    def is_file_modified(self, file_path: Union[str, Path]) -> bool:
        """Check if file has been modified since last cache"""
        file_path_str = str(file_path)
        
        if file_path_str not in self._file_cache:
            return True
        
        try:
            current_mtime, current_hash = self._get_file_info(file_path)
            cached_mtime, cached_hash = self._file_cache[file_path_str]
            
            return current_mtime != cached_mtime or current_hash != cached_hash
        
        except Exception:
            # If we can't check, assume modified
            return True
    
    def is_cache_expired(self, cache_time: float) -> bool:
        """Check if cache entry has expired"""
        if not self.enable_cache:
            return True
        
        return time.time() - cache_time > self.cache_ttl
    
    def get_cached_config(self, file_path: Union[str, Path],
                         context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get cached configuration if valid"""
        if not self.enable_cache:
            return None
        
        cache_key = self.get_cache_key(file_path, context)
        
        if cache_key not in self._config_cache:
            return None
        
        config, cache_time, file_hash = self._config_cache[cache_key]
        
        # Check if cache has expired
        if self.is_cache_expired(cache_time):
            self.invalidate_cache_entry(cache_key)
            return None
        
        # Check if file has been modified
        if self.is_file_modified(file_path):
            self.invalidate_cache_entry(cache_key)
            return None
        
        return config
    
    def cache_config(self, file_path: Union[str, Path], config: Dict[str, Any],
                    context: Optional[Dict[str, Any]] = None):
        """Cache configuration"""
        if not self.enable_cache:
            return
        
        cache_key = self.get_cache_key(file_path, context)
        current_time = time.time()
        
        try:
            mtime, content_hash = self._get_file_info(file_path)
            
            # Cache the configuration
            self._config_cache[cache_key] = (config.copy(), current_time, content_hash)
            
            # Cache file info
            self._file_cache[str(file_path)] = (mtime, content_hash)
        
        except Exception:
            # If we can't cache file info, still cache the config
            self._config_cache[cache_key] = (config.copy(), current_time, "")
    
    def invalidate_cache_entry(self, cache_key: str):
        """Invalidate a specific cache entry"""
        if cache_key in self._config_cache:
            del self._config_cache[cache_key]
    
    def invalidate_file_cache(self, file_path: Union[str, Path]):
        """Invalidate all cache entries for a specific file"""
        file_path_str = str(file_path)
        
        # Remove file info cache
        if file_path_str in self._file_cache:
            del self._file_cache[file_path_str]
        
        # Remove related config cache entries
        keys_to_remove = []
        for cache_key in self._config_cache:
            # Check if this cache key is related to the file
            # This is a simplified check - could be more sophisticated
            if file_path_str in cache_key:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._config_cache[key]
    
    def clear_cache(self):
        """Clear all cached configurations"""
        self._config_cache.clear()
        self._file_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = time.time()
        expired_count = 0
        
        for config, cache_time, _ in self._config_cache.values():
            if self.is_cache_expired(cache_time):
                expired_count += 1
        
        return {
            'enabled': self.enable_cache,
            'ttl_seconds': self.cache_ttl,
            'total_entries': len(self._config_cache),
            'expired_entries': expired_count,
            'file_cache_entries': len(self._file_cache),
            'cache_hit_potential': len(self._config_cache) - expired_count
        }
    
    def cleanup_expired_entries(self):
        """Remove expired cache entries"""
        if not self.enable_cache:
            return
        
        keys_to_remove = []
        
        for cache_key, (config, cache_time, file_hash) in self._config_cache.items():
            if self.is_cache_expired(cache_time):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._config_cache[key]
    
    def set_ttl(self, ttl_seconds: float):
        """Set cache time-to-live"""
        self.cache_ttl = ttl_seconds
    
    def enable(self):
        """Enable caching"""
        self.enable_cache = True
    
    def disable(self):
        """Disable caching and clear cache"""
        self.enable_cache = False
        self.clear_cache()
    
    def preload_configs(self, file_paths: list, base_context: Optional[Dict[str, Any]] = None):
        """Preload configurations into cache"""
        from .discovery import ConfigDiscovery
        
        discovery = ConfigDiscovery()
        
        for file_path in file_paths:
            try:
                config = discovery.load_config(file_path)
                self.cache_config(file_path, config, base_context)
            except Exception:
                # Skip files that can't be loaded
                continue


# Global cache instance
default_cache = ConfigCache()