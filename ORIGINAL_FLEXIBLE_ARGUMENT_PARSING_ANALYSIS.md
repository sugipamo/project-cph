# Original Flexible Argument Parsing Analysis

## Overview

This document analyzes the original flexible argument parsing behavior that existed before the regression in commit e603686 (2025-05-23). The original implementation allowed arguments to be specified in any order, making the CLI much more user-friendly.

## Regression Details

- **Regression Commit**: e603686 (2025-05-23)
- **Breaking Change**: Introduced sequential parsing that requires arguments in a specific order
- **Original Flexible Implementation**: Found in commit 418894d and earlier

## Original Flexible Parsing Logic

### 1. Core Parsing Strategy

The original parser used a **flexible, order-independent approach** with the following algorithm:

```python
def parse(self, args: list) -> ExecutionContext:
    # 1. Initialize context with system_info.json values
    context = ExecutionContext(...)
    context = self._apply_system_info(context)
    
    # 2. Load all env.json files from contest_env/
    env_jsons = self._load_all_env_jsons(CONTEST_ENV_DIR)
    
    # 3. Apply flexible argument parsing - ORDER INDEPENDENT
    args, context = self._apply_language(args, context, env_jsons)     # Remove language from args
    args, context = self._apply_env_type(args, context)               # Remove env_type from args  
    args, context = self._apply_command(args, context)                # Remove command from args
    args, context = self._apply_names(args, context)                  # Consume remaining args
    
    # 4. Finalize context
    # ... context finalization steps
```

### 2. Language Detection (`_apply_language`)

**Key Features:**
- Scanned **all arguments** to find language matches
- Supported **aliases** (e.g., "py" for "python")
- **Removed matched argument** from the list
- Set `context.language` and `context.env_json`

**Implementation:**
```python
def _apply_language(self, args: list, context: ExecutionContext, env_jsons: List[dict]) -> tuple:
    language_alias_map = self._extract_language_and_aliases(env_jsons)
    for idx, arg in enumerate(args):
        for lang, aliases in language_alias_map.items():
            if arg == lang or arg in aliases:  # Match language name or alias
                for env_json in env_jsons:
                    if lang in env_json:
                        context.language = lang
                        context.env_json = env_json
                        new_args = args[:idx] + args[idx+1:]  # Remove matched arg
                        return new_args, context
    return args, context
```

**Supported Patterns:**
- `["python", "local", "test", "abc300", "a"]`
- `["local", "python", "test", "abc300", "a"]`
- `["test", "python", "local", "abc300", "a"]`
- `["py", "local", "t", "abc300", "a"]` (aliases)

### 3. Environment Type Detection (`_apply_env_type`)

**Key Features:**
- Only processed after language was identified
- Searched through `context.env_json[language]["env_types"]`
- Supported aliases for environment types
- **Removed matched argument** from the list

**Implementation:**
```python
def _apply_env_type(self, args: list, context: ExecutionContext) -> tuple:
    if not context.env_json or not context.language:
        return args, context
    env_types = context.env_json[context.language]["env_types"]
    for idx, arg in enumerate(args):
        for env_type_name, env_type_conf in env_types.items():
            aliases = env_type_conf["aliases"] if "aliases" in env_type_conf else []
            if arg == env_type_name or arg in aliases:
                context.env_type = env_type_name
                new_args = args[:idx] + args[idx+1:]  # Remove matched arg
                return new_args, context
    return args, context
```

**Supported Environment Types (from shared/env.json):**
- `"local"` with aliases `["local"]`
- `"docker"` with aliases `["docker"]`

### 4. Command Detection (`_apply_command`)

**Key Features:**
- Only processed after language was identified
- Searched through `context.env_json[language]["commands"]`
- Supported command aliases
- **Removed matched argument** from the list

**Implementation:**
```python
def _apply_command(self, args: list, context: ExecutionContext) -> tuple:
    if not context.env_json or not context.language:
        return args, context
    commands = context.env_json[context.language]["commands"]
    for idx, arg in enumerate(args):
        for cmd_name, cmd_conf in commands.items():
            aliases = cmd_conf["aliases"] if "aliases" in cmd_conf else []
            if arg == cmd_name or arg in aliases:
                context.command_type = cmd_name
                new_args = args[:idx] + args[idx+1:]  # Remove matched arg
                return new_args, context
    return args, context
```

**Supported Commands (from shared/env.json):**
- `"open"` with aliases `["o"]`
- `"test"` with aliases `["t"]` 
- `"submit"` with aliases `["s"]`
- `"backup"` with aliases `["b"]`
- `"switch"` with aliases `["sw"]`

### 5. Name Assignment (`_apply_names`)

**Key Features:**
- Processed **remaining arguments** after language/env_type/command removal
- Assigned in **reverse order**: `problem_name`, then `contest_name`
- Maximum of 2 arguments allowed

**Implementation:**
```python
def _apply_names(self, args: list, context: ExecutionContext) -> tuple:
    if len(args) > 2:
        raise ValueError(f"引数が多すぎます: {args}")
    
    # 意図した動きなので直さないこと。
    keys = ["problem_name", "contest_name"]
    for key, arg in zip(keys, reversed(args)):
        setattr(context, key, arg)
    return [], context
```

**Assignment Logic:**
- 1 remaining arg: `problem_name = arg`
- 2 remaining args: `problem_name = args[1]`, `contest_name = args[0]`

## Configuration Structure

### Language Configuration (contest_env/python/env.json)
```json
{
  "python": {
    "aliases": ["py"],
    "language_id": "5078",
    "source_file_name": "main.py",
    "run_command": "python3"
  }
}
```

### Shared Configuration (contest_env/shared/env.json)
```json
{
  "shared": {
    "commands": {
      "open": { "aliases": ["o"] },
      "test": { "aliases": ["t"] },
      "submit": { "aliases": ["s"] },
      "backup": { "aliases": ["b"] },
      "switch": { "aliases": ["sw"] }
    },
    "env_types": {
      "local": { "aliases": ["local"] },
      "docker": { "aliases": ["docker"] }
    }
  }
}
```

## Supported Argument Patterns

The original system supported all of these equivalent patterns:

### Complete Commands
```bash
./cph.sh python local test abc300 a
./cph.sh python test local abc300 a
./cph.sh local python test abc300 a
./cph.sh test python local abc300 a
./cph.sh abc300 a python local test
./cph.sh python local abc300 a test
```

### With Aliases
```bash
./cph.sh py local t abc300 a
./cph.sh py t local abc300 a
./cph.sh local py t abc300 a
./cph.sh t py local abc300 a
./cph.sh abc300 a py local t
```

### Mixed Order Examples
```bash
./cph.sh python local o abc300 a    # open command
./cph.sh o a python local abc300    # open command, different order
./cph.sh abc300 a py docker submit  # submit with docker
./cph.sh s py docker abc300 a       # submit alias with docker
```

## Key Flexibility Features

### 1. **Order Independence**
- Arguments could appear in any position
- Parser would scan entire argument list for each type

### 2. **Alias Support**
- Languages: `py` → `python`
- Commands: `o` → `open`, `t` → `test`, `s` → `submit`
- Environment types: `local`, `docker`

### 3. **Incremental Argument Consumption**
- Each parsing step removed matched arguments
- Remaining arguments were processed by subsequent steps
- Final step consumed positional arguments for names

### 4. **Contextual Validation**
- Environment types and commands were only valid for identified language
- Used language-specific configuration from env.json files

### 5. **Fallback Behavior**
- System preserved previous state from system_info.json
- Arguments only updated specified fields
- Missing arguments used existing context values

## Current Sequential Parser Problems

The current implementation (post-e603686) has these limitations:

1. **Fixed Order Requirement**: `language → env_type → command → names`
2. **No Argument Scanning**: Only checks first available argument for each type
3. **Loss of Flexibility**: Cannot handle user-friendly argument orders
4. **Reduced Usability**: Forces users to remember specific order

## Test Patterns (from original tests)

The original tests demonstrated these working patterns:

```python
# Basic pattern
args = ["python", "docker", "test", "abc300", "a"]
# Result: language=python, env_type=docker, command=test, contest=abc300, problem=a

# Alias pattern  
args = ["py", "local", "t", "abc300", "a"]
# Result: language=python, env_type=local, command=test, contest=abc300, problem=a
```

## Implementation Status

- **Original Flexible Parser**: Commit 418894d and earlier
- **Regression Introduced**: Commit e603686 (2025-05-23)
- **Current Sequential Parser**: Requires specific order
- **Restoration Needed**: Implement flexible parsing logic in current codebase