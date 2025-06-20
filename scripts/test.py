#!/usr/bin/env python3
"""
統合テスト・品質チェックツール
問題がある場合のみ詳細出力し、問題がない場合は簡潔なサマリーを表示
"""

import argparse
import ast
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple

from infrastructure.command_executor import CommandExecutor, create_command_executor
from infrastructure.file_handler import FileHandler, create_file_handler
from infrastructure.logger import Logger, create_logger


class ProgressSpinner:
    """プログレスを表示するスピナー"""

    def __init__(self, message: str, logger: Logger = None):
        self.message = message
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.running = False
        self.thread = None
        self.logger = logger or create_logger()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, success: bool = True):
        self.running = False
        if self.thread:
            self.thread.join()
        # スピナーを消去して結果を表示
        self.logger.print(f"\r{'✅' if success else '❌'} {self.message}", flush=True)

    def _spin(self):
        i = 0
        while self.running:
            self.logger.print(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message}...", end="", flush=True)
            i += 1
            time.sleep(0.1)


class TestRunner:
    def __init__(self, verbose: bool = False, logger: Logger = None, command_executor: CommandExecutor = None, file_handler: FileHandler = None):
        self.verbose = verbose
        self.logger = logger or create_logger(verbose=verbose)
        self.command_executor = command_executor or create_command_executor()
        self.file_handler = file_handler or create_file_handler()
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner(description, self.logger)
            spinner.start()

        try:
            result = self.command_executor.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )

            success = result.success

            # vultureの場合は特別処理
            if cmd[0] == "vulture" and result.stdout.strip():
                if spinner:
                    spinner.stop(True)  # 未使用コード検出は成功として表示
            else:
                if spinner:
                    spinner.stop(success)

            if not success:
                if self.verbose:
                    self.logger.error(f"{description}")
                    self.logger.debug(f"コマンド: {' '.join(cmd)}")
                    if result.stderr.strip():
                        self.logger.error(f"エラー出力: {result.stderr}")
                    if result.stdout.strip():
                        self.logger.debug(f"標準出力: {result.stdout}")
                # vultureの場合は特別処理（未使用コード検出時は正常終了とみなす）
                if cmd[0] == "vulture" and result.stdout.strip():
                    return True, result.stdout
                # 失敗時は標準出力と標準エラー出力の両方を確認
                combined_output = ""
                if result.stdout.strip():
                    combined_output += result.stdout.strip()
                if result.stderr.strip():
                    if combined_output:
                        combined_output += "\n"
                    combined_output += result.stderr.strip()

                # 何も出力がない場合は終了コードを表示
                if not combined_output:
                    combined_output = f"終了コード: {result.returncode}"

                self.issues.append(f"{description}: {combined_output}")
                return False, combined_output
            if self.verbose:
                self.logger.info(f"{description}")

            return True, result.stdout

        except Exception as e:
            if spinner:
                spinner.stop(False)

            error_msg = f"{description}: {e!s}"
            self.issues.append(error_msg)
            if self.verbose:
                self.logger.error(f"{error_msg}")
            return False, str(e)

    def check_ruff(self) -> bool:
        """Ruffによるコード品質チェック"""
        # まず修正可能な問題を自動修正
        self.run_command(
            ["ruff", "check", "--fix", "--unsafe-fixes"],
            "Ruff自動修正"
        )

        # 残った問題をチェック
        success, output = self.run_command(
            ["ruff", "check"],
            "コード品質チェック (ruff)"
        )

        return success

    def check_quality_scripts(self) -> bool:
        """品質チェックスクリプトを実行"""
        all_passed = True

        # 汎用名チェック
        if self.file_handler.exists("scripts/quality/check_generic_names.py"):
            success, output = self.run_command(
                ["python3", "scripts/quality/check_generic_names.py", "src/"],
                "汎用名チェック"
            )
            all_passed = all_passed and success

        # 実用的品質チェック
        if self.file_handler.exists("scripts/quality/practical_quality_check.py"):
            success, output = self.run_command(
                ["python3", "scripts/quality/practical_quality_check.py"],
                "実用的品質チェック"
            )
            all_passed = all_passed and success
        elif self.file_handler.exists("scripts/quality/functional_quality_check.py"):
            success, output = self.run_command(
                ["python3", "scripts/quality/functional_quality_check.py", "src/"],
                "関数型品質チェック"
            )
            all_passed = all_passed and success

        # アーキテクチャ品質チェック
        if self.file_handler.exists("scripts/quality/architecture_quality_check.py"):
            success, output = self.run_command(
                ["python3", "scripts/quality/architecture_quality_check.py", "src/"],
                "アーキテクチャ品質チェック"
            )
            all_passed = all_passed and success

        return all_passed

    def check_dead_code(self) -> bool:
        """vultureを使用した未使用コード検出"""
        # vultureが利用可能かチェック
        try:
            result = self.command_executor.run(["vulture", "--version"], capture_output=True, text=True)
            if not result.success:
                raise Exception("vulture not available")
        except Exception:
            if not self.verbose:
                self.logger.warning("vultureがインストールされていません（推奨）")
            else:
                self.logger.warning("vultureがインストールされていません（推奨）")
            self.warnings.append("vultureがインストールされていません（推奨）")
            return True  # 未使用コード検出なしでも続行

        success, output = self.run_command(
            ["vulture", "src/", ".vulture_whitelist.py", "--min-confidence", "80"],
            "未使用コード検出"
        )

        # 未使用コードが検出された場合は警告として扱う（エラーではない）
        # vultureは未使用コード検出時に終了コード1を返すが、標準出力に結果があれば正常
        if output.strip():
            # 出力を解析して警告として追加
            dead_code_lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            if dead_code_lines:
                self.warnings.append("未使用コードが検出されました:")
                for line in dead_code_lines[:10]:  # 最大10件表示
                    # ファイルパスを短縮表示
                    if line.startswith('src/'):
                        line = line[4:]  # 'src/'を除去
                    self.warnings.append(f"  {line}")

                if len(dead_code_lines) > 10:
                    self.warnings.append(f"  ... 他{len(dead_code_lines) - 10}件")

        return True  # 警告レベルなので常にTrueを返す

    def check_import_resolution(self) -> bool:
        """インポート解決チェック - ファイル移動・削除で破綻したインポートを検出"""
        import ast
        import glob
        from pathlib import Path

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("インポート解決チェック", self.logger)
            spinner.start()

        try:
            import_issues = []

            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    tree = ast.parse(content, filename=file_path)

                    # import文を解析
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom) and node.module:
                            module = node.module
                            if module.startswith('src.'):
                                # モジュールパスの存在確認
                                # src.context.user_input_parser -> src/context/user_input_parser.py
                                module_path = module.replace('.', '/') + '.py'
                                # または __init__.py での初期化
                                init_path = module.replace('.', '/') + '/__init__.py'

                                if not (Path(module_path).exists() or Path(init_path).exists()):
                                    relative_file = file_path.replace('src/', '') if file_path.startswith('src/') else file_path
                                    import_issues.append(f"{relative_file}: import {module} (モジュールが見つかりません)")

                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name
                                if module.startswith('src.'):
                                    module_path = module.replace('.', '/') + '.py'
                                    init_path = module.replace('.', '/') + '/__init__.py'

                                    if not (Path(module_path).exists() or Path(init_path).exists()):
                                        relative_file = file_path.replace('src/', '') if file_path.startswith('src/') else file_path
                                        import_issues.append(f"{relative_file}: import {module} (モジュールが見つかりません)")

                except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                    # 構文エラーやファイル読み込みエラーは無視
                    continue

            success = len(import_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} インポート解決チェック")

            if import_issues:
                self.issues.append("インポート解決エラーが検出されました:")
                for issue in import_issues[:15]:  # 最大15件表示
                    self.issues.append(f"  {issue}")

                if len(import_issues) > 15:
                    self.issues.append(f"  ... 他{len(import_issues) - 15}件")

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"インポート解決チェックでエラー: {e}")
            if self.verbose:
                self.logger.error(f"インポート解決チェックでエラー: {e}")
            return False

    def quick_smoke_test(self) -> bool:
        """クイックスモークテスト - 基本的な実行可能性をチェック"""
        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("クイックスモークテスト", self.logger)
            spinner.start()

        try:
            # メインモジュールのインポートテスト
            result = self.command_executor.run([
                "python3", "-c",
                "import sys; sys.path.insert(0, '.'); "
                "from src.main import main; print('OK')"
            ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))

            success = result.success

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} クイックスモークテスト")

            if not success:
                error_output = result.stderr.strip() or result.stdout.strip() or f"終了コード: {result.returncode}"
                self.issues.append(f"スモークテスト失敗: {error_output}")

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"スモークテストでエラー: {e}")
            if self.verbose:
                self.logger.error(f"スモークテストでエラー: {e}")
            return False

    def check_naming_conventions(self) -> bool:
        """命名規則チェック"""
        import ast
        import glob
        import re
        from pathlib import Path

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("命名規則チェック", self.logger)
            spinner.start()

        try:
            naming_issues = []

            # 汎用的すぎるファイル名を検出
            generic_filenames = [
                'helpers.py', 'utils.py', 'core.py', 'base.py', 'common.py',
                'misc.py', 'tools.py', 'generic.py', 'data.py', 'info.py'
            ]

            # 抽象的すぎる関数名パターン
            abstract_function_patterns = [
                r'^handle$', r'^process$', r'^manage$', r'^execute$', r'^create$',
                r'^build$', r'^run$', r'^do_', r'^perform_', r'^get$', r'^set$'
            ]

            # 汎用的すぎるクラス名パターン
            generic_class_patterns = [
                r'^Base[A-Z]', r'^Abstract[A-Z]', r'^Generic[A-Z]',
                r'^Manager$', r'^Handler$', r'^Processor$', r'^Helper$'
            ]

            # 無駄なプレフィックスパターン（ファイル名、関数名用）
            useless_prefix_patterns = [
                r'^simple_', r'^pure_', r'^basic_', r'^plain_', r'^raw_',
                r'^common_', r'^general_', r'^standard_', r'^default_',
                r'^normal_', r'^regular_', r'^typical_', r'^ordinary_'
            ]

            # 無駄なプレフィックスパターン（クラス名用 - キャメルケース）
            useless_class_prefix_patterns = [
                r'^Simple[A-Z]', r'^Pure[A-Z]', r'^Basic[A-Z]', r'^Plain[A-Z]', r'^Raw[A-Z]',
                r'^Common[A-Z]', r'^General[A-Z]', r'^Standard[A-Z]', r'^Default[A-Z]',
                r'^Normal[A-Z]', r'^Regular[A-Z]', r'^Typical[A-Z]', r'^Ordinary[A-Z]'
            ]

            for file_path in glob.glob('src/**/*.py', recursive=True):
                file_name = Path(file_path).name
                relative_path = file_path.replace('src/', '')

                # ファイル名チェック
                if file_name in generic_filenames:
                    naming_issues.append(f"汎用的ファイル名: {relative_path}")

                # 無駄なプレフィックスファイル名チェック
                base_filename = file_name.replace('.py', '')
                for pattern in useless_prefix_patterns:
                    if re.match(pattern, base_filename):
                        naming_issues.append(f"無駄なプレフィックスファイル名: {relative_path}")
                        break

                # 長すぎるファイル名チェック（35文字以上）
                if len(file_name) > 35:
                    naming_issues.append(f"長すぎるファイル名: {relative_path} ({len(file_name)}文字)")

                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    tree = ast.parse(content, filename=file_path)

                    # クラス名チェック
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            class_name = node.name
                            # 汎用的クラス名チェック
                            for pattern in generic_class_patterns:
                                if re.match(pattern, class_name):
                                    naming_issues.append(f"汎用的クラス名: {relative_path}:{node.lineno} class {class_name}")
                                    break
                            # 無駄なプレフィックスクラス名チェック
                            for pattern in useless_class_prefix_patterns:
                                if re.match(pattern, class_name):
                                    naming_issues.append(f"無駄なプレフィックスクラス名: {relative_path}:{node.lineno} class {class_name}")
                                    break

                        # 関数名チェック
                        elif isinstance(node, ast.FunctionDef):
                            func_name = node.name
                            # プライベートメソッドやspecialメソッドはスキップ
                            if not func_name.startswith('_'):
                                # 抽象的関数名チェック
                                for pattern in abstract_function_patterns:
                                    if re.match(pattern, func_name):
                                        naming_issues.append(f"抽象的関数名: {relative_path}:{node.lineno} def {func_name}")
                                        break
                                # 無駄なプレフィックス関数名チェック
                                for pattern in useless_prefix_patterns:
                                    if re.match(pattern, func_name):
                                        naming_issues.append(f"無駄なプレフィックス関数名: {relative_path}:{node.lineno} def {func_name}")
                                        break

                except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
                    # 構文エラーやエンコードエラーは無視
                    continue

            if spinner:
                spinner.stop(True)

            if self.verbose:
                self.logger.info("✅ 命名規則チェック")

            # 問題が見つかった場合は警告として追加
            if naming_issues:
                self.warnings.append("命名規則の問題が検出されました:")
                for issue in naming_issues[:15]:  # 最大15件表示
                    self.warnings.append(f"  {issue}")

                if len(naming_issues) > 15:
                    self.warnings.append(f"  ... 他{len(naming_issues) - 15}件")

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.warnings.append(f"命名規則チェックでエラー: {e}")
            if self.verbose:
                self.logger.error(f"命名規則チェックでエラー: {e}")

        return True  # 警告レベルなので常にTrueを返す

    def check_dependency_injection(self) -> bool:
        """依存性注入チェック - 副作用はinfrastructure外で直接使用禁止"""
        import ast
        import glob

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("依存性注入チェック", self.logger)
            spinner.start()

        try:
            injection_issues = []

            # 副作用パターン（直接使用禁止）
            side_effect_patterns = {
                'subprocess': ['run', 'Popen', 'call', 'check_call', 'check_output'],
                'shutil': ['copy', 'copy2', 'copytree', 'move', 'rmtree'],
                'sqlite3': ['connect'],
                'sys': ['stdout.write', 'stderr.write'],
                'os': ['system', 'popen', 'utime', 'chmod', 'chown'],
                'pathlib.Path': ['write_text', 'write_bytes', 'mkdir', 'rmdir', 'unlink'],
                'docker': ['from_env', 'DockerClient'],
                'json': ['dump', 'dumps'],  # ファイル書き込み系のみ
                'yaml': ['dump', 'safe_dump'],
                'toml': ['dump']
            }

            # 許可されたディレクトリ（CLAUDE.mdに従い、infrastructure層全体を許可）
            allowed_dirs = [
                'src/infrastructure/',
                'tests/infrastructure/'
            ]

            for file_path in glob.glob('src/**/*.py', recursive=True):
                # 許可されたディレクトリは除外
                if any(file_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                    continue

                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    tree = ast.parse(content, filename=file_path)

                    relative_path = file_path.replace('src/', '')

                    # インポート文と使用箇所をチェック
                    for node in ast.walk(tree):
                        # from subprocess import run のようなケース
                        if isinstance(node, ast.ImportFrom) and node.module:
                            module = node.module
                            if module in side_effect_patterns:
                                for alias in node.names or []:
                                    if alias.name in side_effect_patterns[module]:
                                        injection_issues.append(
                                            f"{relative_path}:{node.lineno} from {module} import {alias.name} (副作用の直接インポート)"
                                        )

                        # import subprocess のようなケース
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name in side_effect_patterns:
                                    injection_issues.append(
                                        f"{relative_path}:{node.lineno} import {alias.name} (副作用モジュールの直接インポート)"
                                    )

                        # subprocess.run() のような使用
                        elif isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Attribute):
                                # モジュール.メソッド の形式
                                if isinstance(node.func.value, ast.Name):
                                    module_name = node.func.value.id
                                    method_name = node.func.attr
                                    if module_name in side_effect_patterns and method_name in side_effect_patterns[module_name]:
                                        injection_issues.append(
                                            f"{relative_path}:{node.lineno} {module_name}.{method_name}() (副作用の直接使用)"
                                        )
                                # sys.stdout.write のような多段階アクセス
                                elif isinstance(node.func.value, ast.Attribute):
                                    if isinstance(node.func.value.value, ast.Name):
                                        base_module = node.func.value.value.id
                                        attr_chain = f"{node.func.value.attr}.{node.func.attr}"
                                        if base_module in side_effect_patterns and attr_chain in side_effect_patterns[base_module]:
                                            injection_issues.append(
                                                f"{relative_path}:{node.lineno} {base_module}.{attr_chain}() (副作用の直接使用)"
                                            )

                            # 直接関数呼び出し（from import で取り込んだ場合）
                            elif isinstance(node.func, ast.Name):
                                func_name = node.func.id
                                # 各モジュールの関数名をチェック
                                for _module, functions in side_effect_patterns.items():
                                    if func_name in functions:
                                        injection_issues.append(
                                            f"{relative_path}:{node.lineno} {func_name}() (副作用関数の直接使用)"
                                        )

                except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                    # 構文エラーやファイル読み込みエラーは無視
                    continue

            success = len(injection_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} 依存性注入チェック")

            if injection_issues:
                self.issues.append("副作用の直接使用が検出されました（infrastructure層での注入が必要）:")
                for issue in injection_issues[:25]:  # 最大25件表示
                    self.issues.append(f"  {issue}")

                if len(injection_issues) > 25:
                    self.issues.append(f"  ... 他{len(injection_issues) - 25}件")

                return False

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"依存性注入チェックでエラー: {e}")
            if self.verbose:
                self.logger.error(f"依存性注入チェックでエラー: {e}")
            return False

    def check_print_usage(self) -> bool:
        """print使用チェック - loggingディレクトリ配下を除く"""
        import glob
        import re

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("print使用チェック", self.logger)
            spinner.start()

        try:
            print_issues = []

            # print( パターンを検索（コメント除く）
            print_pattern = re.compile(r'\bprint\s*\(')
            comment_pattern = re.compile(r'#.*$')

            for file_path in glob.glob('src/**/*.py', recursive=True):
                # loggingディレクトリ配下は除外
                if '/logging/' in file_path:
                    continue

                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    lines = content.splitlines(keepends=True)

                    for line_num, line in enumerate(lines, 1):
                        # コメントを除去
                        clean_line = comment_pattern.sub('', line)

                        # print( パターンをチェック
                        if print_pattern.search(clean_line):
                            # file=sys.stderrを使用している場合は許可
                            if 'file=sys.stderr' in clean_line:
                                continue
                            relative_path = file_path.replace('src/', '')
                            print_issues.append(f"{relative_path}:{line_num} {clean_line.strip()}")

                except (UnicodeDecodeError, OSError, FileNotFoundError):
                    # ファイル読み込みエラーは無視
                    continue

            success = len(print_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} print使用チェック")

            if print_issues:
                self.issues.append("print()の使用が検出されました（ロギング使用を推奨）:")
                for issue in print_issues[:20]:  # 最大20件表示
                    self.issues.append(f"  {issue}")

                if len(print_issues) > 20:
                    self.issues.append(f"  ... 他{len(print_issues) - 20}件")

                return False

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"print使用チェックでエラー: {e}")
            if self.verbose:
                self.logger.error(f"print使用チェックでエラー: {e}")
            return False

    def check_infrastructure_duplication(self) -> bool:
        """Infrastructure重複生成の検出（CLAUDE.mdルール違反 - main.py以外での生成禁止）"""
        import ast
        import glob

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("Infrastructure重複生成チェック", self.logger)
            spinner.start()

        try:
            duplication_issues = []

            for file_path in glob.glob('src/**/*.py', recursive=True):
                # main.pyは除外
                if file_path.endswith('/main.py') or file_path == 'src/main.py':
                    continue

                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    tree = ast.parse(content, filename=file_path)
                    relative_path = file_path.replace('src/', '')

                    # build_infrastructure()呼び出しを検出
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            # 直接呼び出し: build_infrastructure()
                            if isinstance(node.func, ast.Name) and node.func.id == 'build_infrastructure':
                                duplication_issues.append(f"{relative_path}:{node.lineno} build_infrastructure() の直接呼び出し")

                            # モジュール経由: module.build_infrastructure()
                            elif isinstance(node.func, ast.Attribute) and node.func.attr == 'build_infrastructure':
                                duplication_issues.append(f"{relative_path}:{node.lineno} {self._get_attr_chain(node.func)} の呼び出し")

                    # build_infrastructure のインポートも検出
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and 'build_infrastructure' in node.module:
                                for alias in node.names or []:
                                    if alias.name == 'build_infrastructure':
                                        duplication_issues.append(f"{relative_path}:{node.lineno} build_infrastructure のインポート")
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if 'build_infrastructure' in alias.name:
                                    duplication_issues.append(f"{relative_path}:{node.lineno} {alias.name} のインポート")

                except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                    continue

            success = len(duplication_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} Infrastructure重複生成チェック")

            if duplication_issues:
                self.issues.append("Infrastructure重複生成が検出されました（CLAUDE.mdルール違反 - すべてmain.pyから注入する）:")
                for issue in duplication_issues:
                    self.issues.append(f"  {issue}")

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"Infrastructure重複生成チェックでエラー: {e}")
            return False

    def _get_attr_chain(self, node: ast.Attribute) -> str:
        """属性チェーンを文字列として取得"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        if isinstance(node.value, ast.Attribute):
            return f"{self._get_attr_chain(node.value)}.{node.attr}"
        return f"<expr>.{node.attr}"

    def check_fallback_patterns(self) -> bool:
        """フォールバック処理の検出（CLAUDE.mdルール違反 - エラー隠蔽防止）"""
        import ast
        import glob

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("フォールバック処理チェック", self.logger)
            spinner.start()

        try:
            fallback_issues = []

            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    tree = ast.parse(content, filename=file_path)
                    relative_path = file_path.replace('src/', '')

                    # AST解析による各パターンの検知
                    for node in ast.walk(tree):
                        # 1. try-except でのフォールバック検知
                        if isinstance(node, ast.Try):
                            issues = self._check_try_except_fallback(node, relative_path, content)
                            fallback_issues.extend(issues)

                        # 2. or演算子でのフォールバック検知
                        elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                            issues = self._check_or_fallback(node, relative_path, content)
                            fallback_issues.extend(issues)

                        # 3. 条件式(ternary)でのフォールバック検知
                        elif isinstance(node, ast.IfExp):
                            issues = self._check_ternary_fallback(node, relative_path, content)
                            fallback_issues.extend(issues)

                        # 4. if-None チェックでのフォールバック検知
                        elif isinstance(node, ast.If):
                            issues = self._check_none_fallback(node, relative_path, content)
                            fallback_issues.extend(issues)

                except (SyntaxError, UnicodeDecodeError, OSError, FileNotFoundError):
                    continue

            # スマート分類による誤検出フィルタリング
            filtered_issues = self._filter_legitimate_patterns(fallback_issues)
            success = len(filtered_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} フォールバック処理チェック")

            if filtered_issues:
                self.issues.append("フォールバック処理が検出されました（CLAUDE.mdルール違反 - エラー隠蔽防止）:")
                for issue in filtered_issues[:20]:
                    self.issues.append(f"  {issue}")

                if len(filtered_issues) > 20:
                    self.issues.append(f"  ... 他{len(filtered_issues) - 20}件")

            # 検出統計を表示
            if self.verbose and fallback_issues:
                total_detected = len(fallback_issues)
                filtered_out = total_detected - len(filtered_issues)
                self.logger.info(f"検出統計: 総数{total_detected}件, 除外{filtered_out}件, 問題{len(filtered_issues)}件")

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"フォールバック処理チェックでエラー: {e}")
            return False

    def _check_try_except_fallback(self, node: ast.Try, file_path: str, content: str) -> list:
        """try-except でのフォールバック処理を検知"""
        issues = []
        content_lines = content.splitlines()

        for handler in node.handlers:
            # except節での代入（フォールバック値設定）を検知
            for stmt in handler.body:
                if isinstance(stmt, ast.Assign):
                    # 具体的な値の代入（リテラル、定数など）
                    if self._is_fallback_value(stmt.value):
                        context = self._get_code_context(content_lines, stmt.lineno)
                        severity = self._determine_severity(file_path, stmt.lineno, context, 'try_except_assign')
                        issues.append({
                            'type': 'try_except_assign',
                            'location': f"{file_path}:{stmt.lineno}",
                            'message': 'try-except でのフォールバック代入',
                            'severity': severity,
                            'context': context
                        })

                elif isinstance(stmt, ast.Return) and stmt.value and self._is_fallback_value(stmt.value):
                    # return文での具体的な値返却
                    context = self._get_code_context(content_lines, stmt.lineno)
                    severity = self._determine_severity(file_path, stmt.lineno, context, 'try_except_return')
                    issues.append({
                        'type': 'try_except_return',
                        'location': f"{file_path}:{stmt.lineno}",
                        'message': 'try-except でのフォールバック return',
                        'severity': severity,
                        'context': context
                    })

        return issues

    def _check_or_fallback(self, node: ast.BoolOp, file_path: str, content: str) -> list:
        """or演算子でのフォールバック処理を検知"""
        issues = []
        content_lines = content.splitlines()

        # A or B の形で、Bが具体的な値（フォールバック値）の場合
        if len(node.values) >= 2:
            last_value = node.values[-1]
            if self._is_fallback_value(last_value):
                context = self._get_code_context(content_lines, node.lineno)
                severity = self._determine_severity(file_path, node.lineno, context, 'or_fallback')
                issues.append({
                    'type': 'or_fallback',
                    'location': f"{file_path}:{node.lineno}",
                    'message': 'or演算子でのフォールバック',
                    'severity': severity,
                    'context': context
                })

        return issues

    def _check_ternary_fallback(self, node: ast.IfExp, file_path: str, content: str) -> list:
        """条件式でのフォールバック処理を検知"""
        issues = []
        content_lines = content.splitlines()

        # A if condition else B の形で、BまたはAが具体的な値の場合
        if self._is_fallback_value(node.orelse):
            context = self._get_code_context(content_lines, node.lineno)
            severity = self._determine_severity(file_path, node.lineno, context, 'ternary_else')
            issues.append({
                'type': 'ternary_else',
                'location': f"{file_path}:{node.lineno}",
                'message': '条件式でのフォールバック (else節)',
                'severity': severity,
                'context': context
            })
        elif self._is_fallback_value(node.body):
            context = self._get_code_context(content_lines, node.lineno)
            severity = self._determine_severity(file_path, node.lineno, context, 'ternary_then')
            issues.append({
                'type': 'ternary_then',
                'location': f"{file_path}:{node.lineno}",
                'message': '条件式でのフォールバック (then節)',
                'severity': severity,
                'context': context
            })

        return issues

    def _check_none_fallback(self, node: ast.If, file_path: str, content: str) -> list:
        """if-None チェックでのフォールバック処理を検知"""
        issues = []
        content_lines = content.splitlines()

        # if var is None: var = default の形を検知
        if (isinstance(node.test, ast.Compare) and
            any(isinstance(op, (ast.Is, ast.Eq)) for op in node.test.ops) and
            any(isinstance(comp, ast.Constant) and comp.value is None
                for comp in node.test.comparators)):
            # None チェック後の代入を検知
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and self._is_fallback_value(stmt.value):
                    context = self._get_code_context(content_lines, stmt.lineno)
                    severity = self._determine_severity(file_path, stmt.lineno, context, 'none_check')
                    issues.append({
                        'type': 'none_check',
                        'location': f"{file_path}:{stmt.lineno}",
                        'message': 'None チェックでのフォールバック',
                        'severity': severity,
                        'context': context
                    })

        return issues

    def _is_fallback_value(self, node: ast.AST) -> bool:
        """フォールバック値として使われる可能性のある値を判定"""

        # リテラル値（文字列、数値、リスト、辞書など）
        if isinstance(node, ast.Constant):
            return True

        # 空のコンテナ
        if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.Tuple)):
            if hasattr(node, 'elts'):
                return len(node.elts) == 0
            if hasattr(node, 'keys'):
                return len(node.keys) == 0
            return True

        # よくあるフォールバック関数名
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fallback_function_names = {
                'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'bool',
                'get_default', 'create_default', 'fallback', 'default_value'
            }
            if node.func.id in fallback_function_names:
                return True

        # 明らかなフォールバック変数名
        if isinstance(node, ast.Name):
            fallback_var_names = {
                'default', 'fallback', 'default_value', 'fallback_value',
                'empty_dict', 'empty_list', 'none_value'
            }
            if node.id in fallback_var_names:
                return True

        return False

    def _get_code_context(self, content_lines: list, line_num: int) -> str:
        """指定行の前後のコードコンテキストを取得"""
        try:
            start = max(0, line_num - 3)
            end = min(len(content_lines), line_num + 2)
            context_lines = []
            for i in range(start, end):
                prefix = ">>> " if i == line_num - 1 else "    "
                context_lines.append(f"{prefix}{content_lines[i].strip()}")
            return "\n".join(context_lines)
        except (IndexError, TypeError):
            return ""

    def _determine_severity(self, file_path: str, line_num: int, context: str, pattern_type: str) -> str:
        """コンテキスト分析による重要度判定"""
        # 技術的に必要なパターンの自動識別
        legitimate_patterns = {
            'lazy_import': r'from .* import',
            'di_resolution': r'resolve\(.*DIKey',
            'pathlib_control': r'\.relative_to\(',
            'sqlite_null': r'row\[0\].*if.*else',
            'default_assignment': r'\w+\s*=\s*\w+\s*or\s*',
            'dummy_logger': r'DummyLogger',
            'compatibility': r'互換性.*維持'
        }

        # infrastructure層での特別処理
        if 'infrastructure' in file_path:
            for pattern_name, pattern in legitimate_patterns.items():
                if pattern_name in context.lower() or any(p in context for p in pattern.split('|') if '|' in pattern):
                    return 'ALLOWED'

            # DI関連のフォールバック
            if 'container' in context and 'resolve' in context:
                return 'ALLOWED'

            # SQLite NULL処理
            if 'sqlite' in file_path and ('row[0]' in context or 'None' in context):
                return 'ALLOWED'

            # pathlib制御フロー
            if 'path' in file_path and 'relative_to' in context:
                return 'ALLOWED'

        # 問題のあるパターンの検出
        problematic_patterns = {
            'error_hiding': r'except.*:\s*(pass|return False)',
            'broad_except': r'except Exception:\s*return',
            'silent_fail': r'except.*:\s*$'
        }

        for pattern_name, _pattern in problematic_patterns.items():
            if pattern_name in context.lower():
                return 'ERROR'

        # デフォルト判定
        if pattern_type in ['try_except_assign', 'try_except_return']:
            return 'WARNING'
        return 'WARNING'

    def _filter_legitimate_patterns(self, issues: list) -> list:
        """技術的に必要なパターンをフィルタリング"""
        filtered_issues = []

        for issue in issues:
            if isinstance(issue, dict):
                if issue.get('severity') == 'ALLOWED':
                    continue
                if issue.get('severity') == 'ERROR':
                    filtered_issues.append(f"[ERROR] {issue['location']} {issue['message']}")
                elif issue.get('severity') == 'WARNING':
                    filtered_issues.append(f"[WARNING] {issue['location']} {issue['message']}")
                else:
                    filtered_issues.append(f"{issue['location']} {issue['message']}")
            else:
                # 旧形式のissue（文字列）
                filtered_issues.append(issue)

        return filtered_issues

    def _is_legitimate_pattern(self, node: ast.AST, context: str) -> bool:
        """正当な使用パターンかを判定"""

        # 1. ロギング・デバッグ用途
        if 'log' in context.lower() or 'debug' in context.lower():
            return True

        # 2. テストコード
        if '/test' in context or 'test_' in context:
            return True

        # 3. 初期化処理（ただし設定値は除く）
        if 'init' in context.lower() and 'config' not in context.lower():
            return True

        # 4. 型変換・キャスト
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            type_functions = {'str', 'int', 'float', 'bool', 'list', 'dict', 'set'}
            if node.func.id in type_functions and len(node.args) <= 1:
                return True

        return False

    def check_dict_get_usage(self, auto_convert: bool = False) -> bool:
        """dict.get()使用チェック - エラー隠蔽の温床となるため禁止（フォールバック対応禁止）"""
        import glob
        import re

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("dict.get()使用チェック", self.logger)
            spinner.start()

        try:
            dict_get_issues = []

            # .get( パターンを検索（コメント除く）
            get_pattern = re.compile(r'\.get\(')
            comment_pattern = re.compile(r'#.*$')

            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    lines = content.splitlines(keepends=True)

                    for line_num, line in enumerate(lines, 1):
                        # コメントを除去
                        clean_line = comment_pattern.sub('', line)

                        # .get( パターンをチェック
                        if get_pattern.search(clean_line):
                            relative_path = file_path.replace('src/', '')
                            dict_get_issues.append(f"{relative_path}:{line_num} {clean_line.strip()}")

                except (UnicodeDecodeError, OSError, FileNotFoundError):
                    # ファイル読み込みエラーは無視
                    continue

            success = len(dict_get_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} dict.get()使用チェック")

            if dict_get_issues:
                # 自動変換を実行
                if self._auto_convert_dict_get() and not auto_convert:  # 無限ループ防止
                    # 変換成功時のみ再チェック（1回のみ）
                    return self.check_dict_get_usage(auto_convert=True)

                # 変換失敗または再チェック時は従来のエラー表示
                self.issues.append("dict.get()の使用が検出されました（エラー隠蔽防止・フォールバック対応禁止のため使用禁止）:")
                for issue in dict_get_issues[:20]:  # 最大20件表示
                    self.issues.append(f"  {issue}")

                if len(dict_get_issues) > 20:
                    self.issues.append(f"  ... 他{len(dict_get_issues) - 20}件")

                return False

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"dict.get()使用チェックでエラー: {e}")
            if self.verbose:
                self.logger.error(f"dict.get()使用チェックでエラー: {e}")
            return False

    def _auto_convert_dict_get(self) -> bool:
        """dict.get()を自動変換"""
        self.logger.info("🔧 dict.get()の自動変換を実行中...")

        try:
            result = self.command_executor.run([
                "python3", "scripts/quality/convert_dict_get.py", "src/"
            ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))

            if result.success:
                self.logger.info("✅ dict.get()の自動変換が完了しました")
                if result.stdout.strip():
                    self.logger.info("変換結果:")
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.logger.info(f"   {line}")
                return True
            self.logger.error("❌ dict.get()の自動変換中にエラーが発生しました")
            if result.stderr.strip():
                self.logger.error(f"エラー: {result.stderr}")
            return False

        except Exception as e:
            self.logger.error(f"dict.get()の自動変換でエラー: {e}")
            return False

    def check_types(self) -> bool:
        """型チェック (mypy)"""
        # mypyが利用可能かチェック
        try:
            result = self.command_executor.run(["mypy", "--version"], capture_output=True, text=True)
            if not result.success:
                raise Exception("mypy not available")
        except Exception:
            if not self.verbose:
                self.logger.warning("mypyがインストールされていません（推奨）")
            else:
                self.logger.warning("mypyがインストールされていません（推奨）")
            self.warnings.append("mypyがインストールされていません（推奨）")
            return True  # 型チェックなしでも続行

        return self.run_command(
            ["mypy", "src/", "--no-error-summary"],
            "型チェック"
        )[0]

    def check_syntax(self) -> bool:
        """基本構文チェック"""
        import ast
        import glob

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("構文チェック", self.logger)
            spinner.start()

        try:
            syntax_errors = []
            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    content = self.file_handler.read_text(file_path, encoding='utf-8')
                    ast.parse(content, filename=file_path)
                except SyntaxError as e:
                    syntax_errors.append(f'{file_path}:{e.lineno}: {e.msg}')
                except FileNotFoundError:
                    # ファイルが見つからない場合は無視
                    continue
                except Exception as e:
                    syntax_errors.append(f'{file_path}: {e}')

            success = len(syntax_errors) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                self.logger.info(f"{'✅' if success else '❌'} 構文チェック")

            if syntax_errors:
                self.issues.extend(syntax_errors)
                return False
            return True

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"構文チェック: {e}")
            return False

    def run_tests(self, pytest_args: List[str], no_coverage: bool = False, html_coverage: bool = False) -> bool:
        """pytest実行"""
        cmd = ["pytest"]

        if html_coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        elif not no_coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        # 失敗したテストの詳細を表示するための設定
        cmd.extend(["--tb=short", "-v"])
        cmd.extend(pytest_args)

        # 詳細モードでは従来通り、非詳細モードでは実行中テストを表示
        if self.verbose:
            success, output = self.run_command(cmd, "テスト実行")
        else:
            success, output = self._run_tests_with_live_progress(cmd)

        # テスト失敗時は失敗したテストのみを抽出して表示
        if not success and output:
            self._extract_failed_tests(output)

        # カバレッジ詳細分析（低網羅率のファイルのみ）
        if not no_coverage and output:
            self._analyze_coverage(output)

        return success

    def _run_tests_with_live_progress(self, cmd: List[str]) -> Tuple[bool, str]:
        """テスト実行中に現在のテストを改行せずに表示"""

        try:
            # CommandExecutorを使用してテストを実行
            # ライブプログレス表示のため、CommandExecutorの結果を使用
            result = self.command_executor.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )

            # プログレス表示
            self.logger.print("🧪 テスト実行", end="", flush=True)

            # 簡単なプログレス表示（実際のライブプログレスは省略）
            import time
            for _i in range(3):
                time.sleep(0.1)
                self.logger.print(".", end="", flush=True)

            success = result.success
            output = result.stdout

            # 最終結果を表示
            self.logger.print(f"\r{'✅' if success else '❌'} テスト実行".ljust(90), flush=True)

            return success, output

        except Exception as e:
            # プログレス表示
            self.logger.print("\r❌ テスト実行", flush=True)
            self.issues.append(f"テスト実行でエラー: {e}")
            return False, str(e)

    def _extract_failed_tests(self, output: str) -> None:
        """失敗したテストの詳細を抽出して表示"""
        lines = output.split('\n')
        failed_tests = []
        current_failure = None
        in_failure_section = False
        in_short_summary = False

        for line in lines:
            # FAILURES セクションの開始
            if line.strip().startswith('=') and 'FAILURES' in line:
                in_failure_section = True
                continue

            # 短いサマリーセクションの開始
            if line.strip().startswith('=') and 'short test summary' in line.lower():
                in_short_summary = True
                continue

            # セクションの終了
            if line.strip().startswith('=') and not ('FAILURES' in line or 'short test summary' in line.lower()):
                in_failure_section = False
                in_short_summary = False
                if current_failure:
                    failed_tests.append(current_failure)
                    current_failure = None
                continue

            # 失敗したテストの詳細を収集
            if in_failure_section:
                if line.startswith('_') and '::' in line:
                    # 新しい失敗テストの開始
                    if current_failure:
                        failed_tests.append(current_failure)
                    current_failure = {'name': line.strip('_ '), 'details': []}
                elif current_failure and line.strip():
                    current_failure['details'].append(line)

            # 短いサマリーから失敗したテスト名を収集
            if in_short_summary and ('FAILED' in line or 'ERROR' in line):
                test_name = line.split()[1] if len(line.split()) > 1 else line.strip()
                failed_tests.append({'name': test_name, 'summary': line.strip()})

        # 最後の失敗テストを追加
        if current_failure:
            failed_tests.append(current_failure)

        # 失敗したテストの情報を警告として追加
        if failed_tests:
            self.warnings.append("失敗したテスト:")
            for test in failed_tests:
                if 'summary' in test:
                    # 短いサマリーからの情報
                    self.warnings.append(f"  {test['summary']}")
                else:
                    # 詳細な失敗情報
                    self.warnings.append(f"  {test['name']}")
                    if test.get('details'):
                        # 最も重要な部分だけを表示（最初の数行とエラー行）
                        important_lines = []
                        for detail in test['details'][:10]:  # 最大10行
                            if any(keyword in detail.lower() for keyword in ['error', 'assert', 'exception', 'failed', '>']):
                                important_lines.append(f"    {detail.strip()}")
                        if important_lines:
                            self.warnings.extend(important_lines[:5])  # 最大5行

    def _analyze_coverage(self, output: str) -> None:
        """カバレッジ詳細分析（低網羅率のファイルのみ表示）"""
        lines = output.split('\n')
        low_coverage_files = []

        # カバレッジ情報を解析
        for line in lines:
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue

            # TOTALライン（総合カバレッジ）
            if line.startswith('TOTAL'):
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            int(part[:-1])
                        except ValueError:
                            continue
                        break
            # 個別ファイルのカバレッジ（80%未満のみ収集）
            elif line.startswith('src/') and '%' in line:
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[0]
                    # パーセンテージを探す
                    for part in parts[1:]:
                        if part.endswith('%'):
                            try:
                                coverage = int(part[:-1])
                                if coverage < 80:  # 80%未満のみ収集
                                    low_coverage_files.append((file_path, coverage))
                            except ValueError:
                                continue
                            break

        # 低カバレッジファイルのみ表示（総合カバレッジは表示しない）
        if low_coverage_files:
            # カバレッジが低い順にソート
            low_coverage_files.sort(key=lambda x: x[1])
            self.warnings.append("カバレッジが低いファイル（80%未満）:")
            for file_path, coverage in low_coverage_files[:15]:  # 最大15件
                # ファイル名を短縮表示
                short_path = file_path.replace('src/', '')
                self.warnings.append(f"  {short_path}: {coverage}%")

            if len(low_coverage_files) > 15:
                self.warnings.append(f"  ... 他{len(low_coverage_files) - 15}件")

    def print_summary(self):
        """実行結果のサマリーを表示"""
        if not self.issues and not self.warnings:
            self.logger.info("✅ 全ての品質チェックが正常に完了しました")
            return

        if self.warnings:
            self.logger.warning("⚠️  警告:")
            for warning in self.warnings:
                self.logger.warning(f"   {warning}")

        if self.issues:
            self.logger.error("❌ 修正が必要な問題:")
            for issue in self.issues:
                self.logger.error(f"   {issue}")
            sys.exit(1)


def main(file_handler: FileHandler = None):
    parser = argparse.ArgumentParser(description="統合テスト・品質チェックツール")
    parser.add_argument("--no-cov", action="store_true", help="カバレッジなしでテスト実行")
    parser.add_argument("--html", action="store_true", help="HTMLカバレッジレポート生成")
    parser.add_argument("--no-ruff", action="store_true", help="Ruffスキップ")
    parser.add_argument("--no-deadcode", action="store_true", help="未使用コード検出スキップ")
    parser.add_argument("--no-naming", action="store_true", help="命名規則チェックスキップ")
    parser.add_argument("--no-import-check", action="store_true", help="インポート解決チェックスキップ")
    parser.add_argument("--no-smoke-test", action="store_true", help="スモークテストスキップ")
    parser.add_argument("--no-dict-get-check", action="store_true", help="dict.get()使用チェックスキップ")
    parser.add_argument("--auto-convert-dict-get", action="store_true", help="dict.get()検出時に自動変換実行")
    parser.add_argument("--no-fallback-check", action="store_true", help="フォールバック処理チェックスキップ")
    parser.add_argument("--check-only", action="store_true", help="高速チェック（テストなし）")
    parser.add_argument("--coverage-only", action="store_true", help="カバレッジレポートのみ表示")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("pytest_args", nargs="*", help="pytestに渡す引数")

    args = parser.parse_args()

    # ロガーを初期化
    logger = create_logger(verbose=args.verbose)

    # FileHandlerを初期化
    if file_handler is None:
        file_handler = create_file_handler()

    # 競合オプションのチェック
    if args.no_cov and args.html:
        logger.error("エラー: --no-cov と --html は同時に使用できません")
        sys.exit(1)

    if args.coverage_only and args.no_cov:
        logger.error("エラー: --coverage-only と --no-cov は同時に使用できません")
        sys.exit(1)

    # CommandExecutorを初期化
    command_executor = create_command_executor()

    runner = TestRunner(verbose=args.verbose, logger=logger, command_executor=command_executor, file_handler=file_handler)

    # カバレッジレポートのみモード
    if args.coverage_only:
        runner.run_tests(args.pytest_args, False, args.html)
        runner.print_summary()
        return

    # 基本チェック（構文・インポート・スモークテスト）
    runner.check_syntax()
    if not args.no_import_check:
        runner.check_import_resolution()
    if not args.no_smoke_test:
        runner.quick_smoke_test()

    # コード品質チェック
    if not args.no_ruff:
        runner.check_ruff()
        runner.check_quality_scripts()

    # 未使用コード検出
    if not args.no_deadcode:
        runner.check_dead_code()

    # 命名規則チェック
    if not args.no_naming:
        runner.check_naming_conventions()

    # 依存性注入チェック
    runner.check_dependency_injection()

    # Infrastructure重複生成チェック
    runner.check_infrastructure_duplication()

    # print使用チェック
    runner.check_print_usage()

    # dict.get()使用チェック
    if not args.no_dict_get_check:
        runner.check_dict_get_usage(auto_convert=args.auto_convert_dict_get)

    # フォールバック処理チェック
    if not args.no_fallback_check:
        runner.check_fallback_patterns()

    # check-onlyモード
    if args.check_only:
        runner.check_types()
        runner.print_summary()
        return

    # テスト実行
    runner.run_tests(args.pytest_args, args.no_cov, args.html)

    # サマリー表示
    runner.print_summary()


if __name__ == "__main__":
    main()
