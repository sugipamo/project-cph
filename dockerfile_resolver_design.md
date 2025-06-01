# Dockerfile Path Resolver Design

## Overview
This design delays Dockerfile reading until fitting time while maintaining the current hash-based naming system and full backward compatibility.

## Key Components

### 1. DockerfileResolver Class
```python
class DockerfileResolver:
    """Resolves Dockerfile paths and provides lazy content loading"""
    
    def __init__(self, dockerfile_path: Optional[str] = None, oj_dockerfile_path: Optional[str] = None, loader_func: Callable = None):
        self.dockerfile_path = dockerfile_path
        self.oj_dockerfile_path = oj_dockerfile_path
        self.loader_func = loader_func
        self._dockerfile_content_cache = None
        self._oj_dockerfile_content_cache = None
    
    def get_dockerfile_content(self) -> Optional[str]:
        """Lazy load and cache Dockerfile content"""
        if self._dockerfile_content_cache is None and self.dockerfile_path:
            self._dockerfile_content_cache = self.loader_func(self.dockerfile_path)
        return self._dockerfile_content_cache
    
    def get_oj_dockerfile_content(self) -> Optional[str]:
        """Lazy load and cache OJ Dockerfile content"""
        if self._oj_dockerfile_content_cache is None and self.oj_dockerfile_path:
            self._oj_dockerfile_content_cache = self.loader_func(self.oj_dockerfile_path)
        return self._oj_dockerfile_content_cache
    
    def get_docker_names(self, language: str) -> dict:
        """Generate Docker names using lazy-loaded content"""
        dockerfile_content = self.get_dockerfile_content()
        oj_dockerfile_content = self.get_oj_dockerfile_content()
        
        return {
            "image_name": get_docker_image_name(language, dockerfile_content),
            "container_name": get_docker_container_name(language, dockerfile_content),
            "oj_image_name": get_oj_image_name(oj_dockerfile_content),
            "oj_container_name": get_oj_container_name(oj_dockerfile_content)
        }
```

### 2. Modified ExecutionContext
```python
class ExecutionContext:
    def __init__(self, ...):
        # Store resolver instead of content
        self._dockerfile_resolver = None
    
    @property
    def dockerfile_resolver(self):
        return self._dockerfile_resolver
    
    @dockerfile_resolver.setter 
    def dockerfile_resolver(self, value):
        self._dockerfile_resolver = value
    
    # Backward compatibility properties
    @property
    def dockerfile(self):
        """Backward compatibility: lazy load dockerfile content"""
        if self._dockerfile_resolver:
            return self._dockerfile_resolver.get_dockerfile_content()
        return None
    
    @dockerfile.setter
    def dockerfile(self, value):
        """Backward compatibility: create resolver from content"""
        if value is not None:
            # Create resolver with pre-loaded content for compatibility
            self._dockerfile_resolver = DockerfileResolver()
            self._dockerfile_resolver._dockerfile_content_cache = value
    
    @property 
    def oj_dockerfile(self):
        """Backward compatibility: lazy load OJ dockerfile content"""
        if self._dockerfile_resolver:
            return self._dockerfile_resolver.get_oj_dockerfile_content()
        return None
    
    @oj_dockerfile.setter
    def oj_dockerfile(self, value):
        """Backward compatibility: update resolver with content"""
        if not self._dockerfile_resolver:
            self._dockerfile_resolver = DockerfileResolver()
        self._dockerfile_resolver._oj_dockerfile_content_cache = value
    
    def get_docker_names(self) -> dict:
        """Generate Docker names using resolver"""
        if self._dockerfile_resolver:
            return self._dockerfile_resolver.get_docker_names(self.language)
        
        # Fallback for cases without resolver
        return {
            "image_name": get_docker_image_name(self.language),
            "container_name": get_docker_container_name(self.language),
            "oj_image_name": get_oj_image_name(),
            "oj_container_name": get_oj_container_name()
        }
```

### 3. Modified User Input Parser
```python
def _apply_dockerfile(context, dockerfile_loader):
    """Store Dockerfile PATH in context resolver (not content)"""
    dockerfile_path = None
    if context.env_json and context.language and context.env_type:
        env_types = context.env_json[context.language].get("env_types", {})
        env_type_conf = env_types.get(context.env_type, {})
        dockerfile_path = env_type_conf.get("dockerfile_path")
    
    # Create resolver with path (content loaded lazily)
    context.dockerfile_resolver = DockerfileResolver(
        dockerfile_path=dockerfile_path,
        loader_func=dockerfile_loader
    )
    return context

def _apply_oj_dockerfile(context):
    """Store OJ Dockerfile PATH in context resolver"""
    oj_dockerfile_path = os.path.join(os.path.dirname(__file__), "oj.Dockerfile")
    
    if not context.dockerfile_resolver:
        context.dockerfile_resolver = DockerfileResolver()
    
    context.dockerfile_resolver.oj_dockerfile_path = oj_dockerfile_path
    return context
```

## Migration Strategy

### Phase 1: Add Resolver Support (Non-Breaking)
1. Add `DockerfileResolver` class
2. Add `dockerfile_resolver` property to `ExecutionContext`
3. Maintain backward compatibility with existing `dockerfile`/`oj_dockerfile` properties
4. Update `user_input_parser.py` to create resolvers but still load content immediately

### Phase 2: Update Fitting Components (Non-Breaking)
1. Update `PreparationExecutor` to trigger content loading during fitting
2. Update `PureRequestFactory` to trigger content loading when needed
3. Ensure all docker name generation happens through the resolver

### Phase 3: Switch to Lazy Loading (Breaking for Internal APIs)
1. Modify `user_input_parser.py` to store paths only
2. Content loading now happens on first access during fitting
3. All external APIs remain compatible

## Benefits

1. **Architectural Consistency**: Follows resolver pattern used elsewhere
2. **Lazy Loading**: Dockerfile content only read when actually needed
3. **Backward Compatibility**: All existing APIs continue to work
4. **Caching**: Content is cached after first load
5. **Testability**: Easy to mock resolver for testing
6. **Performance**: Avoids unnecessary file I/O during initialization

## Testing Strategy

1. **Unit Tests**: Test resolver independently
2. **Integration Tests**: Verify backward compatibility of all APIs
3. **Performance Tests**: Measure initialization time improvement
4. **Fitting Tests**: Ensure docker names are available during fitting

## Implementation Priority

1. High: Maintain backward compatibility
2. High: Ensure fitting functionality works correctly  
3. Medium: Performance improvements
4. Low: Internal API cleanup