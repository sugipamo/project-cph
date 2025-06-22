#!/usr/bin/env python3
"""
統合テスト・品質チェックツール
問題がある場合のみ詳細出力し、問題がない場合は簡潔なサマリーを表示
"""

import argparse
import sys

from code_analysis.dead_code_checker import DeadCodeChecker
from code_analysis.import_checker import ImportChecker
from quality_checks.dependency_injection_checker import DependencyInjectionChecker
from quality_checks.dict_get_checker import DictGetChecker
from quality_checks.fallback_checker import FallbackChecker
from quality_checks.getattr_checker import GetattrChecker
from quality_checks.infrastructure_duplication_checker import InfrastructureDuplicationChecker
from quality_checks.naming_checker import NamingChecker
from quality_checks.none_default_checker import NoneDefaultChecker
from quality_checks.print_usage_checker import PrintUsageChecker
from quality_checks.ruff_checker import RuffChecker
from quality_checks.syntax_checker import SyntaxChecker
from quality_checks.type_checker import TypeChecker
from test_runner.smoke_test import SmokeTest
from test_runner.test_runner import TestRunner

from infrastructure.command_executor import create_command_executor
from infrastructure.file_handler import create_file_handler
from infrastructure.logger import create_logger


class MainTestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = create_logger(verbose=verbose)
        self.command_executor = create_command_executor()
        self.file_handler = create_file_handler()

        # メインテストランナーの初期化
        self.test_runner = TestRunner(
            verbose=verbose,
            logger=self.logger,
            command_executor=self.command_executor,
            file_handler=self.file_handler
        )

        # 品質チェッカーの初期化
        self.ruff_checker = RuffChecker(
            self.file_handler,
            self.command_executor,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.syntax_checker = SyntaxChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.type_checker = TypeChecker(
            self.file_handler,
            self.command_executor,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.dead_code_checker = DeadCodeChecker(
            self.command_executor,
            self.logger,
            self.test_runner.warnings,
            self.test_runner.issues
        )

        self.import_checker = ImportChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.naming_checker = NamingChecker(
            self.file_handler,
            self.logger,
            self.test_runner.warnings,
            verbose
        )

        self.smoke_test = SmokeTest(
            self.command_executor,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.dependency_injection_checker = DependencyInjectionChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.print_usage_checker = PrintUsageChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.infrastructure_duplication_checker = InfrastructureDuplicationChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.none_default_checker = NoneDefaultChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.fallback_checker = FallbackChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.dict_get_checker = DictGetChecker(
            self.file_handler,
            self.command_executor,
            self.logger,
            self.test_runner.issues,
            verbose
        )

        self.getattr_checker = GetattrChecker(
            self.file_handler,
            self.logger,
            self.test_runner.issues,
            verbose
        )

    def run_all_checks(self, args):
        """全てのチェックを実行"""
        # カバレッジレポートのみモード
        if args.coverage_only:
            self.test_runner.run_tests(args.pytest_args, False, args.html)
            self.test_runner.print_summary()
            return

        # 基本チェック（構文・インポート・スモークテスト）
        self.syntax_checker.check_syntax()
        if not args.no_import_check:
            self.import_checker.check_import_resolution()
        if not args.no_smoke_test:
            self.smoke_test.quick_smoke_test()

        # コード品質チェック
        if not args.no_ruff:
            self.ruff_checker.check_ruff()
            self.ruff_checker.check_quality_scripts()

        # 未使用コード検出
        if not args.no_deadcode:
            self.dead_code_checker.check_dead_code()

        # 命名規則チェック
        if not args.no_naming:
            self.naming_checker.check_naming_conventions()

        # 依存性注入チェック
        self.dependency_injection_checker.check_dependency_injection()

        # print使用チェック
        self.print_usage_checker.check_print_usage()

        # Infrastructure重複生成チェック
        self.infrastructure_duplication_checker.check_infrastructure_duplication()

        # None引数初期値チェック
        self.none_default_checker.check_none_default_arguments()

        # try文使用チェック
        self.fallback_checker.check_fallback_patterns()

        # dict.get()使用チェック
        self.dict_get_checker.check_dict_get_usage()

        # getattr()デフォルト値使用チェック
        self.getattr_checker.check_getattr_usage()

        # check-onlyモード
        if args.check_only:
            self.type_checker.check_types()
            self.test_runner.print_summary()
            return

        # テスト実行
        self.test_runner.run_tests(args.pytest_args, args.no_cov, args.html)

        # サマリー表示
        self.test_runner.print_summary()


def main():
    parser = argparse.ArgumentParser(description="統合テスト・品質チェックツール")
    parser.add_argument("--no-cov", action="store_true", help="カバレッジなしでテスト実行")
    parser.add_argument("--html", action="store_true", help="HTMLカバレッジレポート生成")
    parser.add_argument("--no-ruff", action="store_true", help="Ruffスキップ")
    parser.add_argument("--no-deadcode", action="store_true", help="未使用コード検出スキップ")
    parser.add_argument("--no-naming", action="store_true", help="命名規則チェックスキップ")
    parser.add_argument("--no-import-check", action="store_true", help="インポート解決チェックスキップ")
    parser.add_argument("--no-smoke-test", action="store_true", help="スモークテストスキップ")
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

    runner = MainTestRunner(verbose=args.verbose)
    runner.run_all_checks(args)


if __name__ == "__main__":
    main()
