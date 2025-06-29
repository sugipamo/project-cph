# CLAUDE.md Violations Report - 2025-06-29

## Summary
Found multiple violations of CLAUDE.md rules in the src/ directory:

## 1. Default Values in Function Arguments (15 violations)
**Rule violated**: "引数にデフォルト値を指定するのを禁止する"

### Violations found:
- `src/data/docker_image/docker_image_repository.py:173`: `find_unused_images(self, days: int = 30)`
- `src/data/sqlite_state/sqlite_state_repository.py:34`: `get_execution_history(self, limit: int=10)`
- `src/operations/error_codes.py:266`: `classify_error(exception: Exception, context: str = "")`
- `src/data/state/state_repository.py:29`: `get_execution_history(self, limit: int=10)`
- `src/data/docker_container/docker_container_repository.py:156`: `find_unused_containers(self, days: int = 7)`
- `src/operations/interfaces/utility_interfaces.py:41`: `add(..., format_info: Optional[Any] = None, execution_detail: Optional[Any] = None)`
- `src/operations/interfaces/utility_interfaces.py:56`: `flush(self, use_old_format: bool = False)`
- `src/operations/interfaces/utility_interfaces.py:61`: `flatten(self, depth: int = 0)`
- `src/operations/interfaces/infrastructure_interfaces.py:55`: `execute_query(..., params: Optional[Tuple] = None)`
- `src/operations/interfaces/infrastructure_interfaces.py:60`: `execute_command(..., params: Optional[Tuple] = None)`
- `src/presentation/cli_app.py:247`: `main(argv: Optional[list[str]], exit_func, infrastructure, config_manager=None)`
- `src/presentation/string_formatters.py:47`: `is_potential_script_path(..., script_extensions: Optional[list[str]] = None)`
- `src/presentation/docker_command_builder.py:180`: `build_docker_remove_command(..., force: bool = False, volumes: bool = False)`
- `src/domain/services/workflow_execution_service.py:244`: `_execute_main_workflow(..., use_parallel=False, max_workers=4)`
- `src/infrastructure/sqlite_provider.py:154`: `execute(self, sql: str, parameters: Tuple = ())`

## 2. Side Effects Outside Infrastructure Layer (36 violations)
**Rule violated**: "副作用はsrc/infrastructureのみとする"

### Major violations:
- **File I/O operations**:
  - `src/application/sqlite_manager.py:81`: Direct file reading (`f.read()`)
  - `src/application/fast_sqlite_manager.py:123`: Direct file reading (`f.read()`)
  - `src/application/config_manager.py:333`: Direct file reading (`f.read()`)

- **Subprocess operations**:
  - `src/utils/python_utils.py:42`: `subprocess.run()` call
  - `src/utils/python_utils.py:102`: `subprocess.run()` call

- **OS operations**:
  - `src/utils/path_operations.py:113`: `os.path.normpath()`
  - `src/utils/path_operations.py:166`: `os.path.join()`
  - `src/utils/path_operations.py:219`: `os.path.relpath()`

- **JSON operations**:
  - `src/configuration/di_config.py:87`: `json.load(f)`
  - `src/configuration/system_config_repository.py`: Multiple `json.loads()` and `json.dumps()` calls

## 3. Direct Configuration File Editing
**Rule violated**: "設定ファイルの編集はユーザーから明示された場合のみ許可"

### Potential violations:
- `src/configuration/system_config_repository.py:113`: `json.dumps()` operations suggesting configuration manipulation
- Multiple JSON serialization operations in data repositories

## 4. Fallback Processing (Multiple violations)
**Rule violated**: "フォールバック処理は禁止"

### Violations found:
- `src/configuration/system_config_repository.py`: Multiple instances of JSON decode fallback:
  ```python
  except json.JSONDecodeError:
      configs[key] = value  # Fallback to raw value
  ```

- `src/configuration/runtime_config_overlay.py`: 
  ```python
  except (KeyError, TypeError):
      return default_value  # Fallback to default
  ```

- `src/configuration/runtime_config_overlay.py`:
  ```python
  except (KeyError, TypeError):
      return False  # Fallback to False
  ```

- `src/application/execution_requests.py`: Retry logic with fallback behavior

## 5. Short-term Solutions
**Rule violated**: "中長期を見据えた実装を行う"

### Violations found:
- `src/domain/services/workflow_execution_service.py:301`: "# Temporary workaround for TEST steps allow_failure issue"
- `src/presentation/context_formatter.py:211`: "# temporary simple naming"
- `src/presentation/context_formatter.py:218`: "# temporary simple naming"

## Recommendations

1. **Default Parameters**: All default parameter values should be removed and callers should explicitly provide values
2. **Side Effects**: Move all file I/O, subprocess, and OS operations to the infrastructure layer
3. **Fallback Processing**: Remove all try-except blocks that provide fallback values
4. **Temporary Solutions**: Address the temporary workarounds with proper implementations
5. **Configuration**: Ensure all configuration operations go through proper abstractions

## Statistics
- Total Python files in src/: 135
- Functions with default parameters: 15
- Side effects outside infrastructure: 36 instances
- Fallback processing patterns: At least 8 instances
- Temporary/short-term solutions: 3 explicit mentions