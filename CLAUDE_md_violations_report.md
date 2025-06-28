# CLAUDE.md Rule Violations Report

This report documents violations of CLAUDE.md rules found in the src/ directory.

## Summary of Violations

### 1. Default Parameter Values (禁止: 引数にデフォルト値を指定するのを禁止する)

#### src/infrastructure/drivers/generic/execution_driver.py
- **Line 15**: `container: Optional[DIContainer] = None`
- **Lines 61-64**: Multiple default parameters in `execute_shell_command` method:
  ```python
  cwd: Optional[str] = None,
  env: Optional[Dict[str, str]] = None,
  inputdata: Optional[str] = None,
  timeout: Optional[int] = None
  ```

#### src/application/execution_requests.py
- **Lines 32-37**: Multiple default parameters in ShellRequest.__init__:
  ```python
  name: Optional[str] = None,
  timeout: Optional[float] = None,
  environment: Optional[dict] = None,
  shell: Optional[bool] = None,
  retry_config: Optional[dict] = None,
  debug_tag: Optional[str] = None
  ```
- **Lines 138-142**: Multiple default parameters in PythonRequest.__init__

#### src/infrastructure/ast_analyzer.py
- **Line 32**: `filename: str = '<string>'`

### 2. Fallback Processing (禁止: フォールバック処理は禁止)

#### src/infrastructure/drivers/generic/execution_driver.py
- **Lines 37-40**: Using getattr() with default values:
  ```python
  cwd=getattr(request, 'cwd', None),
  env=getattr(request, 'env', None),
  inputdata=getattr(request, 'inputdata', None),
  timeout=getattr(request, 'timeout', None)
  ```
- **Line 45**: `cwd = getattr(request, 'cwd', None)`

#### src/domain/step_runner.py
- **Lines 374-387**: Hardcoded fallback defaults dictionary
- **Lines 392-402**: Multiple uses of .get() with fallback values:
  ```python
  name=json_step.get('name', step_defaults.get('name', fallback_defaults['name'])),
  allow_failure=json_step.get('allow_failure', step_defaults.get('allow_failure', fallback_defaults['allow_failure'])),
  # ... etc
  ```

#### src/configuration/di_config.py
- **Lines 88-91**: Using .get() with default fallback:
  ```python
  db_path = defaults.get("default_arguments", {}).get("persistence_driver", {}).get("db_path", "cph_history.db")
  ```
- **Line 91**: Hardcoded fallback value "cph_history.db"

#### src/application/execution_requests.py
- **Line 71**: `max_attempts = self.retry_config.get('max_attempts', 1)`
- **Lines 84-85**: Using .get() with default empty strings:
  ```python
  stdout = result.get('stdout', '')
  stderr = result.get('stderr', '')
  ```
- **Line 88**: `if not result.get('success', False):`
- **Line 90**: `result.get('error') or Exception(...)`

#### src/infrastructure/ast_analyzer.py
- **Line 56**: `module = node.module or ''` - Using "or" operator for fallback
- **Line 61**: `level=node.level or 0` - Using "or" operator for fallback

### 3. Default Value Usage in Configuration

#### src/infrastructure/drivers/generic/execution_driver.py
- **Lines 78-85**: Using _get_default_value method to retrieve defaults, but with hardcoded fallback values:
  ```python
  cwd = self._get_default_value("infrastructure_defaults.shell.cwd", ".")
  env = self._get_default_value("infrastructure_defaults.shell.env", {})
  inputdata = self._get_default_value("infrastructure_defaults.shell.inputdata", "")
  timeout = self._get_default_value("infrastructure_defaults.shell.timeout", 30)
  ```

## Recommendations

1. **Remove all default parameter values** - All function parameters should require explicit values from callers
2. **Remove all fallback processing** - Replace .get() with direct dictionary access, remove "or" operators for defaults
3. **Configuration defaults** - All default values should come from configuration files, never hardcoded
4. **Error handling** - Instead of fallbacks, raise appropriate errors when required values are missing

## Impact

These violations go against CLAUDE.md's principles of:
- Explicit value passing (no hidden defaults)
- No fallback processing (which can hide missing required values)
- All defaults must come from configuration files

The violations create technical debt and make it harder to track down issues when required values are missing.