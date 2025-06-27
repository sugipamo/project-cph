# Dependency Analysis Report

## Summary

The dependency analysis of the `src/` directory has revealed several issues that need attention:

### Key Findings

1. **Circular Imports**: 1 detected
2. **TYPE_CHECKING Delayed Imports**: 4 modules using this pattern
3. **Tight Coupling**: 9 modules with 5 or more dependencies
4. **Local Imports**: 0 files (good - no function-level imports)

## Detailed Issues

### 1. Circular Import

**Location**: `/home/cphelper/project-cph/src/infrastructure/drivers/python/mock_python_driver.py`

**Issue**: Line 4 shows a self-referential import:
```python
from src.infrastructure.drivers.python.mock_python_driver import PythonDriver
```

This module is importing from itself, which is clearly incorrect. It should likely import from a base class or interface module.

### 2. TYPE_CHECKING Delayed Imports

The following modules use `TYPE_CHECKING` to avoid circular imports at runtime:

1. **src.domain.step_runner**
   - Delayed import: `src.domain.step`
   - This suggests a potential circular dependency between step_runner and step modules

2. **src.domain.config_node_logic**
   - Delayed import: `src.domain.config_node_logic` (self-reference!)
   - This is unusual and suggests the module is trying to reference its own types

3. **src.utils.types**
   - Delayed imports: `src.application.output_manager`, `src.utils.format_info`
   - Type definitions depending on application layer violates clean architecture

4. **src.operations.results.result_factory**
   - Delayed import: `src.operations.results.__init__`
   - Suggests circular dependency within the results package

### 3. High Coupling Issues

The most tightly coupled modules are:

1. **src.configuration.di_config**: 26 dependencies
   - This is expected for a dependency injection configuration module
   - However, 26 dependencies is quite high and may indicate the module is doing too much

2. **src.infrastructure.drivers.generic.unified_driver**: 8 dependencies
   - High coupling in infrastructure layer suggests violation of single responsibility

3. **src.presentation.main**: 6 dependencies
   - Main entry point having multiple dependencies is acceptable

4. **src.operations.requests.file_request**: 6 dependencies
   - May benefit from refactoring to reduce dependencies

5. **src.presentation.cli_app**: 5 dependencies
   - CLI module with 5 dependencies is reasonable

## Recommendations

### Immediate Actions Required

1. **Fix the circular import in mock_python_driver.py**
   - Change line 4 to import from the correct base class/interface
   - Likely should be: `from src.infrastructure.drivers.python.python_driver import PythonDriver`

2. **Review TYPE_CHECKING usage**
   - The self-referential import in `config_node_logic.py` needs investigation
   - Consider refactoring to eliminate the need for delayed imports

### Architecture Improvements

1. **Reduce coupling in di_config**
   - Consider splitting into multiple configuration modules by domain
   - Use factory patterns to reduce direct dependencies

2. **Clean Architecture Violations**
   - `src.utils.types` should not depend on application layer
   - Move type definitions to appropriate layers

3. **Package Structure**
   - The circular dependency in `results` package suggests poor internal structure
   - Consider reorganizing the package to have clearer boundaries

## Visual Dependency Graph

A visual dependency graph has been generated at:
- DOT format: `/home/cphelper/project-cph/src_check/dependency_graph.dot`
- PNG image: `/home/cphelper/project-cph/src_check/dependency_graph.png`

The graph uses the following color coding:
- 🔴 Red nodes: Modules with circular imports
- 🟡 Yellow nodes: Modules using TYPE_CHECKING
- 🔵 Blue nodes: Modules with high coupling (>= 5 dependencies)
- 🟠 Orange dashed lines: TYPE_CHECKING delayed imports
- 🔴 Red bold lines: Circular dependencies