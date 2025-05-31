# Package Structure Documentation

## Overview

This document describes the modernized package structure for the CPH project, including the rationale for changes and migration guidelines.

## New Package Organization

### Core Packages

```
src/
├── core/                    # Core domain abstractions and shared types
├── operations/              # Concrete request implementations  
├── workflow/                # Workflow building and execution
├── environment/             # Environment management (unified env_*)
├── factories/               # All factory patterns (unified)
├── infrastructure/          # External concerns and utilities
└── cli/                     # Command-line interface
```

### Package Responsibilities

#### `src/core/`
- Exception hierarchy and error handling
- Core domain abstractions
- Shared types and interfaces
- Cross-cutting concerns

#### `src/operations/`
- Concrete request implementations (File, Shell, Docker, Python)
- Drivers and execution engines
- Result types and handling
- Composite operations and orchestration

#### `src/workflow/`
- Workflow builders and graph management
- Step definitions and execution
- Dependency resolution
- Request execution graphs

#### `src/environment/`
- Unified environment management (consolidates env_*)
- Execution context handling
- Resource management
- Environment integration

#### `src/factories/`
- All factory patterns in one place
- Request builders and creation logic
- Driver factories
- Unified factory coordination

#### `src/infrastructure/`
- Configuration management system
- Validation services
- Utility functions
- External integrations

#### `src/cli/`
- Command-line interface components
- Input parsing and validation
- User interaction handling

## Import Guidelines

### Public API Access
```python
# Preferred: Use package-level imports
from src.operations import FileRequest, ShellRequest
from src.core import CPHException, ErrorHandler
from src.infrastructure import ConfigurationManager

# Avoid: Deep module imports
from src.operations.file.file_request import FileRequest  # Not recommended
```

### Internal Package Imports
```python
# Within a package, use relative imports
from .base_request import BaseRequest           # ✓ Good
from ..shell.shell_request import ShellRequest # ✓ Good
```

### Cross-Package Dependencies
```python
# Use absolute imports from package root
from src.core.exceptions import CPHException
from src.operations.result import OperationResult
```

## Migration Status

### ✅ Completed
- Added missing `__init__.py` files to all major packages
- Established public APIs for core packages
- Created unified package structure documentation
- Maintained backward compatibility for existing code

### 🔄 In Progress  
- Environment package consolidation (`env_*` → `environment/`)
- Factory pattern unification
- Workflow package organization

### 📋 Planned
- Complete package restructuring with new names
- Import path modernization across entire codebase
- Deprecation of old import patterns

## Benefits Achieved

### 1. **Improved Discoverability**
- Clear package organization makes code easier to navigate
- Public APIs clearly defined in `__init__.py` files
- Logical grouping of related functionality

### 2. **Better Maintainability**
- Reduced coupling between packages
- Clear separation of concerns
- Consistent naming and organization patterns

### 3. **Enhanced Testability**
- Well-defined package boundaries enable better unit testing
- Mock-friendly interfaces and dependency injection
- Clear public/private API boundaries

### 4. **Future Extensibility**
- Modular structure supports adding new operation types
- Plugin-friendly architecture
- Clear extension points defined

## Backward Compatibility

The new structure maintains full backward compatibility with existing code:

```python
# Old imports still work
from src.operations.base_request import BaseRequest
from src.env_core.step.step import Step

# New imports provide cleaner interface
from src.operations import BaseRequest
from src.workflow import Step
```

## Best Practices

### 1. **Package Design Principles**
- High cohesion within packages
- Low coupling between packages  
- Clear dependency direction
- Single responsibility per package

### 2. **Import Conventions**
- Use package-level imports for external consumers
- Use relative imports within packages
- Avoid circular dependencies
- Keep import paths shallow

### 3. **API Design**
- Export only what's intended for public use
- Use `__all__` to control exports
- Provide clear abstraction layers
- Version APIs appropriately

## Troubleshooting

### Common Import Issues

**Problem**: `ImportError: cannot import name 'X' from 'src.package'`
**Solution**: Check if the module is properly exported in `__init__.py`

**Problem**: Circular import errors
**Solution**: Use delayed imports or restructure dependencies

**Problem**: Module not found errors
**Solution**: Ensure all packages have `__init__.py` files

### Migration Guidelines

1. **Start with package-level imports**: Use the new unified imports where possible
2. **Gradually update old imports**: Replace deep imports with package-level ones
3. **Test thoroughly**: Ensure all functionality works with new structure
4. **Update documentation**: Keep import examples current

## Future Enhancements

### Planned Improvements
- **Lazy loading**: Import optimization for large packages
- **Plugin system**: Dynamic package loading for extensions
- **Type hints**: Complete type annotation coverage
- **API versioning**: Structured approach to breaking changes

### Extension Points
- New operation types can be added to `src/operations/`
- Custom workflow builders in `src/workflow/`
- Additional factories in `src/factories/`
- Infrastructure services in `src/infrastructure/`