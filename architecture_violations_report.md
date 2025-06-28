# CPH Project Architecture Violations Report

## Summary

This report identifies key architectural issues and violations of the CLAUDE.md rules in the CPH project.

## 1. Circular Dependencies and Delayed Imports

### Identified Delayed Imports (Potential Circular Dependency Workarounds)

1. **src/configuration/di_config.py** (Line 230-233)
   - Imports application and operations modules inside `_create_request_creator` function
   - This is a clear workaround for circular dependencies between configuration and application layers

2. **src/domain/step_runner.py** (Line 364)
   - Imports `src.configuration.config_resolver` inside `create_step` function
   - Domain should not depend on configuration layer

3. **src/infrastructure/drivers/generic/persistence_driver.py** (Line 117)
   - Imports `src.infrastructure.sqlite_provider` inside `_initialize_database` function
   - Infrastructure importing other infrastructure modules via delayed imports

4. **src/presentation/user_input_parser.py** (Line 422)
   - Imports `src.infrastructure.docker_naming_provider` inside function
   - Presentation layer should receive infrastructure dependencies via injection

## 2. Clean Architecture Violations

### Domain Layer Violations

1. **src/domain/workflow_logger_adapter.py** (Line 5)
   ```python
   from src.infrastructure.di_container import DIContainer
   ```
   - Domain layer directly imports infrastructure
   - Violates clean architecture principle

2. **src/domain/services/workflow_execution_service.py**
   - While it doesn't directly import infrastructure, it receives and uses infrastructure container
   - Contains comments about "互換性維持" (compatibility maintenance) suggesting awareness of violations

### Application Layer Violations

Multiple files in application layer import infrastructure directly:

1. **src/application/execution_requests.py** (Lines 6-10)
   ```python
   from src.infrastructure.json_provider import JsonProvider
   from src.infrastructure.os_provider import OsProvider
   from src.infrastructure.registry_provider import SystemRegistryProvider
   from src.infrastructure.requests.file.file_op_type import FileOpType
   from src.infrastructure.time_provider import TimeProvider
   ```

2. **src/application/config_manager.py**
3. **src/application/contest_manager.py**
4. **src/application/fast_sqlite_manager.py**
5. **src/application/sqlite_manager.py**
6. **src/application/pure_config_manager.py**
7. **src/application/mock_output_manager.py**
8. **src/application/services/debug_service.py**
9. **src/application/services/config_loader_service.py**

## 3. Default Value Usage Violations

### Found Default Parameter Values in src/

1. **src/domain/services/workflow_execution_service.py** (Line 244)
   ```python
   def _execute_main_workflow(self, operations_composite, use_parallel=False, max_workers=4):
   ```

2. **src/domain/workflow_logger_adapter.py**
   - Line 90: `def step_success(self, step_name: str, message: str='') -> None:`
   - Line 100: `def step_failure(self, step_name: str, error: str, allow_failure: bool=False) -> None:`
   - Line 118: `def log_workflow_start(self, step_count: int, parallel: bool=False) -> None:`

3. **src/domain/composite_step_failure.py**
   ```python
   def __init__(self, message: str, result: Optional[Any]=None, original_exception: Optional[Exception]=None, error_code: Optional[ErrorCode]=None, context: str=''):
   ```

4. **src/application/execution_results.py**
   ```python
   def __init__(self, stdout: Optional[str] = None, stderr: Optional[str] = None,
   ```

## 4. Fallback Processing Violations

### src/domain/step_runner.py (Lines 374-387)
```python
# フォールバック用のデフォルト値（設定が取得できない場合）
fallback_defaults = {
    'name': None,
    'allow_failure': False,
    'show_output': True,
    'max_workers': 1,
    'cwd': None,
    'when': None,
    'output_format': None,
    'format_preset': None,
    'force_env_type': None,
    'format_options': None,
    'auto_generated': False
}
```
- Explicit fallback values defined despite CLAUDE.md prohibition
- Comment acknowledges it's for "when configuration cannot be obtained"

## 5. Short-term Fixes and Technical Debt

### Evidence of Short-term Solutions

1. **Compatibility Maintenance Comments (互換性維持)**
   - Multiple files contain "互換性維持" comments indicating temporary compatibility fixes
   - Examples in workflow_execution_service.py suggest awareness of architectural violations

2. **Delayed Import Pattern**
   - Used extensively to avoid circular dependencies
   - Shows tight coupling between layers that should be independent

3. **Configuration Management Issues**
   - Multiple config managers and loaders suggest confusion in configuration responsibility
   - Default values hardcoded despite prohibition

## 6. Key Patterns Indicating Technical Debt

1. **Circular dependency avoidance through delayed imports**
   - Shows fundamental architectural coupling issues

2. **Direct infrastructure imports in domain and application layers**
   - Violates dependency inversion principle
   - Makes testing and maintenance difficult

3. **Fallback processing despite explicit prohibition**
   - Risk of hiding configuration errors
   - Goes against fail-fast principle

4. **Default parameter values throughout codebase**
   - Makes it unclear what values are actually being used
   - Violates explicit configuration requirement

## Recommendations

1. **Refactor to proper dependency injection**
   - Remove all direct infrastructure imports from domain and application layers
   - Pass dependencies through constructors or interfaces

2. **Eliminate delayed imports**
   - Restructure modules to avoid circular dependencies
   - Consider using interfaces/protocols for loose coupling

3. **Remove all default values and fallback processing**
   - Force explicit configuration at all call sites
   - Fail fast when configuration is missing

4. **Separate concerns properly**
   - Domain should only contain business logic
   - Application should orchestrate domain and infrastructure
   - Infrastructure should handle all external dependencies

5. **Address technical debt systematically**
   - Don't use "互換性維持" as excuse for violations
   - Plan proper refactoring instead of quick fixes