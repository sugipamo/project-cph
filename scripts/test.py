#!/usr/bin/env python3
"""
統合テスト・品質チェックツール
問題がある場合のみ詳細出力し、問題がない場合は簡潔なサマリーを表示
"""

import argparse
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple


class ProgressSpinner:
    """プログレスを表示するスピナー"""

    def __init__(self, message: str):
        self.message = message
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.running = False
        self.thread = None

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
        print(f"\r{'✅' if success else '❌'} {self.message}", flush=True)

    def _spin(self):
        i = 0
        while self.running:
            print(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message}...", end="", flush=True)
            i += 1
            time.sleep(0.1)


class TestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner(description)
            spinner.start()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            success = result.returncode == 0

            # vultureの場合は特別処理
            if cmd[0] == "vulture" and result.stdout.strip():
                if spinner:
                    spinner.stop(True)  # 未使用コード検出は成功として表示
            else:
                if spinner:
                    spinner.stop(success)

            if not success:
                if self.verbose:
                    print(f"❌ {description}")
                    print(f"   コマンド: {' '.join(cmd)}")
                    if result.stderr.strip():
                        print(f"   エラー出力: {result.stderr}")
                    if result.stdout.strip():
                        print(f"   標準出力: {result.stdout}")
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
                print(f"✅ {description}")

            return True, result.stdout

        except Exception as e:
            if spinner:
                spinner.stop(False)

            error_msg = f"{description}: {e!s}"
            self.issues.append(error_msg)
            if self.verbose:
                print(f"❌ {error_msg}")
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
        if Path("scripts/quality/check_generic_names.py").exists():
            success, output = self.run_command(
                ["python3", "scripts/quality/check_generic_names.py", "src/"],
                "汎用名チェック"
            )
            all_passed = all_passed and success

        # 実用的品質チェック
        if Path("scripts/quality/practical_quality_check.py").exists():
            success, output = self.run_command(
                ["python3", "scripts/quality/practical_quality_check.py"],
                "実用的品質チェック"
            )
            all_passed = all_passed and success
        elif Path("scripts/quality/functional_quality_check.py").exists():
            success, output = self.run_command(
                ["python3", "scripts/quality/functional_quality_check.py", "src/"],
                "関数型品質チェック"
            )
            all_passed = all_passed and success

        # アーキテクチャ品質チェック
        if Path("scripts/quality/architecture_quality_check.py").exists():
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
            subprocess.run(["vulture", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            if not self.verbose:
                print("⚠️  vultureがインストールされていません（推奨）")
            else:
                print("⚠️  vultureがインストールされていません（推奨）")
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
            spinner = ProgressSpinner("インポート解決チェック")
            spinner.start()

        try:
            import_issues = []

            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
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

                except (SyntaxError, UnicodeDecodeError, OSError):
                    # 構文エラーやファイル読み込みエラーは無視
                    continue

            success = len(import_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} インポート解決チェック")

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
                print(f"❌ インポート解決チェックでエラー: {e}")
            return False

    def quick_smoke_test(self) -> bool:
        """クイックスモークテスト - 基本的な実行可能性をチェック"""
        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("クイックスモークテスト")
            spinner.start()

        try:
            # メインモジュールのインポートテスト
            result = subprocess.run([
                "python3", "-c",
                "import sys; sys.path.insert(0, '.'); "
                "from src.main import main; print('OK')"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

            success = result.returncode == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} クイックスモークテスト")

            if not success:
                error_output = result.stderr.strip() or result.stdout.strip() or f"終了コード: {result.returncode}"
                self.issues.append(f"スモークテスト失敗: {error_output}")

            return success

        except Exception as e:
            if spinner:
                spinner.stop(False)
            self.issues.append(f"スモークテストでエラー: {e}")
            if self.verbose:
                print(f"❌ スモークテストでエラー: {e}")
            return False

    def check_naming_conventions(self) -> bool:
        """命名規則チェック"""
        import ast
        import glob
        import re
        from pathlib import Path

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("命名規則チェック")
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
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
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

                except (SyntaxError, UnicodeDecodeError):
                    # 構文エラーやエンコードエラーは無視
                    continue

            if spinner:
                spinner.stop(True)

            if self.verbose:
                print("✅ 命名規則チェック")

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
                print(f"❌ 命名規則チェックでエラー: {e}")

        return True  # 警告レベルなので常にTrueを返す

    def check_dependency_injection(self) -> bool:
        """依存性注入チェック - 副作用はinfrastructure外で直接使用禁止"""
        import ast
        import glob
        from pathlib import Path

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("依存性注入チェック")
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

            # 許可されたディレクトリ
            allowed_dirs = [
                'src/infrastructure/drivers/',
                'tests/infrastructure/',
                'src/infrastructure/config/'
            ]

            for file_path in glob.glob('src/**/*.py', recursive=True):
                # 許可されたディレクトリは除外
                if any(file_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                    continue

                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
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
                                for module, functions in side_effect_patterns.items():
                                    if func_name in functions:
                                        injection_issues.append(
                                            f"{relative_path}:{node.lineno} {func_name}() (副作用関数の直接使用)"
                                        )

                except (SyntaxError, UnicodeDecodeError, OSError):
                    # 構文エラーやファイル読み込みエラーは無視
                    continue

            success = len(injection_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} 依存性注入チェック")

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
                print(f"❌ 依存性注入チェックでエラー: {e}")
            return False

    def check_print_usage(self) -> bool:
        """print使用チェック - loggingディレクトリ配下を除く"""
        import glob
        import re

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("print使用チェック")
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
                    with open(file_path, encoding='utf-8') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        # コメントを除去
                        clean_line = comment_pattern.sub('', line)

                        # print( パターンをチェック
                        if print_pattern.search(clean_line):
                            relative_path = file_path.replace('src/', '')
                            print_issues.append(f"{relative_path}:{line_num} {clean_line.strip()}")

                except (UnicodeDecodeError, OSError):
                    # ファイル読み込みエラーは無視
                    continue

            success = len(print_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} print使用チェック")

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
                print(f"❌ print使用チェックでエラー: {e}")
            return False

    def check_dict_get_usage(self, auto_convert: bool = False) -> bool:
        """dict.get()使用チェック - エラー隠蔽の温床となるため禁止（フォールバック対応禁止）"""
        import glob
        import re

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner("dict.get()使用チェック")
            spinner.start()

        try:
            dict_get_issues = []

            # .get( パターンを検索（コメント除く）
            get_pattern = re.compile(r'\.get\(')
            comment_pattern = re.compile(r'#.*$')

            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        # コメントを除去
                        clean_line = comment_pattern.sub('', line)

                        # .get( パターンをチェック
                        if get_pattern.search(clean_line):
                            relative_path = file_path.replace('src/', '')
                            dict_get_issues.append(f"{relative_path}:{line_num} {clean_line.strip()}")

                except (UnicodeDecodeError, OSError):
                    # ファイル読み込みエラーは無視
                    continue

            success = len(dict_get_issues) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} dict.get()使用チェック")

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
                print(f"❌ dict.get()使用チェックでエラー: {e}")
            return False

    def _auto_convert_dict_get(self) -> bool:
        """dict.get()を自動変換"""
        print("🔧 dict.get()の自動変換を実行中...")

        try:
            result = subprocess.run([
                "python3", "scripts/quality/convert_dict_get.py", "src/"
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)

            if result.returncode == 0:
                print("✅ dict.get()の自動変換が完了しました")
                if result.stdout.strip():
                    print("変換結果:")
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            print(f"   {line}")
                return True
            print("❌ dict.get()の自動変換中にエラーが発生しました")
            if result.stderr.strip():
                print(f"エラー: {result.stderr}")
            return False

        except Exception as e:
            print(f"❌ dict.get()の自動変換でエラー: {e}")
            return False

    def check_types(self) -> bool:
        """型チェック (mypy)"""
        # mypyが利用可能かチェック
        try:
            subprocess.run(["mypy", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            if not self.verbose:
                print("⚠️  mypyがインストールされていません（推奨）")
            else:
                print("⚠️  mypyがインストールされていません（推奨）")
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
            spinner = ProgressSpinner("構文チェック")
            spinner.start()

        try:
            syntax_errors = []
            for file_path in glob.glob('src/**/*.py', recursive=True):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        ast.parse(f.read(), filename=file_path)
                except SyntaxError as e:
                    syntax_errors.append(f'{file_path}:{e.lineno}: {e.msg}')
                except Exception as e:
                    syntax_errors.append(f'{file_path}: {e}')

            success = len(syntax_errors) == 0

            if spinner:
                spinner.stop(success)
            elif self.verbose:
                print(f"{'✅' if success else '❌'} 構文チェック")

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
        import re

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,
                universal_newlines=True,
                cwd=Path(__file__).parent.parent
            )

            output_lines = []
            # シンプルなテスト名検出パターン
            test_pattern = re.compile(r'(\S+::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)')

            print("🧪 テスト実行", end="", flush=True)

            last_test = ""

            for line in iter(process.stdout.readline, ''):
                output_lines.append(line)
                line_stripped = line.strip()

                # テスト名検出
                match = test_pattern.search(line_stripped)
                if match:
                    test_name = match.group(1)

                    # 重複を避ける
                    if test_name == last_test:
                        continue
                    last_test = test_name

                    # テスト名を短縮表示
                    if '::' in test_name:
                        parts = test_name.split('::')
                        file_part = parts[0].split('/')[-1]
                        if file_part.endswith('.py'):
                            file_part = file_part[:-3]
                        test_part = parts[-1]
                        short_name = f"{file_part}::{test_part}"
                    else:
                        short_name = test_name

                    # 長い名前を切り詰め
                    if len(short_name) > 50:
                        short_name = short_name[:47] + "..."

                    print(f"\r🧪 テスト実行: {short_name}".ljust(90), end="", flush=True)

            process.wait()
            output = ''.join(output_lines)
            success = process.returncode == 0

            # 最終結果を表示
            print(f"\r{'✅' if success else '❌'} テスト実行".ljust(90), flush=True)

            return success, output

        except Exception as e:
            print("\r❌ テスト実行", flush=True)
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
            print("✅ 全ての品質チェックが正常に完了しました")
            return

        if self.warnings:
            print("⚠️  警告:")
            for warning in self.warnings:
                print(f"   {warning}")

        if self.issues:
            print("❌ 修正が必要な問題:")
            for issue in self.issues:
                print(f"   {issue}")
            sys.exit(1)


def main():
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
    parser.add_argument("--check-only", action="store_true", help="高速チェック（テストなし）")
    parser.add_argument("--coverage-only", action="store_true", help="カバレッジレポートのみ表示")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("pytest_args", nargs="*", help="pytestに渡す引数")

    args = parser.parse_args()

    # 競合オプションのチェック
    if args.no_cov and args.html:
        print("エラー: --no-cov と --html は同時に使用できません")
        sys.exit(1)

    if args.coverage_only and args.no_cov:
        print("エラー: --coverage-only と --no-cov は同時に使用できません")
        sys.exit(1)

    runner = TestRunner(verbose=args.verbose)

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

    # print使用チェック
    runner.check_print_usage()

    # dict.get()使用チェック
    if not args.no_dict_get_check:
        runner.check_dict_get_usage(auto_convert=args.auto_convert_dict_get)

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
