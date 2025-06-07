#!/usr/bin/env python3
"""
プロジェクト全体のインポート関係を分析し、循環依存や双方向依存を特定するスクリプト
"""

import ast
import json
from collections import defaultdict, deque
from pathlib import Path


class ImportAnalyzer:
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.modules: dict[str, dict] = {}
        self.import_graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_import_graph: dict[str, set[str]] = defaultdict(set)

    def extract_imports_from_file(self, file_path: Path) -> list[str]:
        """ファイルからインポート文を抽出"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            return imports
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def get_module_path(self, file_path: Path) -> str:
        """ファイルパスからモジュールパスを生成"""
        relative_path = file_path.relative_to(self.src_path)
        if relative_path.name == "__init__.py":
            return str(relative_path.parent).replace("/", ".")
        return str(relative_path.with_suffix("")).replace("/", ".")

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
                    return ".".join([*base_parts, remaining])
                return ".".join(base_parts)
            remaining = import_name[1:]
            if remaining:
                return ".".join(parts[:-1] + [remaining])
            return ".".join(parts[:-1])
        return import_name

    def analyze_all_files(self):
        """全てのPythonファイルを分析"""
        for py_file in self.src_path.rglob("*.py"):
            module_path = self.get_module_path(py_file)
            imports = self.extract_imports_from_file(py_file)

            self.modules[module_path] = {
                "file_path": str(py_file),
                "raw_imports": imports,
                "normalized_imports": [],
                "internal_imports": [],
                "external_imports": []
            }

            # インポートを正規化
            for imp in imports:
                normalized = self.normalize_import(imp, module_path)
                self.modules[module_path]["normalized_imports"].append(normalized)

                # 内部インポートか外部インポートかを判定
                if normalized.startswith("src.") or any(normalized.startswith(mod) for mod in self.modules):
                    self.modules[module_path]["internal_imports"].append(normalized)
                    # グラフに追加（プロジェクト内モジュールのみ）
                    if normalized in self.modules or any(normalized.startswith(mod + ".") for mod in self.modules):
                        self.import_graph[module_path].add(normalized)
                        self.reverse_import_graph[normalized].add(module_path)
                else:
                    self.modules[module_path]["external_imports"].append(normalized)

    def find_circular_dependencies(self) -> list[list[str]]:
        """循環依存を検出"""
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.import_graph.get(node, []):
                if neighbor in rec_stack:
                    # 循環を発見
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor, path.copy(), visited, rec_stack)

            rec_stack.remove(node)
            path.pop()

        cycles = []
        visited = set()

        for node in self.import_graph:
            if node not in visited:
                dfs(node, [], visited, set())

        return cycles

    def calculate_layers(self) -> dict[str, int]:
        """レイヤー構造を計算（トポロジカルソート）"""
        # 循環依存がある場合、完全なトポロジカルソートはできないが、
        # 可能な限りレイヤーを計算
        layers = {}
        in_degree = defaultdict(int)

        # 各ノードの入次数を計算
        for node in self.modules:
            in_degree[node] = 0

        for node in self.import_graph:
            for neighbor in self.import_graph[node]:
                if neighbor in self.modules:
                    in_degree[neighbor] += 1

        # レイヤー0（依存なし）から開始
        queue = deque([node for node in self.modules if in_degree[node] == 0])
        layer = 0

        while queue:
            next_queue = deque()
            while queue:
                node = queue.popleft()
                layers[node] = layer

                for neighbor in self.import_graph[node]:
                    if neighbor in self.modules:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            next_queue.append(neighbor)

            queue = next_queue
            layer += 1

        # まだレイヤーが決まっていないノード（循環依存の一部）
        for node in self.modules:
            if node not in layers:
                layers[node] = -1  # 循環依存マーク

        return layers

    def generate_report(self) -> dict:
        """分析レポートを生成"""
        circular_deps = self.find_circular_dependencies()
        layers = self.calculate_layers()

        # 特に注目すべきモジュール群の分析
        focus_modules = [
            "shared.utils",
            "application.formatters",
            "context",
            "infrastructure"
        ]

        focus_analysis = {}
        for focus in focus_modules:
            focus_analysis[focus] = {
                "modules": [],
                "imports": [],
                "imported_by": []
            }

            for module_name in self.modules:
                if module_name.startswith(focus):
                    focus_analysis[focus]["modules"].append({
                        "name": module_name,
                        "layer": layers.get(module_name, -1),
                        "imports": self.modules[module_name]["internal_imports"],
                        "imported_by": list(self.reverse_import_graph.get(module_name, [])),
                        "file_path": self.modules[module_name]["file_path"]
                    })

        return {
            "summary": {
                "total_modules": len(self.modules),
                "circular_dependencies": len(circular_deps),
                "max_layer": max(layers.values()) if layers else 0
            },
            "circular_dependencies": circular_deps,
            "layers": layers,
            "focus_analysis": focus_analysis,
            "detailed_modules": self.modules
        }

def main():
    analyzer = ImportAnalyzer("/home/cphelper/project-cph/src")
    analyzer.analyze_all_files()
    report = analyzer.generate_report()

    # 結果をJSONファイルに保存
    with open("/home/cphelper/project-cph/import_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 主要な結果を表示
    print("=== プロジェクトインポート分析レポート ===\n")

    print("📊 概要:")
    print(f"  総モジュール数: {report['summary']['total_modules']}")
    print(f"  循環依存数: {report['summary']['circular_dependencies']}")
    print(f"  最大レイヤー: {report['summary']['max_layer']}")
    print()

    if report['circular_dependencies']:
        print("🔄 循環依存:")
        for i, cycle in enumerate(report['circular_dependencies']):
            print(f"  {i+1}. {' -> '.join(cycle)}")
        print()

    print("📋 注目モジュール群の分析:")
    for focus_name, focus_data in report['focus_analysis'].items():
        print(f"\n  {focus_name}:")
        print(f"    モジュール数: {len(focus_data['modules'])}")

        for module in focus_data['modules']:
            layer_info = f"Layer {module['layer']}" if module['layer'] >= 0 else "循環依存"
            print(f"    📦 {module['name']} ({layer_info})")

            if module['imports']:
                print(f"      ⬇️  インポート: {', '.join(module['imports'][:3])}{'...' if len(module['imports']) > 3 else ''}")

            if module['imported_by']:
                print(f"      ⬆️  インポート元: {', '.join(module['imported_by'][:3])}{'...' if len(module['imported_by']) > 3 else ''}")

if __name__ == "__main__":
    main()
