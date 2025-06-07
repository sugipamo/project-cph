#!/usr/bin/env python3
import os


def count_lines_of_code(file_path):
    """Count non-empty, non-comment lines in a Python file"""
    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

        loc = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        return loc
    except:
        return 0

# Analyze complexity of modules
module_complexity = {}

for root, _dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, 'src')
            module_path = rel_path.replace('/', '.').replace('.py', '')

            loc = count_lines_of_code(file_path)
            module_complexity[module_path] = loc

# Get tested modules
tested_modules = set()
for root, _dirs, files in os.walk('tests'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            test_name = file[5:-3]
            tested_modules.add(test_name)

# Categorize by complexity and test status
high_complexity_untested = []
medium_complexity_untested = []
critical_untested = []

CRITICAL_MODULES = [
    'main', 'config.manager', 'core.exceptions.error_handler',
    'operations.base_request', 'context.execution_context',
    'env_integration.service'
]

print("=== COMPLEXITY AND COVERAGE ANALYSIS ===\n")

print("High Complexity Modules (>200 LOC):")
for module, loc in sorted(module_complexity.items(), key=lambda x: x[1], reverse=True):
    if loc > 200:
        module_parts = module.split('.')
        test_candidates = [
            module_parts[-1],
            '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],
            '_'.join(module_parts),
        ]

        has_test = any(candidate in tested_modules for candidate in test_candidates)
        status = "✓ TESTED" if has_test else "✗ UNTESTED"

        if not has_test:
            high_complexity_untested.append((module, loc))

        print(f"  {status:12} {module:50} ({loc:3d} LOC)")

print(f"\nHigh complexity untested modules: {len(high_complexity_untested)}")

print("\n" + "="*80)
print("PRIORITY MATRIX FOR TEST COVERAGE IMPROVEMENT")
print("="*80)

# Priority 1: Critical + High Complexity + No Tests
p1_modules = []
for module, loc in high_complexity_untested:
    if any(crit in module for crit in CRITICAL_MODULES) or module in CRITICAL_MODULES:
        p1_modules.append((module, loc))

print(f"\nPRIORITY 1 - Critical High-Complexity Modules (No Tests): {len(p1_modules)}")
for module, loc in sorted(p1_modules, key=lambda x: x[1], reverse=True):
    print(f"  🔴 {module:50} ({loc:3d} LOC)")

# Priority 2: Critical + Medium Complexity + No Tests
p2_modules = []
for module, loc in module_complexity.items():
    if 50 <= loc <= 200 and (any(crit in module for crit in CRITICAL_MODULES) or module in CRITICAL_MODULES):
        module_parts = module.split('.')
        test_candidates = [
            module_parts[-1],
            '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],
            '_'.join(module_parts),
        ]
        has_test = any(candidate in tested_modules for candidate in test_candidates)
        if not has_test:
            p2_modules.append((module, loc))

print(f"\nPRIORITY 2 - Critical Medium-Complexity Modules (No Tests): {len(p2_modules)}")
for module, loc in sorted(p2_modules, key=lambda x: x[1], reverse=True)[:10]:
    print(f"  🟡 {module:50} ({loc:3d} LOC)")

# Priority 3: High Complexity Non-Critical + No Tests
p3_modules = []
for module, loc in high_complexity_untested:
    if not any(crit in module for crit in CRITICAL_MODULES) and module not in CRITICAL_MODULES:
        p3_modules.append((module, loc))

print(f"\nPRIORITY 3 - Non-Critical High-Complexity Modules (No Tests): {len(p3_modules)}")
for module, loc in sorted(p3_modules, key=lambda x: x[1], reverse=True)[:10]:
    print(f"  🟠 {module:50} ({loc:3d} LOC)")

# Dead code analysis
print("\n" + "="*60)
print("POTENTIAL DEAD CODE ANALYSIS")
print("="*60)

small_untested = []
for module, loc in module_complexity.items():
    if loc < 20:
        module_parts = module.split('.')
        test_candidates = [
            module_parts[-1],
            '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],
            '_'.join(module_parts),
        ]
        has_test = any(candidate in tested_modules for candidate in test_candidates)
        if not has_test:
            small_untested.append((module, loc))

print(f"\nSmall Untested Modules (<20 LOC): {len(small_untested)}")
print("These may be dead code or utility modules:")
for module, loc in sorted(small_untested, key=lambda x: x[1]):
    print(f"  {module:50} ({loc:2d} LOC)")

# Summary
total_modules = len(module_complexity)
total_loc = sum(module_complexity.values())
tested_count = sum(1 for module in module_complexity
                  if any(candidate in tested_modules
                        for candidate in [module.split('.')[-1],
                                        '_'.join(module.split('.')[-2:]) if len(module.split('.')) > 1 else module.split('.')[-1],
                                        '_'.join(module.split('.'))]))

print("\n" + "="*60)
print("COVERAGE SUMMARY")
print("="*60)
print(f"Total modules: {total_modules}")
print(f"Total LOC: {total_loc}")
print(f"Tested modules: {tested_count}")
print(f"Coverage by module count: {tested_count/total_modules*100:.1f}%")
print(f"Priority 1 modules needing tests: {len(p1_modules)}")
print(f"Priority 2 modules needing tests: {len(p2_modules)}")
print(f"High complexity untested: {len(high_complexity_untested)}")
