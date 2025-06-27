#!/usr/bin/env python3
"""
Comprehensive dependency analysis tool for detecting:
1. Circular imports
2. TYPE_CHECKING delayed imports
3. Tight coupling issues
4. Dependency graph visualization
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import json

class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import information from Python files"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.imports = []
        self.type_checking_imports = []
        self.local_imports = []
        self.in_type_checking_block = False
        self.in_function = False
        self.current_function = None
        
    def visit_If(self, node):
        """Detect TYPE_CHECKING blocks"""
        if (isinstance(node.test, ast.Name) and 
            node.test.id == 'TYPE_CHECKING'):
            self.in_type_checking_block = True
            self.generic_visit(node)
            self.in_type_checking_block = False
        else:
            self.generic_visit(node)
            
    def visit_FunctionDef(self, node):
        """Track when we're inside a function"""
        old_in_function = self.in_function
        old_function = self.current_function
        self.in_function = True
        self.current_function = node.name
        self.generic_visit(node)
        self.in_function = old_in_function
        self.current_function = old_function
        
    def visit_Import(self, node):
        """Handle import statements"""
        for alias in node.names:
            import_info = {
                'module': alias.name,
                'line': node.lineno,
                'type': 'import',
                'in_type_checking': self.in_type_checking_block,
                'in_function': self.in_function,
                'function_name': self.current_function if self.in_function else None
            }
            
            if self.in_type_checking_block:
                self.type_checking_imports.append(import_info)
            elif self.in_function:
                self.local_imports.append(import_info)
            else:
                self.imports.append(import_info)
                
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Handle from ... import statements"""
        module = node.module or ''
        level = node.level
        
        # Handle relative imports
        if level > 0:
            parts = self.file_path.parts
            if 'src' in parts:
                src_idx = parts.index('src')
                current_parts = list(parts[src_idx:-1])  # Remove filename
                
                # Go up 'level' directories
                for _ in range(level):
                    if current_parts:
                        current_parts.pop()
                        
                if module:
                    current_parts.extend(module.split('.'))
                    
                module = '.'.join(current_parts)
        
        for alias in node.names:
            import_info = {
                'module': module,
                'name': alias.name,
                'line': node.lineno,
                'type': 'from',
                'level': level,
                'in_type_checking': self.in_type_checking_block,
                'in_function': self.in_function,
                'function_name': self.current_function if self.in_function else None
            }
            
            if self.in_type_checking_block:
                self.type_checking_imports.append(import_info)
            elif self.in_function:
                self.local_imports.append(import_info)
            else:
                self.imports.append(import_info)
                
        self.generic_visit(node)


class DependencyAnalyzer:
    """Analyze dependencies and detect issues"""
    
    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.type_checking_deps: Dict[str, Set[str]] = defaultdict(set)
        self.local_import_files: Set[str] = set()
        self.file_to_module: Dict[Path, str] = {}
        self.module_to_file: Dict[str, Path] = {}
        
    def analyze(self):
        """Analyze all Python files in src directory"""
        py_files = list(self.src_dir.rglob('*.py'))
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
                
            # Convert file path to module name
            relative_path = py_file.relative_to(self.src_dir.parent)
            module_name = str(relative_path.with_suffix('')).replace('/', '.')
            
            self.file_to_module[py_file] = module_name
            self.module_to_file[module_name] = py_file
            
            # Analyze imports
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content, filename=str(py_file))
                analyzer = ImportAnalyzer(py_file)
                analyzer.visit(tree)
                
                # Process regular imports
                for imp in analyzer.imports:
                    target_module = imp['module']
                    if target_module.startswith('src.'):
                        self.dependencies[module_name].add(target_module)
                        
                # Process TYPE_CHECKING imports
                for imp in analyzer.type_checking_imports:
                    target_module = imp['module']
                    if target_module.startswith('src.'):
                        self.type_checking_deps[module_name].add(target_module)
                        
                # Track files with local imports
                if analyzer.local_imports:
                    self.local_import_files.add(str(py_file))
                    
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
                
    def detect_circular_imports(self) -> List[List[str]]:
        """Detect circular import dependencies"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    
            rec_stack.remove(node)
            
        for node in self.dependencies:
            if node not in visited:
                dfs(node, [])
                
        # Remove duplicate cycles
        unique_cycles = []
        seen = set()
        
        for cycle in cycles:
            # Normalize cycle
            min_idx = cycle.index(min(cycle))
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
            
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(list(normalized)[:-1])
                
        return unique_cycles
        
    def detect_tight_coupling(self, threshold: int = 5) -> Dict[str, List[str]]:
        """Detect modules with too many dependencies"""
        tight_coupling = {}
        
        for module, deps in self.dependencies.items():
            if len(deps) >= threshold:
                tight_coupling[module] = sorted(list(deps))
                
        return tight_coupling
        
    def generate_report(self) -> Dict:
        """Generate comprehensive dependency report"""
        circular_imports = self.detect_circular_imports()
        tight_coupling = self.detect_tight_coupling()
        
        # Find modules using TYPE_CHECKING
        type_checking_modules = []
        for module, deps in self.type_checking_deps.items():
            if deps:
                type_checking_modules.append({
                    'module': module,
                    'file': str(self.module_to_file.get(module, 'Unknown')),
                    'delayed_imports': sorted(list(deps))
                })
                
        report = {
            'summary': {
                'total_modules': len(self.dependencies),
                'total_dependencies': sum(len(deps) for deps in self.dependencies.values()),
                'circular_imports_count': len(circular_imports),
                'type_checking_usage_count': len(type_checking_modules),
                'local_import_files_count': len(self.local_import_files),
                'tight_coupling_count': len(tight_coupling)
            },
            'circular_imports': circular_imports,
            'type_checking_usage': type_checking_modules,
            'local_import_files': sorted(list(self.local_import_files)),
            'tight_coupling': tight_coupling
        }
        
        return report


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    
    if not src_dir.exists():
        print(f"Error: src directory not found at {src_dir}")
        return
        
    print("Analyzing dependencies in src/ directory...")
    analyzer = DependencyAnalyzer(src_dir)
    analyzer.analyze()
    
    report = analyzer.generate_report()
    
    # Print summary
    print("\n=== Dependency Analysis Report ===\n")
    print(f"Total modules analyzed: {report['summary']['total_modules']}")
    print(f"Total dependencies: {report['summary']['total_dependencies']}")
    print(f"Circular imports detected: {report['summary']['circular_imports_count']}")
    print(f"Modules using TYPE_CHECKING: {report['summary']['type_checking_usage_count']}")
    print(f"Files with local imports: {report['summary']['local_import_files_count']}")
    print(f"Modules with tight coupling: {report['summary']['tight_coupling_count']}")
    
    # Print circular imports
    if report['circular_imports']:
        print("\n🔴 Circular Imports Detected:")
        for i, cycle in enumerate(report['circular_imports'], 1):
            print(f"\n  {i}. {' → '.join(cycle)}")
            
    # Print TYPE_CHECKING usage
    if report['type_checking_usage']:
        print("\n⚠️  TYPE_CHECKING Delayed Imports:")
        for item in report['type_checking_usage'][:5]:
            print(f"\n  Module: {item['module']}")
            print(f"  File: {item['file']}")
            print(f"  Delayed imports: {', '.join(item['delayed_imports'])}")
            
        if len(report['type_checking_usage']) > 5:
            print(f"\n  ... and {len(report['type_checking_usage']) - 5} more modules")
            
    # Print tight coupling
    if report['tight_coupling']:
        print("\n⚡ Modules with High Coupling (>= 5 dependencies):")
        for module, deps in sorted(report['tight_coupling'].items(), 
                                  key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"\n  {module}: {len(deps)} dependencies")
            
    # Save full report
    report_file = project_root / 'src_check' / 'dependency_analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Full report saved to: {report_file}")


if __name__ == '__main__':
    main()