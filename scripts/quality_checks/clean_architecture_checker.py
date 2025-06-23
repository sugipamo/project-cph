#!/usr/bin/env python3
"""
クリーンアーキテクチャチェッカー - レイヤー違反・依存関係方向性をチェック
"""

import ast
from pathlib import Path
from typing import Dict, List, Set

from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger

from .base.base_quality_checker import QualityCheckExecutor


class CleanArchitectureChecker(QualityCheckExecutor):
    def __init__(self, file_handler: FileHandler, logger: Logger, issues: List[str], verbose: bool = False):
        super().__init__(file_handler, logger, issues, verbose)

        # クリーンアーキテクチャのレイヤー定義
        self.layer_hierarchy = {
            'domain': 0,        # 内側（ビジネスロジック）
            'operations': 0,    # ドメイン層（プロジェクト特有）
            'context': 1,       # アプリケーション層
            'workflow': 1,      # アプリケーション層
            'cli': 2,           # インターフェース層
            'infrastructure': 2, # インフラストラクチャ層
            'configuration': 2   # インフラストラクチャ層
        }

        # 許可される依存関係
        self.allowed_dependencies = {
            'domain': [],
            'operations': [],
            'context': ['operations', 'domain'],
            'workflow': ['operations', 'domain', 'context'],
            'cli': ['operations', 'domain', 'context', 'workflow'],
            'infrastructure': ['operations', 'domain'],
            'configuration': []
        }

    def check_clean_architecture(self) -> bool:
        """クリーンアーキテクチャルールのチェック（互換性維持用メソッド）"""
        return self.check()

    def check(self) -> bool:
        """クリーンアーキテクチャルールのチェック"""
        spinner = None
        if not self.verbose:
            spinner = self.create_progress_spinner("クリーンアーキテクチャチェック")
            spinner.start()

        architecture_issues = []

        # モジュール間の依存関係を分析
        module_dependencies = self._analyze_dependencies()

        # レイヤー違反をチェック
        layer_violations = self._check_layer_violations(module_dependencies)
        architecture_issues.extend(layer_violations)

        # 循環依存をチェック
        circular_deps = self._check_circular_dependencies(module_dependencies)
        architecture_issues.extend(circular_deps)

        # ドメイン純粋性をチェック
        domain_purity_issues = self._check_domain_purity()
        architecture_issues.extend(domain_purity_issues)

        if spinner:
            spinner.stop()

        if architecture_issues:
            self.issues.extend([f"クリーンアーキテクチャ違反: {issue}" for issue in architecture_issues])
            return False

        return True

    def _analyze_dependencies(self) -> Dict[str, Set[str]]:
        """プロジェクト内のモジュール間依存関係を分析"""
        dependencies = {}

        # 対象ファイルを取得（testsを除外）
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)

                # モジュール名を取得
                module_name = self._get_module_name(file_path)
                if not module_name:
                    continue

                dependencies[module_name] = set()

                # インポート文を解析
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.module.startswith('src.'):
                            dependencies[module_name].add(node.module)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('src.'):
                                dependencies[module_name].add(alias.name)

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")

        return dependencies

    def _check_layer_violations(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """レイヤー間の依存関係違反をチェック"""
        violations = []

        for from_module, deps in dependencies.items():
            from_layer = self._get_layer_from_module(from_module)
            if not from_layer:
                continue

            for to_module in deps:
                to_layer = self._get_layer_from_module(to_module)
                if not to_layer:
                    continue

                # 依存関係方向をチェック
                if not self._is_allowed_dependency(from_layer, to_layer):
                    violations.append(
                        f"{from_module} ({from_layer}) -> {to_module} ({to_layer})"
                    )

        return violations

    def _check_circular_dependencies(self, dependencies: Dict[str, Set[str]]) -> List[str]:
        """循環依存をチェック"""
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(module: str, path: List[str]) -> None:
            if module in rec_stack:
                # 循環発見
                cycle_start = path.index(module)
                cycle = path[cycle_start:] + [module]
                circular_deps.append(f"循環依存: {' -> '.join(cycle)}")
                return

            if module in visited:
                return

            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            # CLAUDE.mdルール適用: dict.get()使用禁止、明示的設定取得
            if module in dependencies:
                module_deps = dependencies[module]
            else:
                module_deps = set()
            for dep in module_deps:
                if dep in dependencies:  # プロジェクト内モジュールのみ
                    dfs(dep, path.copy())

            rec_stack.remove(module)

        for module in dependencies:
            if module not in visited:
                dfs(module, [])

        return circular_deps

    def _check_domain_purity(self) -> List[str]:
        """ドメイン層の純粋性をチェック（インフラストラクチャ依存の検出）"""
        purity_issues = []

        # ドメイン層のファイルを取得
        target_files = self.get_target_files(excluded_categories=["tests"])
        domain_files = [f for f in target_files if '/operations/' in f or '/domain/' in f]

        # 禁止されたインポート（インフラストラクチャ系）
        forbidden_imports = {
            'subprocess', 'shutil', 'sqlite3', 'docker', 'requests', 'urllib',
            'json', 'yaml', 'toml', 'configparser'  # 設定系も制限
        }

        for file_path in domain_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

                for node in ast.walk(tree):
                    # 外部ライブラリのインポートをチェック
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in forbidden_imports:
                                purity_issues.append(
                                    f"{relative_path}:{node.lineno} ドメイン層でインフラストラクチャ依存: import {alias.name}"
                                )
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        if node.module in forbidden_imports:
                            purity_issues.append(
                                f"{relative_path}:{node.lineno} ドメイン層でインフラストラクチャ依存: from {node.module}"
                            )
                        # src.infrastructure への直接依存もチェック
                        elif node.module.startswith('src.infrastructure'):
                            purity_issues.append(
                                f"{relative_path}:{node.lineno} ドメイン層でインフラストラクチャ層への直接依存: {node.module}"
                            )

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to check domain purity for {file_path}: {e}")

        return purity_issues

    def _get_module_name(self, file_path: str) -> str:
        """ファイルパスからモジュール名を生成"""
        try:
            path = Path(file_path)
            # src/から始まる相対パスを取得
            parts = path.parts
            src_index = None
            for i, part in enumerate(parts):
                if part == 'src':
                    src_index = i
                    break

            if src_index is None:
                return ""

            module_parts = parts[src_index:]
            # __init__.pyの場合はディレクトリ名のみ使用
            if module_parts[-1] == '__init__.py':
                module_parts = module_parts[:-1]
            else:
                # .pyを除去
                last_part = module_parts[-1]
                if last_part.endswith('.py'):
                    module_parts = module_parts[:-1] + (last_part[:-3],)

            return '.'.join(module_parts)
        except Exception:
            return ""

    def _get_layer_from_module(self, module_name: str) -> str:
        """モジュール名からレイヤーを特定"""
        if not module_name.startswith('src.'):
            return ""

        parts = module_name.split('.')
        if len(parts) < 2:
            return ""

        layer_name = parts[1]
        return layer_name if layer_name in self.layer_hierarchy else ""

    def _is_allowed_dependency(self, from_layer: str, to_layer: str) -> bool:
        """依存関係が許可されているかチェック"""
        if from_layer not in self.allowed_dependencies:
            return False

        # 同じレイヤー内は許可
        if from_layer == to_layer:
            return True

        # 許可されたレイヤーへの依存かチェック
        return to_layer in self.allowed_dependencies[from_layer]
