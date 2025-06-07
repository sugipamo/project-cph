#!/usr/bin/env python3
import os

# Define critical modules based on functionality
CRITICAL_MODULES = {
    'Entry Points': [
        'main',
        'context.user_input_parser',
        'env.build_operations'
    ],
    'Core Operations': [
        'operations.base_request',
        'operations.composite.composite_request',
        'operations.docker.docker_driver',
        'operations.shell.shell_driver',
        'operations.file.file_driver'
    ],
    'Configuration System': [
        'config.manager',
        'config.validation',
        'context.execution_context',
        'context.resolver.config_resolver'
    ],
    'Error Handling': [
        'core.exceptions.error_handler',
        'core.exceptions.base_exceptions',
        'operations.exceptions.composite_step_failure'
    ],
    'Workflow Engine': [
        'env_core.workflow.graph_based_workflow_builder',
        'env_core.step.workflow',
        'env_integration.service'
    ],
    'Factory System': [
        'env_factories.unified_factory',
        'operations.factory.driver_factory'
    ]
}

# Get all tested modules
tested_modules = set()
for root, _dirs, files in os.walk('tests'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            test_name = file[5:-3]  # Remove 'test_' and '.py'
            tested_modules.add(test_name)

# Also check for module-based tests
src_files = set()
for root, _dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            rel_path = os.path.relpath(os.path.join(root, file), 'src')
            module_path = rel_path.replace('/', '.').replace('.py', '')
            src_files.add(module_path)

print("=== CRITICAL MODULE COVERAGE ANALYSIS ===\n")

total_critical = 0
total_tested = 0

for category, modules in CRITICAL_MODULES.items():
    print(f"{category}:")
    category_critical = 0
    category_tested = 0

    for module in modules:
        category_critical += 1
        total_critical += 1

        # Check if module exists
        exists = module in src_files

        # Check various test naming patterns
        module_parts = module.split('.')
        test_candidates = [
            module_parts[-1],  # Just the file name
            '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],  # parent_file
            '_'.join(module_parts),  # full_path
        ]

        has_test = any(candidate in tested_modules for candidate in test_candidates)

        if has_test:
            category_tested += 1
            total_tested += 1
            status = "✓ TESTED"
        else:
            status = "✗ NOT TESTED"

        if not exists:
            status += " (MISSING)"

        print(f"  {status:15} {module}")

    coverage_pct = (category_tested / category_critical * 100) if category_critical > 0 else 0
    print(f"  Category Coverage: {category_tested}/{category_critical} ({coverage_pct:.1f}%)\n")

overall_coverage = (total_tested / total_critical * 100) if total_critical > 0 else 0
print(f"OVERALL CRITICAL MODULE COVERAGE: {total_tested}/{total_critical} ({overall_coverage:.1f}%)")

print("\n=== HIGH-IMPACT MISSING TESTS ===")
high_impact_missing = []

for category, modules in CRITICAL_MODULES.items():
    for module in modules:
        if module in src_files:  # Module exists
            module_parts = module.split('.')
            test_candidates = [
                module_parts[-1],
                '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],
                '_'.join(module_parts),
            ]

            has_test = any(candidate in tested_modules for candidate in test_candidates)
            if not has_test:
                high_impact_missing.append((category, module))

for category, module in high_impact_missing:
    print(f"  {category:20} - {module}")

print(f"\nTotal high-impact missing tests: {len(high_impact_missing)}")
