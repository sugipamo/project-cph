# CPH (Competitive Programming Helper) - Typical User Workflows

## Overview

CPH is a command-line tool designed to streamline competitive programming workflows. Based on the analysis of the existing Python implementation (`old_src`), the tool supports multiple programming languages (Python, C++, Rust) and provides a consistent interface for common competitive programming tasks.

## Core Command Structure

The basic command structure follows this pattern:
```
cph [language] [command] [env_type] [contest_name] [problem_name]
```

Where:
- `language`: python/py, cpp, rust
- `command`: open/o, test/t, submit/s
- `env_type`: local, docker
- `contest_name`: e.g., abc300, arc150
- `problem_name`: e.g., a, b, c, d

Arguments can be provided in flexible order, and the system maintains state to remember previous selections.

## Typical User Scenarios

### 1. Starting a New Contest Problem

**Scenario**: A competitive programmer wants to start working on problem A of AtCoder Beginner Contest 300.

**Workflow**:
```bash
# Open problem A of contest abc300 using Python
cph python open abc300 a

# This command will:
# 1. Backup current work (if any) to contest_stock
# 2. Restore previous work from contest_stock (if exists)
# 3. Or initialize from template if no previous work exists
# 4. Open the problem in browser (AtCoder URL)
# 5. Open the source file in the configured editor (cursor)
# 6. Download test cases using online-judge-tools
# 7. Move test cases to contest_current directory
```

**State Management**: The system remembers the current language, contest, and problem, so subsequent commands can be shorter.

### 2. Testing Solutions Locally

**Scenario**: After implementing a solution, the programmer wants to test it against sample test cases.

**Workflow**:
```bash
# Test the current solution
cph test

# Or explicitly specify the problem
cph python test abc300 a

# This command will:
# 1. Copy source file to workspace
# 2. Run the solution against all test cases
# 3. Display results in formatted output (pass/fail with execution time)
```

**Output Format**: The system supports multiple output formats (minimal, standard, competitive) for test results.

### 3. Submitting Solutions

**Scenario**: The solution passes all test cases, and the programmer wants to submit it to the online judge.

**Workflow**:
```bash
# Submit the current solution
cph submit

# Or explicitly specify
cph python submit abc300 a

# This command will:
# 1. Copy source file to workspace
# 2. Use online-judge-tools to submit to AtCoder
# 3. Wait for judge results
# 4. Display submission status
```

### 4. Switching Between Problems

**Scenario**: The programmer wants to switch from problem A to problem B while preserving their work.

**Workflow**:
```bash
# Current state: working on abc300 problem a
cph open b

# This command will:
# 1. Automatically backup abc300/a to contest_stock
# 2. Load or initialize abc300/b
# 3. Update the current context
```

### 5. Using Docker Environment

**Scenario**: The programmer wants to test their C++ solution in a Docker container to ensure consistency with the judge environment.

**Workflow**:
```bash
# Test using Docker environment
cph cpp test docker abc300 c

# This will:
# 1. Build or use existing Docker image for C++
# 2. Mount necessary directories
# 3. Run tests inside the container
# 4. Return results to the host
```

### 6. Working with Multiple Languages

**Scenario**: The programmer wants to solve the same problem in different languages.

**Workflow**:
```bash
# Start with Python
cph python open abc300 a
# ... implement solution ...
cph test

# Switch to C++
cph cpp open abc300 a
# ... implement C++ solution ...
cph test
```

Each language maintains separate contest_stock storage, so work is preserved independently.

## File Organization

The system maintains the following directory structure:

```
workspace/              # Temporary working directory
contest_current/        # Active problem files
contest_stock/          # Backed up solutions
  └── {language}/
      └── {contest}/
          └── {problem}/
contest_template/       # Language-specific templates
  └── {language}/
test/                   # Test cases
  ├── *.in             # Input files
  └── *.out            # Expected output files
```

## Advanced Features

### 1. Debug Mode
```bash
cph --debug python test abc300 a
```
Enables verbose logging for troubleshooting.

### 2. Custom Templates
Templates in `contest_template/{language}/` are automatically copied when starting new problems.

### 3. Parallel Execution
Some commands support parallel execution for improved performance (configured in env.json).

### 4. State Persistence
The system uses SQLite to persist:
- Current contest/problem/language state
- Command history
- File tracking information

## Implementation Status

### Current Rust Implementation
The Rust rewrite currently has:
- ✅ Basic CLI structure with clap
- ✅ Command definitions (open, test, submit, init)
- ✅ Error handling framework
- ✅ Infrastructure interfaces defined
- ❌ Command implementations (TODO)
- ❌ Workflow execution engine
- ❌ Configuration management
- ❌ File operations
- ❌ Docker integration
- ❌ Online-judge-tools integration

### Expected vs Current Functionality
The Python implementation provides a complete competitive programming workflow, while the Rust implementation is in early stages with only the CLI skeleton implemented. The core functionality that needs to be ported includes:

1. **Workflow Engine**: Step-based execution system
2. **Configuration Management**: Language and command configurations
3. **File Management**: Contest file backup/restore system
4. **External Tool Integration**: online-judge-tools, Docker
5. **Template System**: Language-specific problem templates
6. **Test Runner**: Execution and result formatting

## Next Steps for Development

1. Implement the configuration system to load env.json files
2. Build the workflow execution engine
3. Implement file system operations for contest management
4. Integrate with external tools (oj, Docker)
5. Add proper state management with persistence
6. Implement the command handlers