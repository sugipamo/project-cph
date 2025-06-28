#!/usr/bin/env python3
import ast
import os
import sys
from collections import defaultdict
from pathlib import Path

class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.imports = []
        self.delayed_imports = []
        self.current_function = None
        
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
        
    def visit_Import(self, node):
        for alias in node.names:
            import_info = {
                'module': alias.name,
                'is_delayed': self.current_function is not None,
                'function': self.current_function,
                'line': node.lineno
            }
            if self.current_function:
                self.delayed_imports.append(import_info)
            else:
                self.imports.append(import_info)
                
    def visit_ImportFrom(self, node):
        if node.module:
            import_info = {
                'module': node.module,
                'is_delayed': self.current_function is not None,
                'function': self.current_function,
                'line': node.lineno,
                'items': [alias.name for alias in node.names]
            }
            if self.current_function:
                self.delayed_imports.append(import_info)
            else:
                self.imports.append(import_info)

def analyze_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        analyzer = ImportAnalyzer(file_path)
        analyzer.visit(tree)
        return analyzer.imports, analyzer.delayed_imports
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return [], []

def normalize_module_path(module_name, current_file):
    """Convert relative imports to absolute paths based on current file location"""
    if module_name.startswith('.'):
        # Handle relative imports
        current_dir = os.path.dirname(current_file)
        parts = current_file.replace('/home/cphelper/project-cph/', '').replace('.py', '').split('/')
        
        # Count leading dots
        dot_count = len(module_name) - len(module_name.lstrip('.'))
        module_part = module_name[dot_count:]
        
        # Go up directories based on dot count
        if dot_count > 0:
            parts = parts[:-dot_count]
        
        if module_part:
            parts.extend(module_part.split('.'))
            
        return '.'.join(parts)
    else:
        # Already absolute
        return module_name

def find_circular_imports(src_dir):
    # Build import graph
    import_graph = defaultdict(set)
    delayed_import_graph = defaultdict(set)
    file_to_module = {}
    
    # Map files to module names
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                module_path = file_path.replace(src_dir + '/', '').replace('.py', '').replace('/', '.')
                file_to_module[file_path] = module_path
    
    # Analyze all files
    all_imports_info = {}
    for file_path, module_path in file_to_module.items():
        imports, delayed_imports = analyze_file(file_path)
        all_imports_info[file_path] = {
            'module': module_path,
            'imports': imports,
            'delayed_imports': delayed_imports
        }
        
        # Build graph for regular imports
        for imp in imports:
            imported_module = normalize_module_path(imp['module'], file_path)
            # Only track imports within src/
            if imported_module.startswith('src.') or not '.' in imported_module:
                import_graph[module_path].add(imported_module)
                
        # Build graph for delayed imports
        for imp in delayed_imports:
            imported_module = normalize_module_path(imp['module'], file_path)
            if imported_module.startswith('src.') or not '.' in imported_module:
                delayed_import_graph[module_path].add((imported_module, imp['function'], imp['line']))
    
    # Find circular dependencies using DFS
    def find_cycles(graph, start, path, visited, cycles):
        if start in path:
            cycle_start = path.index(start)
            cycle = path[cycle_start:] + [start]
            cycles.add(tuple(cycle))
            return
            
        if start in visited:
            return
            
        visited.add(start)
        path.append(start)
        
        for neighbor in graph.get(start, []):
            if isinstance(neighbor, tuple):
                neighbor = neighbor[0]  # Extract module name from delayed import tuple
            find_cycles(graph, neighbor, path[:], visited, cycles)
    
    # Find all cycles
    regular_cycles = set()
    delayed_cycles = set()
    
    for module in import_graph:
        find_cycles(import_graph, module, [], set(), regular_cycles)
        
    # Check for cycles including delayed imports
    combined_graph = defaultdict(set)
    for module, imports in import_graph.items():
        combined_graph[module].update(imports)
    for module, imports in delayed_import_graph.items():
        combined_graph[module].update([imp[0] for imp in imports])
        
    for module in combined_graph:
        find_cycles(combined_graph, module, [], set(), delayed_cycles)
    
    # Report findings
    print("=== CIRCULAR IMPORT ANALYSIS ===\n")
    
    # Report direct circular imports
    if regular_cycles:
        print("DIRECT CIRCULAR IMPORTS FOUND:")
        for cycle in sorted(regular_cycles):
            if len(cycle) > 2:  # Filter out self-imports
                print(f"\nCycle: {' → '.join(cycle)}")
                # Show details for each import in the cycle
                for i in range(len(cycle) - 1):
                    from_module = cycle[i]
                    to_module = cycle[i + 1]
                    # Find the file
                    for file_path, info in all_imports_info.items():
                        if info['module'] == from_module:
                            for imp in info['imports']:
                                if normalize_module_path(imp['module'], file_path) == to_module:
                                    print(f"  - {file_path} (line {imp['line']}): imports {imp['module']}")
    else:
        print("No direct circular imports found.\n")
    
    # Report delayed imports
    print("\nDELAYED IMPORTS (potential circular dependency workarounds):")
    delayed_found = False
    for file_path, info in sorted(all_imports_info.items()):
        if info['delayed_imports']:
            delayed_found = True
            print(f"\n{file_path}:")
            for imp in info['delayed_imports']:
                print(f"  - Line {imp['line']}: imports {imp['module']} in function '{imp['function']}'")
                if 'items' in imp:
                    print(f"    Items: {', '.join(imp['items'])}")
    
    if not delayed_found:
        print("No delayed imports found.")
    
    # Check if any delayed imports are part of cycles
    print("\n\nCIRCULAR DEPENDENCIES INCLUDING DELAYED IMPORTS:")
    cycles_with_delayed = set()
    for cycle in delayed_cycles:
        if len(cycle) > 2:
            # Check if this cycle involves any delayed imports
            has_delayed = False
            for i in range(len(cycle) - 1):
                from_module = cycle[i]
                to_module = cycle[i + 1]
                for file_path, info in all_imports_info.items():
                    if info['module'] == from_module:
                        for imp in info['delayed_imports']:
                            if normalize_module_path(imp['module'], file_path) == to_module:
                                has_delayed = True
                                break
            if has_delayed:
                cycles_with_delayed.add(cycle)
                
    if cycles_with_delayed:
        for cycle in sorted(cycles_with_delayed):
            print(f"\nCycle involving delayed imports: {' → '.join(cycle)}")
    else:
        print("No additional cycles found when including delayed imports.")

if __name__ == "__main__":
    src_dir = "/home/cphelper/project-cph/src"
    find_circular_imports(src_dir)