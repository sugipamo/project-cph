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

            if spinner:
                spinner.stop(success)

            if not success:
                if self.verbose:
                    print(f"❌ {description}")
                    print(f"   コマンド: {' '.join(cmd)}")
                    print(f"   エラー出力: {result.stderr}")
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
