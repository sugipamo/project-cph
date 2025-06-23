# Clean Architecture Violations Analysis

## Summary

This analysis examines all files that import `src.configuration.config_manager` to identify clean architecture violations, specifically focusing on lower layers (infrastructure and context) depending on higher layers (configuration).

## Architecture Layer Analysis

Based on the project structure, the architectural layers are:

1. **Infrastructure Layer** (lowest): `src/infrastructure/` - Technical concerns, drivers, persistence
2. **Context Layer**: `src/context/` - User input parsing, context management  
3. **Configuration Layer**: `src/configuration/` - Application configuration management
4. **Operations Layer**: `src/operations/` - Business logic and domain operations
5. **Workflow Layer** (highest): `src/workflow/` - Application workflows

## Files Importing config_manager

The following files import `src.configuration.config_manager`:

### Infrastructure Layer Files (VIOLATIONS)

1. **`/home/cphelper/project-cph/src/infrastructure/config/di_config.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Contains factory functions that create config manager instances
   - **Issue**: The infrastructure layer should not depend on higher-level configuration logic
   - **Impact**: HIGH - This is a core dependency injection configuration file

2. **`/home/cphelper/project-cph/src/infrastructure/environment/environment_manager.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for environment configuration
   - **Issue**: Infrastructure should receive configuration, not manage it
   - **Impact**: MEDIUM - Environment management should be configured from above

3. **`/home/cphelper/project-cph/src/infrastructure/drivers/python/python_driver.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for Python execution configuration
   - **Issue**: Drivers should be configured externally, not manage configuration internally
   - **Impact**: MEDIUM - Driver-level configuration dependency

4. **`/home/cphelper/project-cph/src/infrastructure/drivers/unified/unified_driver.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for unified driver configuration
   - **Issue**: Unified driver should receive configuration, not manage it
   - **Impact**: MEDIUM - Central driver configuration dependency

5. **`/home/cphelper/project-cph/src/infrastructure/drivers/filesystem/local_filesystem.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for filesystem configuration
   - **Issue**: Filesystem operations should be configured externally
   - **Impact**: LOW - Limited configuration usage

6. **`/home/cphelper/project-cph/src/infrastructure/drivers/filesystem/path_operations.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for path operation configuration
   - **Issue**: Path operations should receive configuration, not manage it
   - **Impact**: LOW - Utility-level configuration dependency

7. **`/home/cphelper/project-cph/src/infrastructure/drivers/python/utils/python_utils.py`**
   - **Violation**: Infrastructure layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for Python utility configuration
   - **Issue**: Utilities should be configured externally
   - **Impact**: LOW - Utility-level configuration dependency

### Context Layer Files (VIOLATIONS)

8. **`/home/cphelper/project-cph/src/context/user_input_parser/user_input_parser.py`**
   - **Violation**: Context layer importing configuration layer
   - **Analysis**: Uses `TypeSafeConfigNodeManager` for parsing configuration
   - **Issue**: Context layer should receive configuration, not manage it directly
   - **Impact**: HIGH - Core user input parsing functionality

9. **`/home/cphelper/project-cph/src/context/formatters/context_formatter.py`**
   - **Violation**: Context layer importing configuration layer
   - **Analysis**: Uses `TypedExecutionConfiguration` for formatting
   - **Issue**: Formatters should receive data, not manage configuration
   - **Impact**: MEDIUM - Formatting logic with configuration dependency

10. **`/home/cphelper/project-cph/src/context/user_input_parser/user_input_parser_integration.py`**
    - **Violation**: Context layer importing configuration layer
    - **Analysis**: Direct integration with configuration management system
    - **Issue**: Integration layer creates tight coupling to configuration
    - **Impact**: MEDIUM - Integration-specific configuration handling

## Violation Details

### Critical Issues

#### 1. Dependency Injection Configuration (`di_config.py`)
```python
from src.configuration.config_manager import TypeSafeConfigNodeManager
```
- **Problem**: The DI container factory creates config managers directly
- **Solution**: Configuration should be injected from main.py
- **Impact**: This violates the fundamental principle that infrastructure should not create business logic

#### 2. User Input Parser (`user_input_parser.py`)
```python
from src.configuration.config_manager import TypeSafeConfigNodeManager
```
- **Problem**: Parser directly manages configuration instead of receiving it
- **Solution**: Configuration should be injected as a dependency
- **Impact**: Core parsing functionality is tightly coupled to configuration management

### Medium Priority Issues

#### 3. Environment Manager (`environment_manager.py`)
```python
from src.configuration.config_manager import TypeSafeConfigNodeManager
```
- **Problem**: Infrastructure component managing configuration
- **Solution**: Receive configuration through constructor injection
- **Impact**: Environment setup is coupled to configuration management logic

#### 4. Driver Classes
Multiple drivers import configuration manager:
- `python_driver.py`
- `unified_driver.py`
- `local_filesystem.py`
- `path_operations.py`
- `python_utils.py`

**Common Problem**: Drivers should be stateless and receive configuration
**Solution**: Pass configuration through method parameters or constructor

### Low Priority Issues

#### 5. Context Formatters
- `context_formatter.py`
- `user_input_parser_integration.py`

**Problem**: Formatting logic mixed with configuration management
**Solution**: Separate formatting from configuration resolution

## Recommendations

### Immediate Actions (High Priority)

1. **Refactor DI Configuration**
   - Move config manager creation to main.py
   - Inject configuration into infrastructure components
   - Remove direct config_manager imports from di_config.py

2. **Refactor User Input Parser**
   - Inject configuration manager as dependency
   - Remove direct import of config_manager
   - Pass configuration through constructor

### Medium-term Actions

3. **Refactor Infrastructure Drivers**
   - Remove config_manager imports from all drivers
   - Pass configuration through constructor injection
   - Make drivers stateless where possible

4. **Refactor Environment Manager**
   - Receive configuration through dependency injection
   - Remove direct config_manager creation

### Long-term Actions

5. **Establish Clear Boundaries**
   - Define interfaces for configuration access
   - Implement configuration adapters for infrastructure
   - Enforce dependency direction through linting rules

6. **Create Configuration Abstraction**
   - Define configuration interfaces
   - Implement configuration providers
   - Separate configuration data from configuration management

## Compliance with Project Rules

According to `/home/cphelper/project-cph/CLAUDE.md`:

- ✅ "副作用はsrc/infrastructure tests/infrastructure のみとする、また、すべてmain.pyから注入する"
- ❌ Current violations prevent proper dependency injection from main.py
- ✅ "コード変更前に責務の配置が適切であるかを確認" - This analysis addresses responsibility placement

## Conclusion

The project has significant clean architecture violations with **10 files** importing config_manager from lower layers. The most critical violations are in:

1. **Infrastructure DI configuration** - Creates fundamental architecture problems
2. **User input parsing** - Creates tight coupling in core functionality  
3. **Multiple infrastructure drivers** - Violates separation of concerns

These violations should be addressed systematically, starting with the highest impact files and working down to ensure proper dependency flow and maintainability.