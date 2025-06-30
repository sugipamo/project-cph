#!/usr/bin/env python3
"""
Generate visual dependency graph for the project
"""

import json
from pathlib import Path
import subprocess

def generate_dot_graph():
    """Generate GraphViz DOT file from dependency analysis"""
    
    # Load dependency report
    report_file = Path(__file__).parent / 'dependency_analysis_report.json'
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Create DOT content
    dot_lines = ['digraph DependencyGraph {']
    dot_lines.append('  rankdir=LR;')
    dot_lines.append('  node [shape=box, style=rounded];')
    dot_lines.append('  ')
    
    # Add nodes with special styling for problematic modules
    circular_modules = set()
    for cycle in report['circular_imports']:
        circular_modules.update(cycle)
    
    type_checking_modules = {item['module'] for item in report['type_checking_usage']}
    tight_coupling_modules = set(report['tight_coupling'].keys())
    
    # Collect all modules
    all_modules = set()
    for module, deps in report['tight_coupling'].items():
        all_modules.add(module)
        all_modules.update(deps)
    
    # Style nodes
    for module in all_modules:
        attrs = []
        if module in circular_modules:
            attrs.append('fillcolor="#ffcdd2"')  # Red
            attrs.append('style=filled')
        elif module in type_checking_modules:
            attrs.append('fillcolor="#fff3cd"')  # Yellow
            attrs.append('style=filled')
        elif module in tight_coupling_modules:
            attrs.append('fillcolor="#cfe2ff"')  # Blue
            attrs.append('style=filled')
        
        if attrs:
            dot_lines.append(f'  "{module}" [{", ".join(attrs)}];')
    
    dot_lines.append('  ')
    
    # Add edges for tight coupling modules
    for module, deps in report['tight_coupling'].items():
        for dep in deps[:10]:  # Limit to 10 deps per module for readability
            dot_lines.append(f'  "{module}" -> "{dep}";')
    
    # Highlight circular dependencies
    if report['circular_imports']:
        dot_lines.append('  ')
        dot_lines.append('  // Circular dependencies')
        dot_lines.append('  edge [color=red, style=bold];')
        for cycle in report['circular_imports']:
            if len(cycle) == 1:
                # Self-referencing module
                dot_lines.append(f'  "{cycle[0]}" -> "{cycle[0]}" [color=red];')
    
    # Add TYPE_CHECKING dependencies
    dot_lines.append('  ')
    dot_lines.append('  // TYPE_CHECKING dependencies')
    dot_lines.append('  edge [color=orange, style=dashed];')
    for item in report['type_checking_usage']:
        module = item['module']
        for dep in item['delayed_imports']:
            dot_lines.append(f'  "{module}" -> "{dep}" [color=orange, style=dashed];')
    
    dot_lines.append('}')
    
    # Write DOT file
    dot_file = Path(__file__).parent / 'dependency_graph.dot'
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dot_lines))
    
    print(f"DOT file generated: {dot_file}")
    
    # Try to generate PNG if graphviz is available
    try:
        png_file = Path(__file__).parent / 'dependency_graph.png'
        subprocess.run(['dot', '-Tpng', str(dot_file), '-o', str(png_file)], 
                      check=True, capture_output=True)
        print(f"PNG graph generated: {png_file}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("GraphViz not available. Install it to generate PNG output.")
        print("You can visualize the DOT file at: https://dreampuf.github.io/GraphvizOnline/")
    
    # Generate summary
    print("\n=== Dependency Graph Legend ===")
    print("🔴 Red nodes: Modules with circular imports")
    print("🟡 Yellow nodes: Modules using TYPE_CHECKING")
    print("🔵 Blue nodes: Modules with high coupling (>= 5 dependencies)")
    print("🟠 Orange dashed lines: TYPE_CHECKING delayed imports")
    print("🔴 Red bold lines: Circular dependencies")


if __name__ == '__main__':
    generate_dot_graph()