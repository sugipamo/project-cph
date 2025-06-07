#!/usr/bin/env python3
import os

# Get all source modules
src_files = set()
for root, _dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            rel_path = os.path.relpath(os.path.join(root, file), 'src')
            module_path = rel_path.replace('/', '.').replace('.py', '')
            src_files.add(module_path)

# Get all test modules
test_files = set()
for root, _dirs, files in os.walk('tests'):
    for file in files:
        if file.startswith('test_') and file.endswith('.py'):
            # Extract what this test is testing
            test_name = file[5:-3]  # Remove 'test_' and '.py'
            test_files.add(test_name)

print('=== MODULES WITH NO TESTS ===')
modules_without_tests = []
for module in sorted(src_files):
    module_parts = module.split('.')
    test_candidates = [
        module_parts[-1],  # Just the file name
        '_'.join(module_parts[-2:]) if len(module_parts) > 1 else module_parts[-1],  # parent_file
        '_'.join(module_parts),  # full_path
    ]

    has_test = any(candidate in test_files for candidate in test_candidates)
    if not has_test:
        modules_without_tests.append(module)
        print(f'  {module}')

print(f'\nTotal source modules: {len(src_files)}')
print(f'Modules without tests: {len(modules_without_tests)}')
print(f'Coverage by test existence: {((len(src_files) - len(modules_without_tests)) / len(src_files) * 100):.1f}%')

# Categorize modules
print('\n=== MODULE CATEGORIZATION ===')

categories = {
    'Core Operations': [],
    'Context & Config': [],
    'Environment & Workflow': [],
    'Infrastructure': [],
    'New Modules': [],
    'Utilities': [],
    'Mock/Test Support': []
}

for module in sorted(src_files):
    if any(x in module for x in ['operations', 'request', 'driver']):
        categories['Core Operations'].append(module)
    elif any(x in module for x in ['context', 'config', 'resolver']):
        categories['Context & Config'].append(module)
    elif any(x in module for x in ['env', 'workflow', 'step']):
        categories['Environment & Workflow'].append(module)
    elif any(x in module for x in ['resource', 'infrastructure', 'factories']):
        categories['Infrastructure'].append(module)
    elif any(x in module for x in ['core.exceptions', 'performance', 'cli']):
        categories['New Modules'].append(module)
    elif any(x in module for x in ['utils', 'validation', 'format']):
        categories['Utilities'].append(module)
    elif 'mock' in module:
        categories['Mock/Test Support'].append(module)
    else:
        categories['Infrastructure'].append(module)  # Default category

for category, modules in categories.items():
    if modules:
        tested = sum(1 for m in modules if m not in modules_without_tests)
        total = len(modules)
        coverage = (tested / total * 100) if total > 0 else 0
        print(f'\n{category}: {tested}/{total} tested ({coverage:.1f}%)')
        for module in modules:
            status = "✓" if module not in modules_without_tests else "✗"
            print(f'  {status} {module}')
