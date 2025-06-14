#!/usr/bin/env python3
"""
統合テスト・品質チェックツール
問題がある場合のみ詳細出力し、問題がない場合は簡潔なサマリーを表示
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class TestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            if result.returncode != 0:
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
            if self.verbose:
                print("⚠️  mypyがインストールされていません（推奨）")
            self.warnings.append("mypyがインストールされていません（推奨）")
            return True  # 型チェックなしでも続行

        return self.run_command(
            ["mypy", "src/", "--no-error-summary"],
            "型チェック (mypy)"
        )[0]

    def check_syntax(self) -> bool:
        """基本構文チェック"""
        import ast
        import glob

        syntax_errors = []
        for file_path in glob.glob('src/**/*.py', recursive=True):
            try:
                with open(file_path, encoding='utf-8') as f:
                    ast.parse(f.read(), filename=file_path)
            except SyntaxError as e:
                syntax_errors.append(f'{file_path}:{e.lineno}: {e.msg}')
            except Exception as e:
                syntax_errors.append(f'{file_path}: {e}')

        if syntax_errors:
            self.issues.extend(syntax_errors)
            return False
        return True

    def run_tests(self, pytest_args: List[str], no_coverage: bool = False, html_coverage: bool = False) -> bool:
        """pytest実行"""
        cmd = ["pytest"]

        if html_coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        elif not no_coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        cmd.extend(pytest_args)

        success, output = self.run_command(cmd, "テスト実行")

        # カバレッジが低い場合は警告
        if success and not no_coverage and "TOTAL" in output:
            lines = output.split('\n')
            for line in lines:
                if "TOTAL" in line and "%" in line:
                    # カバレッジパーセンテージを抽出
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            coverage = int(part[:-1])
                            if coverage < 80:
                                self.warnings.append(f"テストカバレッジが低いです: {coverage}%")
                            break

        return success

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
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("pytest_args", nargs="*", help="pytestに渡す引数")

    args = parser.parse_args()

    # 競合オプションのチェック
    if args.no_cov and args.html:
        print("エラー: --no-cov と --html は同時に使用できません")
        sys.exit(1)

    runner = TestRunner(verbose=args.verbose)

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
