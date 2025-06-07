#!/usr/bin/env python3
"""
包括的な依存関係問題分析 - 具体的なインポート文とファイルパスを特定
"""

import ast
import json
from collections import defaultdict
from pathlib import Path


class ComprehensiveDependencyAnalyzer:
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.problems = {
            'circular_imports': [],
            'layer_violations': [],
            'tight_coupling': [],
            'shared_utils_overuse': [],
            'env_layer_issues': []
        }

    def analyze_file_imports(self, file_path: Path) -> dict:
        """ファイルから詳細なインポート情報を抽出"""
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()
                content = ''.join(lines)

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'line_text': lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                        })
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'names': [alias.name for alias in node.names],
                        'line': node.lineno,
                        'line_text': lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        'level': node.level
                    })

            return {
                'file_path': str(file_path),
                'imports': imports,
                'total_lines': len(lines)
            }
        except Exception as e:
            return {
                'file_path': str(file_path),
                'imports': [],
                'error': str(e),
                'total_lines': 0
            }

    def determine_layer(self, module_path: str) -> str:
        """モジュールのアーキテクチャレイヤーを特定"""
        if module_path.startswith('src.domain'):
            return 'domain'
        if module_path.startswith('src.infrastructure'):
            return 'infrastructure'
        if module_path.startswith('src.application'):
            return 'application'
        if module_path.startswith('src.context'):
            return 'context'
        if module_path.startswith('src.shared'):
            return 'shared'
        if module_path.startswith('src.env_core'):
            return 'env_core'
        if module_path.startswith('src.env_integration'):
            return 'env_integration'
        if module_path.startswith('src.utils'):
            return 'utils'
        if module_path.startswith('src.workflow'):
            return 'workflow'
        if module_path.startswith('src.pure_functions'):
            return 'pure_functions'
        return 'unknown'

    def get_module_path(self, file_path: Path) -> str:
        """ファイルパスからモジュールパスを生成"""
        relative_path = file_path.relative_to(self.src_path)
        if relative_path.name == "__init__.py":
            if str(relative_path.parent) == ".":
                return "src"
            return "src." + str(relative_path.parent).replace("/", ".")
        module_path = str(relative_path.with_suffix("")).replace("/", ".")
        return "src." + module_path

    def analyze_layer_violations(self) -> list[dict]:
        """具体的なレイヤー違反を特定"""
        violations = []

        # アーキテクチャルール定義
        forbidden_dependencies = [
            # domainレイヤーは他のレイヤーに依存してはいけない
            ('domain', ['infrastructure', 'application', 'context'], 'Domain layer should not depend on infrastructure, application, or context layers'),
            # infrastructureレイヤーはapplicationレイヤーに依存してはいけない
            ('infrastructure', ['application'], 'Infrastructure layer should not depend on application layer'),
            # sharedレイヤーは特定のレイヤーに依存してはいけない
            ('shared', ['application', 'context'], 'Shared layer should not depend on application or context layers'),
            # env_coreはenv_integrationに依存してはいけない
            ('env_core', ['env_integration'], 'Core environment should not depend on integration layer')
        ]

        for py_file in self.src_path.rglob("*.py"):
            file_info = self.analyze_file_imports(py_file)
            module_path = self.get_module_path(py_file)
            source_layer = self.determine_layer(module_path)

            for import_info in file_info['imports']:
                import_module = import_info['module']
                if import_module.startswith('src.'):
                    target_layer = self.determine_layer(import_module)

                    # ルール違反をチェック
                    for source_pattern, forbidden_targets, rule_description in forbidden_dependencies:
                        if source_layer == source_pattern and target_layer in forbidden_targets:
                            violations.append({
                                'source_file': str(py_file),
                                'source_module': module_path,
                                'source_layer': source_layer,
                                'target_module': import_module,
                                'target_layer': target_layer,
                                'line_number': import_info['line'],
                                'import_statement': import_info['line_text'],
                                'rule_violation': rule_description,
                                'severity': self.get_violation_severity(source_layer, target_layer)
                            })

        return violations

    def get_violation_severity(self, source_layer: str, target_layer: str) -> str:
        """違反の重要度を判定"""
        high_severity_pairs = [
            ('domain', 'infrastructure'),
            ('domain', 'application'),
            ('env_core', 'env_integration')
        ]

        if (source_layer, target_layer) in high_severity_pairs:
            return 'high'
        if source_layer == 'shared' and target_layer in ['application', 'context']:
            return 'medium'
        return 'low'

    def analyze_shared_utils_overuse(self) -> list[dict]:
        """shared.utilsの過度な使用を分析"""
        shared_utils_usage = defaultdict(list)

        for py_file in self.src_path.rglob("*.py"):
            file_info = self.analyze_file_imports(py_file)
            module_path = self.get_module_path(py_file)

            for import_info in file_info['imports']:
                import_module = import_info['module']
                if import_module.startswith('src.shared.utils'):
                    shared_utils_usage[import_module].append({
                        'importing_file': str(py_file),
                        'importing_module': module_path,
                        'layer': self.determine_layer(module_path),
                        'line_number': import_info['line'],
                        'import_statement': import_info['line_text']
                    })

        # 過度に使用されているユーティリティを特定
        overused_utils = []
        for util_module, usages in shared_utils_usage.items():
            if len(usages) > 5:  # 閾値: 5個以上のファイルから使用されている
                overused_utils.append({
                    'utility_module': util_module,
                    'usage_count': len(usages),
                    'usages': usages
                })

        return overused_utils

    def analyze_complex_imports(self) -> list[dict]:
        """複雑なインポート構造を分析"""
        complex_files = []

        for py_file in self.src_path.rglob("*.py"):
            file_info = self.analyze_file_imports(py_file)
            internal_imports = [imp for imp in file_info['imports']
                              if imp['module'].startswith('src.')]

            if len(internal_imports) > 8:  # 閾値: 8個以上の内部インポート
                complex_files.append({
                    'file_path': str(py_file),
                    'module_path': self.get_module_path(py_file),
                    'internal_import_count': len(internal_imports),
                    'imports': internal_imports
                })

        return sorted(complex_files, key=lambda x: x['internal_import_count'], reverse=True)

    def analyze_env_dependencies(self) -> dict:
        """env_core/とenv_integration/間の依存関係問題を詳細分析"""
        env_issues = {
            'core_to_integration_violations': [],
            'integration_modules_analysis': [],
            'core_modules_analysis': []
        }

        for py_file in self.src_path.rglob("*.py"):
            file_info = self.analyze_file_imports(py_file)
            module_path = self.get_module_path(py_file)

            if module_path.startswith('src.env_core'):
                # env_coreからenv_integrationへの依存をチェック
                for import_info in file_info['imports']:
                    import_module = import_info['module']
                    if import_module.startswith('src.env_integration'):
                        env_issues['core_to_integration_violations'].append({
                            'source_file': str(py_file),
                            'source_module': module_path,
                            'target_module': import_module,
                            'line_number': import_info['line'],
                            'import_statement': import_info['line_text'],
                            'severity': 'high'
                        })

                env_issues['core_modules_analysis'].append({
                    'module': module_path,
                    'file_path': str(py_file),
                    'imports': [imp for imp in file_info['imports'] if imp['module'].startswith('src.')]
                })

            elif module_path.startswith('src.env_integration'):
                env_issues['integration_modules_analysis'].append({
                    'module': module_path,
                    'file_path': str(py_file),
                    'imports': [imp for imp in file_info['imports'] if imp['module'].startswith('src.')]
                })

        return env_issues

    def find_potential_circular_imports(self) -> list[dict]:
        """潜在的な循環インポートを特定"""
        # このような詳細な循環インポート検出は複雑なので、
        # 簡単な双方向依存をチェック
        module_dependencies = defaultdict(set)

        for py_file in self.src_path.rglob("*.py"):
            file_info = self.analyze_file_imports(py_file)
            module_path = self.get_module_path(py_file)

            for import_info in file_info['imports']:
                import_module = import_info['module']
                if import_module.startswith('src.'):
                    module_dependencies[module_path].add(import_module)

        # 双方向依存をチェック
        bidirectional_deps = []
        checked_pairs = set()

        for mod_a, deps_a in module_dependencies.items():
            for mod_b in deps_a:
                if mod_b in module_dependencies and mod_a in module_dependencies[mod_b]:
                    pair = tuple(sorted([mod_a, mod_b]))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        bidirectional_deps.append({
                            'module_a': mod_a,
                            'module_b': mod_b,
                            'type': 'bidirectional_dependency'
                        })

        return bidirectional_deps

    def generate_comprehensive_report(self) -> dict:
        """包括的な分析レポートを生成"""
        print("🔍 包括的依存関係分析を実行中...")

        layer_violations = self.analyze_layer_violations()
        shared_utils_overuse = self.analyze_shared_utils_overuse()
        complex_imports = self.analyze_complex_imports()
        env_dependencies = self.analyze_env_dependencies()
        circular_imports = self.find_potential_circular_imports()

        return {
            'summary': {
                'layer_violations': len(layer_violations),
                'shared_utils_overuse': len(shared_utils_overuse),
                'complex_import_files': len(complex_imports),
                'env_core_violations': len(env_dependencies['core_to_integration_violations']),
                'potential_circular_imports': len(circular_imports)
            },
            'layer_violations': layer_violations,
            'shared_utils_overuse': shared_utils_overuse,
            'complex_imports': complex_imports,
            'env_dependencies': env_dependencies,
            'potential_circular_imports': circular_imports
        }

def main():
    analyzer = ComprehensiveDependencyAnalyzer("/home/cphelper/project-cph/src")
    report = analyzer.generate_comprehensive_report()

    print("\n" + "="*80)
    print("📋 包括的依存関係問題分析レポート")
    print("="*80)

    print("\n📊 概要:")
    print(f"  🚨 レイヤー違反: {report['summary']['layer_violations']}")
    print(f"  🛠️  shared.utils過度使用: {report['summary']['shared_utils_overuse']}")
    print(f"  🔗 複雑なインポートファイル: {report['summary']['complex_import_files']}")
    print(f"  ⚠️  env_core違反: {report['summary']['env_core_violations']}")
    print(f"  🔄 潜在的循環インポート: {report['summary']['potential_circular_imports']}")

    print("\n🚨 レイヤー違反 (具体的なファイルとインポート文):")
    for i, violation in enumerate(report['layer_violations'][:10]):
        print(f"  {i+1}. 【{violation['severity'].upper()}】")
        print(f"     ファイル: {violation['source_file']}")
        print(f"     行番号: {violation['line_number']}")
        print(f"     インポート文: {violation['import_statement']}")
        print(f"     問題: {violation['source_layer']} → {violation['target_layer']}")
        print(f"     理由: {violation['rule_violation']}")
        print()

    print("\n🛠️  shared.utils過度使用:")
    for usage in report['shared_utils_overuse']:
        print(f"  📦 {usage['utility_module']} ({usage['usage_count']} 回使用)")
        for use in usage['usages'][:3]:  # 最初の3つを表示
            print(f"    - {use['importing_file']}:{use['line_number']}")
        if len(usage['usages']) > 3:
            print(f"    ... 他 {len(usage['usages']) - 3} 件")
        print()

    print("\n🔗 最も複雑なインポート構造:")
    for i, complex_file in enumerate(report['complex_imports'][:5]):
        print(f"  {i+1}. {complex_file['file_path']}")
        print(f"     内部インポート数: {complex_file['internal_import_count']}")
        print(f"     主なインポート: {[imp['module'] for imp in complex_file['imports'][:3]]}")
        print()

    if report['env_dependencies']['core_to_integration_violations']:
        print("\n⚠️  env_core → env_integration 違反:")
        for violation in report['env_dependencies']['core_to_integration_violations']:
            print(f"  ❌ {violation['source_file']}:{violation['line_number']}")
            print(f"     {violation['import_statement']}")
            print()

    if report['potential_circular_imports']:
        print("\n🔄 潜在的な循環インポート:")
        for circular in report['potential_circular_imports']:
            print(f"  ↔️  {circular['module_a']} ⟷ {circular['module_b']}")

    # JSONレポートを保存
    with open("/home/cphelper/project-cph/comprehensive_dependency_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n💾 詳細レポートを comprehensive_dependency_analysis.json に保存しました")

if __name__ == "__main__":
    main()
