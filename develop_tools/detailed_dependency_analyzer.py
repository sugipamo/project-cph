#!/usr/bin/env python3
"""
詳細な依存関係分析ツール - 特に循環依存と依存レイヤーを正確に検出
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import json

class DetailedDependencyAnalyzer:
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.modules: Dict[str, Dict] = {}
        self.direct_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
    def get_module_path(self, file_path: Path) -> str:
        """ファイルパスからモジュールパスを生成"""
        relative_path = file_path.relative_to(self.src_path)
        if relative_path.name == "__init__.py":
            if str(relative_path.parent) == ".":
                return "src"
            return "src." + str(relative_path.parent).replace("/", ".")
        else:
            module_path = str(relative_path.with_suffix("")).replace("/", ".")
            return "src." + module_path
    
    def resolve_import(self, import_name: str, current_module: str) -> Optional[str]:
        """インポート名を解決して実際のモジュールパスを返す"""
        if import_name.startswith("."):
            # 相対インポート
            parts = current_module.split(".")
            if import_name.startswith(".."):
                level = len(import_name) - len(import_name.lstrip("."))
                base_parts = parts[:-level] if level < len(parts) else []
                remaining = import_name[level:]
                if remaining:
                    resolved = ".".join(base_parts + [remaining])
                else:
                    resolved = ".".join(base_parts)
            else:
                remaining = import_name[1:]
                if remaining:
                    resolved = ".".join(parts[:-1] + [remaining])
                else:
                    resolved = ".".join(parts[:-1])
        else:
            resolved = import_name
        
        # 実際に存在するモジュールかチェック
        if resolved in self.modules:
            return resolved
        
        # パッケージレベルでのインポートかチェック
        for module in self.modules:
            if module.startswith(resolved + "."):
                return resolved  # パッケージとして存在
        
        return None if not resolved.startswith("src.") else resolved
    
    def extract_detailed_imports(self, file_path: Path) -> List[str]:
        """ファイルから詳細なインポート情報を抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        
            return imports
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def analyze_all_modules(self):
        """全モジュールを分析"""
        print("Analyzing all modules...")
        
        # まず全ファイルを登録
        for py_file in self.src_path.rglob("*.py"):
            module_path = self.get_module_path(py_file)
            self.modules[module_path] = {
                "file_path": str(py_file),
                "imports": [],
                "resolved_dependencies": set()
            }
        
        # インポート関係を解析
        for py_file in self.src_path.rglob("*.py"):
            module_path = self.get_module_path(py_file)
            imports = self.extract_detailed_imports(py_file)
            
            self.modules[module_path]["imports"] = imports
            
            for imp in imports:
                resolved = self.resolve_import(imp, module_path)
                if resolved and resolved != module_path:
                    self.modules[module_path]["resolved_dependencies"].add(resolved)
                    self.direct_dependencies[module_path].add(resolved)
        
        print(f"Found {len(self.modules)} modules")
        
        # デバッグ: いくつかのキーモジュールの依存関係を表示
        key_modules = [
            "src.shared.utils.unified_formatter",
            "src.application.formatters.format_manager",
            "src.context.utils.format_utils"
        ]
        
        for mod in key_modules:
            if mod in self.modules:
                print(f"\n{mod}:")
                print(f"  Raw imports: {self.modules[mod]['imports']}")
                print(f"  Resolved deps: {list(self.modules[mod]['resolved_dependencies'])}")
    
    def find_strongly_connected_components(self) -> List[List[str]]:
        """Tarjanのアルゴリズムで強連結成分を見つける"""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []
        
        def strongconnect(node):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            
            for neighbor in self.direct_dependencies.get(node, []):
                if neighbor in self.modules:  # 存在するモジュールのみ
                    if neighbor not in index:
                        strongconnect(neighbor)
                        lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                    elif on_stack.get(neighbor, False):
                        lowlinks[node] = min(lowlinks[node], index[neighbor])
            
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                sccs.append(component)
        
        for node in self.modules:
            if node not in index:
                strongconnect(node)
        
        # サイズ1より大きい成分のみ返す（真の循環依存）
        return [scc for scc in sccs if len(scc) > 1]
    
    def calculate_layers_topological(self) -> Dict[str, int]:
        """トポロジカルソートでレイヤーを計算"""
        # 強連結成分を見つける
        sccs = self.find_strongly_connected_components()
        scc_map = {}
        for i, scc in enumerate(sccs):
            for node in scc:
                scc_map[node] = i
        
        # 循環依存にないノードから開始
        layers = {}
        in_degree = defaultdict(int)
        
        # 循環依存ノードをマーク
        in_cycle = set()
        for scc in sccs:
            in_cycle.update(scc)
        
        # 入次数を計算（循環依存でないノードのみ）
        for node in self.modules:
            if node not in in_cycle:
                in_degree[node] = 0
                for dep in self.direct_dependencies.get(node, []):
                    if dep in self.modules and dep not in in_cycle:
                        in_degree[node] += 1
        
        # トポロジカルソート
        queue = deque([node for node in self.modules if node not in in_cycle and in_degree[node] == 0])
        layer = 0
        processed_count = 0
        
        while queue and layer < 100:  # 無限ループ防止
            next_queue = deque()
            layer_nodes = []
            
            while queue:
                node = queue.popleft()
                layers[node] = layer
                layer_nodes.append(node)
                processed_count += 1
                
                # この ノードに依存するノードを探す
                for other_node in self.modules:
                    if (other_node not in in_cycle and 
                        other_node not in layers and 
                        node in self.direct_dependencies.get(other_node, [])):
                        in_degree[other_node] -= 1
                        if in_degree[other_node] == 0:
                            next_queue.append(other_node)
            
            print(f"Layer {layer}: {len(layer_nodes)} modules")
            if layer_nodes:
                print(f"  Examples: {layer_nodes[:3]}")
            
            queue = next_queue
            layer += 1
        
        # 循環依存ノードには-1を設定
        for node in in_cycle:
            layers[node] = -1
        
        print(f"Processed {processed_count} non-cyclic modules in {layer} layers")
        print(f"Cyclic modules: {len(in_cycle)}")
        
        return layers
    
    def analyze_architectural_issues(self) -> Dict:
        """アーキテクチャの問題を分析"""
        issues = {
            "layer_violations": [],
            "circular_dependencies": [],
            "high_coupling": []
        }
        
        # 強連結成分（循環依存）を検出
        sccs = self.find_strongly_connected_components()
        for scc in sccs:
            issues["circular_dependencies"].append({
                "modules": scc,
                "size": len(scc)
            })
        
        # レイヤー違反を検出
        architectural_rules = [
            ("src.shared.utils", ["src.application"], "shared should not depend on application"),
            ("src.context", ["src.application"], "context should not depend on application"),
            ("src.domain", ["src.infrastructure", "src.application"], "domain should not depend on infrastructure or application")
        ]
        
        for source_pattern, forbidden_patterns, rule_desc in architectural_rules:
            for module in self.modules:
                if module.startswith(source_pattern):
                    for dep in self.modules[module]["resolved_dependencies"]:
                        for forbidden in forbidden_patterns:
                            if dep.startswith(forbidden):
                                issues["layer_violations"].append({
                                    "violator": module,
                                    "dependency": dep,
                                    "rule": rule_desc
                                })
        
        # 高結合モジュールを検出
        for module in self.modules:
            dep_count = len(self.modules[module]["resolved_dependencies"])
            if dep_count > 8:  # 閾値
                issues["high_coupling"].append({
                    "module": module,
                    "dependency_count": dep_count,
                    "dependencies": list(self.modules[module]["resolved_dependencies"])
                })
        
        return issues
    
    def generate_detailed_report(self) -> Dict:
        """詳細レポートを生成"""
        layers = self.calculate_layers_topological()
        issues = self.analyze_architectural_issues()
        
        # レイヤー統計
        layer_stats = defaultdict(int)
        for layer in layers.values():
            layer_stats[layer] += 1
        
        # モジュール群別の分析
        module_groups = {
            "shared.utils": [],
            "application.formatters": [],
            "context": [],
            "infrastructure": [],
            "domain": []
        }
        
        for module in self.modules:
            for group in module_groups:
                if module.startswith(f"src.{group}"):
                    module_groups[group].append({
                        "name": module,
                        "layer": layers.get(module, -1),
                        "dependencies": list(self.modules[module]["resolved_dependencies"]),
                        "dependency_count": len(self.modules[module]["resolved_dependencies"])
                    })
        
        return {
            "summary": {
                "total_modules": len(self.modules),
                "layer_distribution": dict(layer_stats),
                "max_layer": max([l for l in layers.values() if l >= 0], default=0),
                "cyclic_modules": len([m for m in layers.values() if m == -1])
            },
            "layers": layers,
            "issues": issues,
            "module_groups": module_groups
        }

def main():
    analyzer = DetailedDependencyAnalyzer("/home/cphelper/project-cph/src")
    analyzer.analyze_all_modules()
    
    print("\n" + "="*80)
    print("🔍 詳細依存関係分析")
    print("="*80)
    
    report = analyzer.generate_detailed_report()
    
    print(f"\n📊 概要:")
    print(f"  📦 総モジュール数: {report['summary']['total_modules']}")
    print(f"  📈 レイヤー分布: {report['summary']['layer_distribution']}")
    print(f"  📊 最大レイヤー: {report['summary']['max_layer']}")
    print(f"  🔄 循環依存モジュール: {report['summary']['cyclic_modules']}")
    
    print(f"\n🔄 循環依存:")
    for i, circ in enumerate(report['issues']['circular_dependencies']):
        print(f"  {i+1}. サイズ {circ['size']}: {' ↔ '.join(circ['modules'])}")
    
    print(f"\n⚠️  レイヤー違反:")
    for violation in report['issues']['layer_violations']:
        print(f"  • {violation['violator']} → {violation['dependency']}")
        print(f"    理由: {violation['rule']}")
    
    print(f"\n🔗 高結合モジュール:")
    for coupling in sorted(report['issues']['high_coupling'], 
                          key=lambda x: x['dependency_count'], reverse=True)[:5]:
        print(f"  • {coupling['module']}: {coupling['dependency_count']} 依存")
    
    print(f"\n📋 モジュール群分析:")
    for group_name, modules in report['module_groups'].items():
        if modules:
            print(f"\n  📂 {group_name} ({len(modules)} modules):")
            layer_dist = defaultdict(int)
            for mod in modules:
                layer_dist[mod['layer']] += 1
            print(f"    レイヤー分布: {dict(layer_dist)}")
            
            # 上位依存モジュール
            top_deps = sorted(modules, key=lambda x: x['dependency_count'], reverse=True)[:3]
            for mod in top_deps:
                if mod['dependency_count'] > 0:
                    print(f"    🔗 {mod['name']}: {mod['dependency_count']} 依存 (Layer {mod['layer']})")
    
    # JSONレポートを保存
    with open("/home/cphelper/project-cph/detailed_dependency_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細レポートを detailed_dependency_report.json に保存しました")

if __name__ == "__main__":
    main()