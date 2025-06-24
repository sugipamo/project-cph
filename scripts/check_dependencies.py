#!/usr/bin/env python3
"""依存性注入チェックスクリプト

CLAUDE.mdの原則に従い、以下をチェックします：
1. operations層からinfrastructure層への直接依存
2. デフォルト値の使用
3. 副作用の適切な配置
4. 循環依存
"""
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyChecker:
    """依存関係チェックツール"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations = []
        self.layer_mapping = {
            'operations': 'domain',
            'infrastructure': 'infrastructure',
            'context': 'application',
            'workflow': 'application'
        }
    
    def check_all(self) -> Dict[str, List[str]]:
        """全ての依存関係チェックを実行"""
        results = {
            'layer_violations': self.check_layer_violations(),
            'default_value_violations': self.check_default_values(),
            'side_effect_violations': self.check_side_effects(),
            'circular_dependencies': self.check_circular_dependencies()
        }
        return results
    
    def check_layer_violations(self) -> List[str]:
        """レイヤー間の不適切な依存関係をチェック"""
        violations = []
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            layer = self._get_layer_from_path(py_file)
            if not layer:
                continue
                
            imports = self._extract_imports(py_file)
            for imp in imports:
                target_layer = self._get_layer_from_import(imp)
                if target_layer and not self._is_valid_dependency(layer, target_layer):
                    violations.append(f"{py_file}:{imp} - {layer} -> {target_layer} (不適切な依存)")
        
        return violations
    
    def check_default_values(self) -> List[str]:
        """デフォルト値の使用をチェック"""
        violations = []
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 関数の引数でのデフォルト値をチェック
                if re.search(r'def\s+\w+\([^)]*=\s*[^,)]+', line):
                    violations.append(f"{py_file}:{line_num} - デフォルト値の使用禁止")
                
                # hasattr() による代替処理をチェック
                if 'hasattr(' in line:
                    violations.append(f"{py_file}:{line_num} - hasattr()による代替処理（デフォルト値代替）")
        
        return violations
    
    def check_side_effects(self) -> List[str]:
        """副作用の適切な配置をチェック"""
        violations = []
        src_path = self.project_root / 'src'
        
        # 副作用が許可されるパス
        allowed_paths = [
            'src/infrastructure',
            'scripts/infrastructure',
            'main.py'
        ]
        
        side_effect_patterns = [
            r'open\s*\(',
            r'write\s*\(',
            r'mkdir\s*\(',
            r'subprocess\.',
            r'os\.',
            r'shutil\.',
            r'print\s*\('
        ]
        
        for py_file in src_path.rglob('*.py'):
            if any(str(py_file).startswith(allowed) for allowed in allowed_paths):
                continue
                
            content = py_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in side_effect_patterns:
                    if re.search(pattern, line):
                        violations.append(f"{py_file}:{line_num} - 副作用の不適切な配置")
                        break
        
        return violations
    
    def check_circular_dependencies(self) -> List[str]:
        """循環依存をチェック"""
        violations = []
        dependency_graph = self._build_dependency_graph()
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    violations.append(f"循環依存: {node} -> {neighbor}")
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in dependency_graph:
            if node not in visited:
                has_cycle(node)
        
        return violations
    
    def _get_layer_from_path(self, path: Path) -> str:
        """ファイルパスからレイヤーを取得"""
        parts = path.parts
        src_index = None
        
        for i, part in enumerate(parts):
            if part == 'src':
                src_index = i
                break
        
        if src_index is None or src_index + 1 >= len(parts):
            return ''
        
        layer_dir = parts[src_index + 1]
        return self.layer_mapping.get(layer_dir, layer_dir)
    
    def _get_layer_from_import(self, import_str: str) -> str:
        """import文からレイヤーを取得"""
        if not import_str.startswith('src.'):
            return ''
        
        parts = import_str.split('.')
        if len(parts) < 2:
            return ''
        
        layer_dir = parts[1]
        return self.layer_mapping.get(layer_dir, layer_dir)
    
    def _extract_imports(self, py_file: Path) -> List[str]:
        """Pythonファイルからimport文を抽出"""
        imports = []
        content = py_file.read_text(encoding='utf-8')
        
        # from ... import ...
        from_imports = re.findall(r'from\s+([\w.]+)\s+import', content)
        imports.extend(from_imports)
        
        # import ...
        import_statements = re.findall(r'^import\s+([\w.]+)', content, re.MULTILINE)
        imports.extend(import_statements)
        
        return imports
    
    def _is_valid_dependency(self, from_layer: str, to_layer: str) -> bool:
        """依存関係が有効かチェック"""
        # 同じレイヤー内は常に有効
        if from_layer == to_layer:
            return True
        
        # ドメイン層（operations）は他の層に依存してはいけない
        if from_layer == 'domain':
            return False
        
        # アプリケーション層はドメイン層とインフラ層に依存可能
        if from_layer == 'application':
            return to_layer in ['domain', 'infrastructure']
        
        # インフラ層はドメイン層に依存可能（インターフェース実装のため）
        if from_layer == 'infrastructure':
            return to_layer == 'domain'
        
        return True
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """依存関係グラフを構築"""
        graph = {}
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            module_name = str(py_file.relative_to(self.project_root)).replace('/', '.').replace('.py', '')
            imports = self._extract_imports(py_file)
            
            src_imports = [imp for imp in imports if imp.startswith('src.')]
            graph[module_name] = src_imports
        
        return graph


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    checker = DependencyChecker(project_root)
    results = checker.check_all()
    
    total_violations = 0
    for category, violations in results.items():
        if violations:
            print(f"\n=== {category.upper()} ===")
            for violation in violations:
                print(f"  {violation}")
            total_violations += len(violations)
    
    if total_violations == 0:
        print("✅ 依存関係チェック完了: 違反なし")
        return 0
    else:
        print(f"\n❌ 依存関係チェック完了: {total_violations}件の違反")
        return 1


if __name__ == "__main__":
    sys.exit(main())