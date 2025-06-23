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
            'configuration': 1, # アプリケーション層として再定義
            'cli': 2,           # インターフェース層
            'infrastructure': 2 # インフラストラクチャ層
        }

        # 許可される依存関係
        self.allowed_dependencies = {
            'domain': [],
            'operations': [],
            'context': ['operations', 'domain'],
            'workflow': ['operations', 'domain', 'context'],
            'configuration': ['operations'],  # 設定層はドメイン層のみに依存可能
            'cli': ['operations', 'domain', 'context', 'workflow'],
            'infrastructure': ['operations', 'domain']
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

        # コメントアウトされたコードをチェック
        commented_code_issues = self._check_commented_code()
        architecture_issues.extend(commented_code_issues)

        # 動的インポートをチェック
        dynamic_import_issues = self._check_dynamic_imports()
        architecture_issues.extend(dynamic_import_issues)

        # 具体的な違反パターンをチェック
        specific_violations = self._check_specific_violations()
        architecture_issues.extend(specific_violations)

        # 副作用の配置違反をチェック
        side_effect_violations = self._check_side_effect_violations()
        architecture_issues.extend(side_effect_violations)

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
            module_deps = dependencies.get(module, set())
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
            'json', 'yaml', 'toml', 'configparser',  # 設定系も制限
            'os', 'sys', 'pathlib', 'glob', 'tempfile', 'io',
            'asyncio', 'threading', 'multiprocessing',
            'logging', 'datetime', 'time',  # 副作用を持つ可能性
            're', 'ast'  # メタプログラミング系
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

    def _check_commented_code(self) -> List[str]:
        """コメントアウトされたコードをチェック"""
        violations = []

        # 対象ファイルを取得
        target_files = self.get_target_files(excluded_categories=["tests"])

        # コードを含む可能性があるキーワード
        code_keywords = {
            'import', 'from', '=', 'def', 'class', 'if', 'for', 'while',
            'try', 'except', 'with', 'return', 'yield', 'raise', 'assert'
        }

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                lines = content.split('\n')
                relative_path = self.get_relative_path(file_path)

                in_docstring = False
                docstring_delimiter = None

                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # docstringの開始/終了を追跡
                    if '"""' in stripped or "'''" in stripped:
                        if not in_docstring:
                            if stripped.count('"""') == 1:
                                in_docstring = True
                                docstring_delimiter = '"""'
                            elif stripped.count("'''") == 1:
                                in_docstring = True
                                docstring_delimiter = "'''"
                        elif docstring_delimiter and docstring_delimiter in stripped:
                            in_docstring = False
                            docstring_delimiter = None

                    # docstring内は許可
                    if in_docstring:
                        continue

                    # # で始まるコメント行をチェック
                    if stripped.startswith('#') and not stripped.startswith('#!/'):
                        comment_content = stripped[1:].strip()

                        # キーワードが含まれているかチェック
                        words = comment_content.split()
                        if (words and any(keyword in comment_content for keyword in code_keywords) and
                            (comment_content.startswith('from ') or
                             comment_content.startswith('import ') or
                             ' = ' in comment_content or
                             comment_content.startswith('def ') or
                             comment_content.startswith('class '))):
                            violations.append(
                                f"{relative_path}:{line_num} コメントアウトされたコード: {stripped}"
                            )

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to check commented code in {file_path}: {e}")

        return violations

    def _check_dynamic_imports(self) -> List[str]:
        """動的インポートをチェック"""
        violations = []

        # 対象ファイルを取得
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

                for node in ast.walk(tree):
                    # importlib.import_module() の使用をチェック
                    if isinstance(node, ast.Call):
                        if (isinstance(node.func, ast.Attribute) and
                            isinstance(node.func.value, ast.Name) and
                            node.func.value.id == 'importlib' and
                            node.func.attr == 'import_module'):
                            violations.append(
                                f"{relative_path}:{node.lineno} 動的インポート禁止: importlib.import_module()"
                            )

                        # __import__() の使用をチェック
                        elif (isinstance(node.func, ast.Name) and
                              node.func.id == '__import__'):
                            violations.append(
                                f"{relative_path}:{node.lineno} 動的インポート禁止: __import__()"
                            )

                    # exec() や eval() でのインポートをチェック
                    elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
                          node.func.id in ['exec', 'eval'] and node.args and
                          isinstance(node.args[0], ast.Constant) and
                          isinstance(node.args[0].value, str) and
                          ('import' in node.args[0].value)):
                        violations.append(
                            f"{relative_path}:{node.lineno} 動的インポート禁止: {node.func.id}() with import"
                        )

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to check dynamic imports in {file_path}: {e}")

        return violations

    def _check_specific_violations(self) -> List[str]:
        """具体的な違反パターンをチェック"""
        violations = []

        # 具体的な違反パターン
        violation_patterns = [
            ('src.configuration', 'src.context', 'configuration層からcontext層への依存'),
            ('src.workflow', 'src.infrastructure', 'workflow層からinfrastructure層への直接依存'),
            ('src.operations', 'src.infrastructure', 'operations層からinfrastructure層への直接依存'),
            ('src.context', 'src.infrastructure', 'context層からinfrastructure層への直接依存')
        ]

        # 対象ファイルを取得
        target_files = self.get_target_files(excluded_categories=["tests"])

        for file_path in target_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                tree = ast.parse(content, filename=file_path)
                relative_path = self.get_relative_path(file_path)

                # ファイルがどの層に属するかを判定
                file_module = self._get_module_name(file_path)
                if not file_module:
                    continue

                for node in ast.walk(tree):
                    # インポート文をチェック
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for from_pattern, to_pattern, description in violation_patterns:
                            if (file_module.startswith(from_pattern) and
                                node.module.startswith(to_pattern)):
                                violations.append(
                                    f"{relative_path}:{node.lineno} {description}: {node.module}"
                                )

                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            for from_pattern, to_pattern, description in violation_patterns:
                                if (file_module.startswith(from_pattern) and
                                    alias.name.startswith(to_pattern)):
                                    violations.append(
                                        f"{relative_path}:{node.lineno} {description}: {alias.name}"
                                    )

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to check specific violations in {file_path}: {e}")

        return violations

    def _check_side_effect_violations(self) -> List[str]:
        """副作用の配置違反をチェック"""
        violations = []

        # 対象ファイルを取得（infrastructure層とscripts/infrastructure以外）
        target_files = self.get_target_files(excluded_categories=["tests"])
        non_infra_files = [
            f for f in target_files
            if '/infrastructure/' not in f and '/scripts/infrastructure/' not in f
        ]

        # 副作用を持つ操作のパターン
        side_effect_patterns = {
            'open': 'ファイルI/O操作',
            'Path.write_text': 'ファイル書き込み操作',
            'Path.read_text': 'ファイル読み込み操作',
            'requests.': 'ネットワーク操作',
            'urllib.': 'ネットワーク操作',
            'subprocess.': 'プロセス実行',
            'os.system': 'システム操作',
            'os.environ': '環境変数の直接アクセス',
            'sys.exit': 'プロセス終了',
            'print(': 'コンソール出力'  # print使用は別チェックと重複するが、より厳密にチェック
        }

        for file_path in non_infra_files:
            try:
                content = self.file_handler.read_text(file_path, encoding='utf-8')
                lines = content.split('\n')
                relative_path = self.get_relative_path(file_path)

                for line_num, line in enumerate(lines, 1):
                    # コメント行は無視
                    if line.strip().startswith('#'):
                        continue

                    for pattern, description in side_effect_patterns.items():
                        if pattern in line:
                            violations.append(
                                f"{relative_path}:{line_num} 副作用配置違反: {description} - {line.strip()}"
                            )

            except Exception as e:
                if self.verbose:
                    self.logger.warning(f"Failed to check side effects in {file_path}: {e}")

        return violations
