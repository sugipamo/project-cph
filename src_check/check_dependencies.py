#!/usr/bin/env python3
"""Dependency checker to enforce clean architecture principles.

This script analyzes import statements to ensure that dependencies
follow clean architecture rules:
- Domain layer should not depend on any other layer
- Application layer should only depend on Domain layer
- Infrastructure layer can depend on Domain and Application layers
- Presentation layer can depend on Application layer (and Domain indirectly)
"""
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyChecker:
    """Check dependencies between layers."""
    
    def __init__(self, src_path: str = "src"):
        self.src_path = Path(src_path)
        self.layer_mapping = {
            "domain": "domain",
            "application": "application",
            "infrastructure": "infrastructure",
            "presentation": "presentation",
            "configuration": "infrastructure",  # Treat as infrastructure
            "operations": "mixed",  # Needs to be split
            "data": "application",  # Should be in application
            "utils": "shared",  # Can be used by any layer
            "logging": "application",
            "context": "infrastructure",
        }
        self.violations: List[Tuple[str, str, str]] = []
    
    def get_layer(self, module_path: str) -> str:
        """Determine which layer a module belongs to."""
        parts = module_path.split(".")
        if len(parts) > 1 and parts[0] == "src":
            directory = parts[1]
            return self.layer_mapping.get(directory, "unknown")
        return "external"
    
    def check_import(self, from_module: str, to_module: str) -> bool:
        """Check if an import is allowed based on clean architecture rules."""
        from_layer = self.get_layer(from_module)
        to_layer = self.get_layer(to_module)
        
        # External and shared imports are always allowed
        if to_layer in ["external", "shared"]:
            return True
        
        # Define allowed dependencies
        allowed_deps = {
            "domain": [],  # Domain should not depend on anything
            "application": ["domain"],
            "infrastructure": ["domain", "application"],
            "presentation": ["application", "domain"],
            "mixed": ["domain", "application", "infrastructure"],  # Temporary
        }
        
        # Check if the dependency is allowed
        if from_layer in allowed_deps:
            allowed = allowed_deps[from_layer]
            if to_layer not in allowed and to_layer != from_layer:
                return False
        
        return True
    
    def extract_imports(self, file_path: Path) -> List[str]:
        """Extract all imports from a Python file."""
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return imports
    
    def get_module_path(self, file_path: Path) -> str:
        """Convert file path to module path."""
        relative_path = file_path.relative_to(self.src_path.parent)
        module_path = str(relative_path).replace(os.sep, ".").replace(".py", "")
        return module_path
    
    def check_file(self, file_path: Path) -> None:
        """Check dependencies in a single file."""
        from_module = self.get_module_path(file_path)
        imports = self.extract_imports(file_path)
        
        for import_module in imports:
            if import_module.startswith("src."):
                if not self.check_import(from_module, import_module):
                    from_layer = self.get_layer(from_module)
                    to_layer = self.get_layer(import_module)
                    self.violations.append((
                        str(file_path),
                        f"{from_layer} -> {to_layer}",
                        import_module
                    ))
    
    def check_all(self) -> None:
        """Check all Python files in the src directory."""
        for file_path in self.src_path.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                self.check_file(file_path)
    
    def report(self) -> int:
        """Report violations and return exit code."""
        if not self.violations:
            print("✅ No dependency violations found!")
            return 0
        
        print(f"❌ Found {len(self.violations)} dependency violations:\n")
        
        # Group violations by type
        by_type: Dict[str, List[Tuple[str, str]]] = {}
        for file_path, violation_type, import_module in self.violations:
            if violation_type not in by_type:
                by_type[violation_type] = []
            by_type[violation_type].append((file_path, import_module))
        
        # Report each type
        for violation_type, violations in by_type.items():
            print(f"\n{violation_type} violations:")
            for file_path, import_module in violations[:5]:  # Show first 5
                print(f"  - {file_path}")
                print(f"    imports: {import_module}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
        
        print("\nClean Architecture Rules:")
        print("- Domain layer should not depend on any other layer")
        print("- Application layer should only depend on Domain layer")
        print("- Infrastructure layer can depend on Domain and Application")
        print("- Presentation layer can depend on Application (and Domain)")
        
        return 1


def main():
    """Main entry point."""
    checker = DependencyChecker()
    checker.check_all()
    sys.exit(checker.report())


if __name__ == "__main__":
    main()