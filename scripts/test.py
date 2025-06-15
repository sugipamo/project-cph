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
                    print(f"   エラー出力: {result.stderr}")
                # vultureの場合は特別処理（未使用コード検出時は正常終了とみなす）
                if cmd[0] == "vulture" and result.stdout.strip():
                    return True, result.stdout
                self.issues.append(f"{description}: {result.stderr.strip()}")
                return False, result.stderr
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

            for file_path in glob.glob('src/**/*.py', recursive=True):
                file_name = Path(file_path).name
                relative_path = file_path.replace('src/', '')

                # ファイル名チェック
                if file_name in generic_filenames:
                    naming_issues.append(f"汎用的ファイル名: {relative_path}")

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
                            for pattern in generic_class_patterns:
                                if re.match(pattern, class_name):
                                    naming_issues.append(f"汎用的クラス名: {relative_path}:{node.lineno} class {class_name}")

                        # 関数名チェック
                        elif isinstance(node, ast.FunctionDef):
                            func_name = node.name
                            # プライベートメソッドやspecialメソッドはスキップ
                            if not func_name.startswith('_'):
                                for pattern in abstract_function_patterns:
                                    if re.match(pattern, func_name):
                                        naming_issues.append(f"抽象的関数名: {relative_path}:{node.lineno} def {func_name}")

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

        cmd.extend(pytest_args)

        success, output = self.run_command(cmd, "テスト実行")

        # カバレッジ詳細分析
        if success and not no_coverage and output:
            self._analyze_coverage(output)

        return success

    def _analyze_coverage(self, output: str) -> None:
        """カバレッジ詳細分析"""
        lines = output.split('\n')
        total_coverage = None
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
                            total_coverage = int(part[:-1])
                        except ValueError:
                            continue
                        break
            # 個別ファイルのカバレッジ
            elif line.startswith('src/') and '%' in line:
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[0]
                    # パーセンテージを探す
                    for part in parts[1:]:
                        if part.endswith('%'):
                            try:
                                coverage = int(part[:-1])
                                if coverage < 80:  # 80%未満は低カバレッジ
                                    low_coverage_files.append((file_path, coverage))
                            except ValueError:
                                continue
                            break

        # 警告メッセージを生成
        if total_coverage is not None and total_coverage < 80:
            self.warnings.append(f"テストカバレッジが低いです: {total_coverage}%")

        if low_coverage_files:
            # カバレッジが低い順にソート
            low_coverage_files.sort(key=lambda x: x[1])
            self.warnings.append("カバレッジが低いファイル:")
            for file_path, coverage in low_coverage_files[:10]:  # 最大10件
                # ファイル名を短縮表示
                short_path = file_path.replace('src/', '')
                self.warnings.append(f"  {short_path}: {coverage}%")

            if len(low_coverage_files) > 10:
                self.warnings.append(f"  ... 他{len(low_coverage_files) - 10}件")

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

    # check-onlyモード
    if args.check_only:
        runner.check_types()
        runner.check_syntax()
        runner.print_summary()
        return

    # テスト実行
    runner.run_tests(args.pytest_args, args.no_cov, args.html)

    # サマリー表示
    runner.print_summary()


if __name__ == "__main__":
    main()
