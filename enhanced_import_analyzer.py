#!/usr/bin/env python3
"""
強化されたインポート関係分析ツール
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import json

class EnhancedImportAnalyzer:
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.modules: Dict[str, Dict] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_module: Dict[str, str] = {}
        
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
    
    def normalize_import(self, import_name: str, current_module: str) -> str:
        """インポート名を正規化"""
        if import_name.startswith("."):
            # 相対インポート
            parts = current_module.split(".")
            if import_name.startswith(".."):
                level = len(import_name) - len(import_name.lstrip("."))
                base_parts = parts[:-level] if level < len(parts) else []
                remaining = import_name[level:]
                if remaining:
                    return ".".join(base_parts + [remaining])
                else:
                    return ".".join(base_parts)
            else:
                remaining = import_name[1:]
                if remaining:
                    return ".".join(parts[:-1] + [remaining])
                else:
                    return ".".join(parts[:-1])
        else:
            return import_name
    
    def extract_imports_from_file(self, file_path: Path) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
        """ファイルからインポート文を抽出し、より詳細な情報を返す"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            from_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                        # from X import Y の形式も記録
                        imported_names = [alias.name for alias in node.names]
                        from_imports.append((node.module, imported_names))
                        
            return imports, from_imports
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return [], []
    
    def analyze_all_files(self):
        """全てのPythonファイルを分析"""
        print("Analyzing all Python files...")
        
        for py_file in self.src_path.rglob("*.py"):
            module_path = self.get_module_path(py_file)
            self.file_to_module[str(py_file)] = module_path
            
            imports, from_imports = self.extract_imports_from_file(py_file)
            
            self.modules[module_path] = {
                "file_path": str(py_file),
                "raw_imports": imports,
                "from_imports": from_imports,
                "normalized_imports": [],
                "internal_imports": [],
                "external_imports": []
            }
            
            # インポートを正規化し、内部/外部を分類
            for imp in imports:
                normalized = self.normalize_import(imp, module_path)
                self.modules[module_path]["normalized_imports"].append(normalized)
                
                # 内部インポートか外部インポートかを判定
                if normalized.startswith("src."):
                    self.modules[module_path]["internal_imports"].append(normalized)
                    # グラフに追加
                    self.import_graph[module_path].add(normalized)
                    self.reverse_import_graph[normalized].add(module_path)
                else:
                    self.modules[module_path]["external_imports"].append(normalized)
        
        print(f"Found {len(self.modules)} modules")
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """DFSを使って循環依存を検出"""
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.import_graph.get(node, []):
                if neighbor in self.modules:  # 存在するモジュールのみ
                    if neighbor in rec_stack:
                        # 循環を発見
                        cycle_start_idx = path.index(neighbor) if neighbor in path else len(path)
                        cycle = path[cycle_start_idx:] + [neighbor]
                        if len(cycle) > 1:  # 自己参照以外
                            cycles.append(cycle)
                    elif neighbor not in visited:
                        dfs(neighbor, path + [neighbor], visited, rec_stack)
            
            rec_stack.remove(node)
        
        cycles = []
        visited = set()
        
        for node in self.modules:
            if node not in visited:
                dfs(node, [node], visited, set())
        
        # 重複する循環を除去
        unique_cycles = []
        for cycle in cycles:
            # 正規化（最小要素から開始）
            min_idx = cycle.index(min(cycle))
            normalized_cycle = cycle[min_idx:] + cycle[:min_idx]
            if normalized_cycle not in unique_cycles:
                unique_cycles.append(normalized_cycle)
        
        return unique_cycles
    
    def calculate_layers_with_cycles(self) -> Dict[str, int]:
        """循環依存を考慮したレイヤー計算"""
        layers = {}
        processed = set()
        
        # まず循環依存を識別
        cycles = self.find_circular_dependencies()
        cycle_members = set()
        for cycle in cycles:
            cycle_members.update(cycle)
        
        # 循環していないノードから処理
        queue = deque()
        in_degree = defaultdict(int)
        
        # 入次数を計算（循環メンバーは除外して）
        for node in self.modules:
            if node not in cycle_members:
                in_degree[node] = 0
                for dep in self.import_graph.get(node, []):
                    if dep in self.modules and dep not in cycle_members:
                        in_degree[node] += 1
        
        # 入次数0のノードをキューに追加
        for node in self.modules:
            if node not in cycle_members and in_degree[node] == 0:
                queue.append(node)
                layers[node] = 0
        
        # トポロジカルソート
        max_layer = 0
        while queue:
            current = queue.popleft()
            processed.add(current)
            
            for neighbor in self.import_graph.get(current, []):
                if neighbor in self.modules and neighbor not in cycle_members:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        layers[neighbor] = layers[current] + 1
                        max_layer = max(max_layer, layers[neighbor])
                        queue.append(neighbor)
        
        # 循環メンバーには特別なマーカーを付与
        for node in cycle_members:
            layers[node] = -1
        
        return layers
    
    def analyze_focus_modules(self, focus_modules: List[str]) -> Dict:
        """特定モジュール群の詳細分析"""
        layers = self.calculate_layers_with_cycles()
        analysis = {}
        
        for focus in focus_modules:
            analysis[focus] = {
                "modules": [],
                "layer_distribution": defaultdict(int),
                "circular_modules": [],
                "dependencies": set(),
                "dependents": set()
            }
            
            for module_name in self.modules:
                if module_name.startswith(f"src.{focus}"):
                    layer = layers.get(module_name, -1)
                    analysis[focus]["layer_distribution"][layer] += 1
                    
                    if layer == -1:
                        analysis[focus]["circular_modules"].append(module_name)
                    
                    module_info = {
                        "name": module_name,
                        "layer": layer,
                        "imports": self.modules[module_name]["internal_imports"],
                        "imported_by": list(self.reverse_import_graph.get(module_name, [])),
                        "file_path": self.modules[module_name]["file_path"]
                    }
                    analysis[focus]["modules"].append(module_info)
                    
                    # 依存関係を集計
                    for imp in self.modules[module_name]["internal_imports"]:
                        if not imp.startswith(f"src.{focus}"):
                            analysis[focus]["dependencies"].add(imp)
                    
                    for imp_by in self.reverse_import_graph.get(module_name, []):
                        if not imp_by.startswith(f"src.{focus}"):
                            analysis[focus]["dependents"].add(imp_by)
            
            # setをlistに変換（JSON serializable）
            analysis[focus]["dependencies"] = list(analysis[focus]["dependencies"])
            analysis[focus]["dependents"] = list(analysis[focus]["dependents"])
        
        return analysis
    
    def generate_detailed_report(self) -> Dict:
        """詳細分析レポートを生成"""
        circular_deps = self.find_circular_dependencies()
        layers = self.calculate_layers_with_cycles()
        
        focus_modules = [
            "shared.utils",
            "application.formatters", 
            "context",
            "infrastructure"
        ]
        
        focus_analysis = self.analyze_focus_modules(focus_modules)
        
        # 層別統計
        layer_stats = defaultdict(int)
        for layer in layers.values():
            layer_stats[layer] += 1
        
        return {
            "summary": {
                "total_modules": len(self.modules),
                "circular_dependencies": len(circular_deps),
                "modules_in_cycles": len([m for m in self.modules if layers.get(m) == -1]),
                "max_layer": max([l for l in layers.values() if l >= 0], default=0),
                "layer_distribution": dict(layer_stats)
            },
            "circular_dependencies": circular_deps,
            "layers": layers,
            "focus_analysis": focus_analysis,
            "problem_areas": self.identify_problem_areas(circular_deps, layers)
        }
    
    def identify_problem_areas(self, circular_deps: List[List[str]], layers: Dict[str, int]) -> Dict:
        """問題領域を特定"""
        problems = {
            "architectural_violations": [],
            "high_coupling_modules": [],
            "layer_violations": []
        }
        
        # アーキテクチャ違反を検出
        for module_name, module_data in self.modules.items():
            # shared.utilsがapplicationを参照している
            if module_name.startswith("src.shared.utils"):
                for imp in module_data["internal_imports"]:
                    if imp.startswith("src.application"):
                        problems["architectural_violations"].append({
                            "violator": module_name,
                            "violation": f"shared.utils module importing from application layer",
                            "imported": imp
                        })
            
            # contextがapplicationを参照している
            if module_name.startswith("src.context"):
                for imp in module_data["internal_imports"]:
                    if imp.startswith("src.application"):
                        problems["architectural_violations"].append({
                            "violator": module_name,
                            "violation": f"context module importing from application layer",
                            "imported": imp
                        })
        
        # 高結合モジュールを検出
        for module_name in self.modules:
            import_count = len(self.modules[module_name]["internal_imports"])
            imported_by_count = len(self.reverse_import_graph.get(module_name, []))
            
            if import_count > 10 or imported_by_count > 10:
                problems["high_coupling_modules"].append({
                    "module": module_name,
                    "imports": import_count,
                    "imported_by": imported_by_count
                })
        
        return problems

def main():
    analyzer = EnhancedImportAnalyzer("/home/cphelper/project-cph/src")
    analyzer.analyze_all_files()
    report = analyzer.generate_detailed_report()
    
    # 結果をJSONファイルに保存
    with open("/home/cphelper/project-cph/enhanced_import_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 主要な結果を表示
    print("\n" + "="*80)
    print("🔍 強化されたプロジェクトインポート分析レポート")
    print("="*80)
    
    print(f"\n📊 概要:")
    print(f"  📦 総モジュール数: {report['summary']['total_modules']}")
    print(f"  🔄 循環依存数: {report['summary']['circular_dependencies']}")
    print(f"  ⚠️  循環に含まれるモジュール: {report['summary']['modules_in_cycles']}")
    print(f"  📊 最大レイヤー: {report['summary']['max_layer']}")
    print(f"  📈 レイヤー分布: {report['summary']['layer_distribution']}")
    
    if report['circular_dependencies']:
        print(f"\n🔄 循環依存 ({len(report['circular_dependencies'])} 個):")
        for i, cycle in enumerate(report['circular_dependencies']):
            print(f"  {i+1}. {' → '.join(cycle)} → {cycle[0]}")
    
    print(f"\n⚠️  問題領域:")
    problems = report['problem_areas']
    
    if problems['architectural_violations']:
        print(f"  🏗️  アーキテクチャ違反 ({len(problems['architectural_violations'])} 個):")
        for violation in problems['architectural_violations'][:5]:
            print(f"    • {violation['violator']} → {violation['imported']}")
            print(f"      理由: {violation['violation']}")
    
    if problems['high_coupling_modules']:
        print(f"  🔗 高結合モジュール ({len(problems['high_coupling_modules'])} 個):")
        for module in sorted(problems['high_coupling_modules'], 
                           key=lambda x: x['imports'] + x['imported_by'], reverse=True)[:5]:
            print(f"    • {module['module']}: {module['imports']} インポート, {module['imported_by']} 被インポート")
    
    print(f"\n📋 注目モジュール群の分析:")
    for focus_name, focus_data in report['focus_analysis'].items():
        print(f"\n  📂 {focus_name}:")
        print(f"    📦 モジュール数: {len(focus_data['modules'])}")
        print(f"    📊 レイヤー分布: {dict(focus_data['layer_distribution'])}")
        
        if focus_data['circular_modules']:
            print(f"    🔄 循環依存モジュール: {len(focus_data['circular_modules'])}")
            for circ_mod in focus_data['circular_modules'][:3]:
                print(f"      • {circ_mod}")
        
        if focus_data['dependencies']:
            print(f"    ⬇️  外部依存: {len(focus_data['dependencies'])} 個")
            for dep in sorted(list(focus_data['dependencies']))[:3]:
                print(f"      • {dep}")
        
        if focus_data['dependents']:
            print(f"    ⬆️  被依存: {len(focus_data['dependents'])} 個")
            for dep in sorted(list(focus_data['dependents']))[:3]:
                print(f"      • {dep}")

if __name__ == "__main__":
    main()