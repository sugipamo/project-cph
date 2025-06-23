#!/usr/bin/env python3
"""
統合テスト・品質チェックツール
問題がある場合のみ詳細出力し、問題がない場合は簡潔なサマリーを表示
"""

import argparse
import sys
from collections import defaultdict
from typing import Dict, List

from code_analysis.dead_code_checker import DeadCodeChecker
from code_analysis.import_checker import ImportChecker
from quality_checks.clean_architecture_checker import CleanArchitectureChecker
from quality_checks.dependency_injection_checker import DependencyInjectionChecker
from quality_checks.dict_get_checker import DictGetChecker
from quality_checks.fallback_checker import FallbackChecker
from quality_checks.getattr_checker import GetattrChecker
from quality_checks.infra_dup_checker import InfrastructureDuplicationChecker
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
    def __init__(self, verbose: bool):
        self.verbose = verbose
        self.logger = create_logger(verbose=verbose, silent=False)
        self.command_executor = create_command_executor(mock=True, subprocess_wrapper=None)
        self.file_handler = create_file_handler(mock=True, file_operations=None)

        # エラー種類ごとのグルーピング用
        self.error_groups: Dict[str, List[str]] = defaultdict(list)

        # メインテストランナーの初期化
        self.test_runner = TestRunner(
            verbose=verbose,
            logger=self.logger,
            command_executor=self.command_executor,
            file_handler=self.file_handler
        )

        # 品質チェッカーの初期化（サイレントモード）
        silent_logger = create_logger(verbose=False, silent=True)
        self.ruff_checker = RuffChecker(
            self.file_handler,
            self.command_executor,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.syntax_checker = SyntaxChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.type_checker = TypeChecker(
            self.file_handler,
            self.command_executor,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.dead_code_checker = DeadCodeChecker(
            self.command_executor,
            silent_logger,
            self.test_runner.warnings,
            self.test_runner.issues
        )

        self.import_checker = ImportChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.naming_checker = NamingChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.warnings,
            verbose
        )

        self.smoke_test = SmokeTest(
            self.command_executor,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.dependency_injection_checker = DependencyInjectionChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.print_usage_checker = PrintUsageChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.infrastructure_duplication_checker = InfrastructureDuplicationChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.none_default_checker = NoneDefaultChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.fallback_checker = FallbackChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.dict_get_checker = DictGetChecker(
            self.file_handler,
            self.command_executor,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.getattr_checker = GetattrChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

        self.clean_architecture_checker = CleanArchitectureChecker(
            self.file_handler,
            silent_logger,
            self.test_runner.issues,
            verbose
        )

    def _categorize_errors(self):
        """エラーをエラー種類ごとにグループ化"""
        # issuesリストからエラーをカテゴリーごとに分類
        for issue in self.test_runner.issues:
            if "構文エラー" in issue:
                self.error_groups["構文エラー"].append(issue)
            elif "インポートエラー" in issue or "インポート解決" in issue:
                self.error_groups["インポートエラー"].append(issue)
            elif "型チェック" in issue or "mypy" in issue:
                self.error_groups["型チェックエラー"].append(issue)
            elif "Ruff" in issue or "lint" in issue:
                self.error_groups["コード品質エラー（Ruff）"].append(issue)
            elif "未使用コード" in issue or "vulture" in issue:
                self.error_groups["未使用コード検出"].append(issue)
            elif "命名規則" in issue:
                self.error_groups["命名規則違反"].append(issue)
            elif "依存性注入" in issue or "副作用" in issue:
                self.error_groups["副作用が検出されました"].append(issue)
            elif "print使用" in issue:
                self.error_groups["print文使用検出"].append(issue)
            elif "Infrastructure重複" in issue:
                self.error_groups["Infrastructure重複生成"].append(issue)
            elif "None引数" in issue or "デフォルト引数" in issue:
                self.error_groups["デフォルト引数使用"].append(issue)
            elif "フォールバック" in issue or "try文" in issue:
                self.error_groups["フォールバック処理検出"].append(issue)
            elif "dict.get()" in issue:
                self.error_groups["dict.get()使用検出"].append(issue)
            elif "getattr()" in issue:
                self.error_groups["getattr()デフォルト値使用"].append(issue)
            elif "クリーンアーキテクチャ違反" in issue:
                self.error_groups["クリーンアーキテクチャ違反"].append(issue)
            elif "テスト実行" in issue:
                self.error_groups["テスト失敗"].append(issue)
            else:
                self.error_groups["その他のエラー"].append(issue)

    def _print_grouped_summary(self):
        """エラー種類ごとにグループ化して結果を表示"""
        # エラーをカテゴライズ
        self._categorize_errors()

        # チェック結果の進捗表示を実行した各チェックについて出力
        self._print_check_status()

        # 警告を表示
        if self.test_runner.warnings:
            print("⚠️  警告:")
            for warning in self.test_runner.warnings:
                print(f"   {warning}")
            print("💡 警告の対処方法:")
            print("    - 不要な警告の原因を特定し、コードを修正してください")
            print("    - 警告を無視せず、適切に対処することで品質を向上させます")
            print("    【Python実装例】")
            print("    • 命名規則: def calculate_total(items) → snake_case使用")
            print("    • Logger使用: logger.info(f'計算開始: {x} + {y}') → print文の代替")
            print("    • 明示的設定: timeout = config['timeout'] → dict.get()の代替")
            print("    • 属性チェック: if hasattr(obj, 'attr'): value = obj.attr → getattr()の代替")
            print("    • 依存性注入: def process_data(data, file_writer) → 副作用の委譲")
            print("    • Result型使用: result = error_converter.execute_with_conversion(op)")
            print("      if result.is_failure(): handle_error(result.error) → フォールバック処理の代替")

        # エラーがない場合
        if not self.test_runner.issues:
            if not self.test_runner.warnings:
                print("✅ 全ての品質チェックが正常に完了しました")
            return

        # エラー種類ごとに表示
        print("❌ 修正が必要な問題:")
        for error_type, errors in self.error_groups.items():
            if errors:
                print(f"\n{error_type}:")

                # 修正方針メッセージを表示
                fix_guidance = self._get_fix_guidance(error_type)
                if fix_guidance:
                    print("📋 修正方針:")
                    for guidance_line in fix_guidance.split('\n'):
                        if guidance_line.strip():
                            print(f"    {guidance_line}")
                    print()  # 空行

                # 各エラーの詳細を抽出してインデント表示
                for error in errors:
                    # エラーメッセージから実際の内容部分を抽出
                    parts = error.split(": ", 1)
                    if len(parts) > 1:
                        # エラー内容の各行をインデント
                        error_lines = parts[1].strip().split("\n")
                        for line in error_lines:
                            print(f"    {line}")
                    else:
                        print(f"    {error}")

        sys.exit(1)

    def _print_check_status(self):
        """各チェックの実行ステータスを表示"""
        # issuesとwarningsから実行されたチェックの成功/失敗を判定
        check_results = {}

        # デフォルトで実行される基本チェック
        check_results["構文チェック"] = not any("構文エラー" in issue for issue in self.test_runner.issues)
        check_results["インポート解決チェック"] = not any("インポート" in issue for issue in self.test_runner.issues)
        check_results["クイックスモークテスト"] = not any("スモークテスト" in issue for issue in self.test_runner.issues)
        check_results["Ruff自動修正"] = True  # 自動修正は常に実行
        check_results["コード品質チェック (ruff)"] = not any("Ruff" in issue or "lint" in issue for issue in self.test_runner.issues)
        check_results["未使用コード検出"] = not any("未使用コード" in issue for issue in self.test_runner.issues)
        check_results["命名規則チェック"] = not any("命名規則" in issue for issue in self.test_runner.issues)
        check_results["依存性注入チェック"] = not any("依存性注入" in issue or "副作用" in issue for issue in self.test_runner.issues)
        check_results["print使用チェック"] = not any("print使用" in issue for issue in self.test_runner.issues)
        check_results["Infrastructure重複生成チェック"] = not any("Infrastructure重複" in issue for issue in self.test_runner.issues)
        check_results["None引数初期値チェック"] = not any("None引数" in issue or "デフォルト引数" in issue for issue in self.test_runner.issues)
        check_results["フォールバック処理チェック"] = not any("フォールバック" in issue or "try文" in issue for issue in self.test_runner.issues)
        check_results["dict.get()使用チェック"] = not any("dict.get()" in issue for issue in self.test_runner.issues)
        check_results["getattr()デフォルト値使用チェック"] = not any("getattr()" in issue for issue in self.test_runner.issues)
        check_results["クリーンアーキテクチャチェック"] = not any("クリーンアーキテクチャ違反" in issue for issue in self.test_runner.issues)

        # 各チェックの結果を表示
        for check_name, success in check_results.items():
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {check_name}")

        print()  # 空行

    def _get_fix_guidance(self, error_type: str) -> str:
        """エラー種類に対応する修正方針メッセージを返す"""
        guidance_map = {
            "構文エラー": (
                "構文エラーは即座に修正が必要です\n"
                "IDEの構文チェック機能を活用してください\n"
                "インデント、括弧の対応、コロンの抜けなどを確認してください"
            ),
            "インポートエラー": (
                "モジュールの依存関係を確認してください\n"
                "相対インポートではなく絶対インポートを使用してください\n"
                "循環インポートが発生していないか確認してください\n"
                "必要なパッケージがインストールされているか確認してください"
            ),
            "型チェックエラー": (
                "型アノテーションを追加してください\n"
                "Optional型の適切な処理を行ってください\n"
                "型の一貫性を保ってください\n"
                "Noneチェックを適切に実装してください"
            ),
            "コード品質エラー（Ruff）": (
                "Ruffの指摘に従ってコードスタイルを統一してください\n"
                "未使用のインポートや変数を削除してください\n"
                "命名規則に従ってください（PEP 8準拠）\n"
                "コードの可読性を向上させてください"
            ),
            "副作用が検出されました": (
                "【CLAUDE.mdルール適用】\n"
                "副作用はsrc/infrastructure、tests/infrastructureのみで許可されます\n"
                "全ての副作用はmain.pyから依存性注入してください\n"
                "ビジネスロジック層では副作用を避けてください\n"
                "ファイル操作、外部APIコール、データベースアクセスはInfrastructure層で実装してください"
            ),
            "print文使用検出": (
                "print文の代わりにLoggerインターフェースを使用してください\n"
                "Infrastructure層から注入されたLoggerを使用してください\n"
                "デバッグ用のprint文は本番コードから削除してください\n"
                "必要な場合はlogger.info()、logger.error()を使用してください"
            ),
            "dict.get()使用検出": (
                "【CLAUDE.mdルール適用】\n"
                "dict.get()の使用は禁止されています\n"
                "設定値は明示的に設定ファイル（{setting}.json）に定義してください\n"
                "src/configuration/readme.mdの設定取得方法に従ってください\n"
                "デフォルト値ではなく、適切な設定管理を実装してください"
            ),
            "getattr()デフォルト値使用": (
                "【CLAUDE.mdルール適用】\n"
                "getattr()のデフォルト値使用は禁止されています\n"
                "属性の存在チェックを明示的に行ってください\n"
                "hasattr()を使用して属性の存在を確認してください\n"
                "必要なエラーを見逃すことを防ぐため、フォールバック処理は避けてください"
            ),
            "デフォルト引数使用": (
                "【CLAUDE.mdルール適用】\n"
                "引数にデフォルト値を指定することは禁止されています\n"
                "呼び出し元で値を用意することを徹底してください\n"
                "全ての引数を明示的に渡すことで、バグの発見を容易にします\n"
                "設定値が必要な場合は設定ファイルから取得してください"
            ),
            "Infrastructure重複生成": (
                "Infrastructureコンポーネントの重複生成を避けてください\n"
                "シングルトンパターンまたは依存性注入を使用してください\n"
                "main.pyからの一元的な注入を実装してください\n"
                "リソースの適切な管理を行ってください"
            ),
            "フォールバック処理検出": (
                "【CLAUDE.mdルール適用】\n"
                "フォールバック処理は禁止されています\n"
                "try-except文での無条件キャッチは避けてください\n"
                "Infrastructure層でErrorConverterを使用してResult型に変換してください\n"
                "ビジネスロジック層ではis_failure()でエラーを明示的にチェックしてください\n"
                "例: error_converter.execute_with_conversion(operation) → result.is_failure()で判定"
            ),
            "命名規則違反": (
                "PEP 8の命名規則に従ってください\n"
                "変数名、関数名はsnake_caseを使用してください\n"
                "クラス名はPascalCaseを使用してください\n"
                "意味のある名前を使用し、略語は避けてください"
            ),
            "テスト失敗": (
                "失敗したテストの原因を特定してください\n"
                "テストコードとプロダクションコードの整合性を確認してください\n"
                "モックの設定が適切かどうか確認してください\n"
                "テストデータの準備が正しく行われているか確認してください"
            ),
            "クリーンアーキテクチャ違反": (
                "【CLAUDE.mdルール適用】\n"
                "レイヤー間の依存関係を正しい方向に修正してください\n"
                "ドメイン層（operations）は外部依存を持ってはいけません\n"
                "インフラストラクチャ層への直接依存を避け、依存性注入を使用してください\n"
                "循環依存を解消してください\n"
                "例: src.operations -> src.infrastructure (×) / main.pyからの注入 (○)"
            ),
            "その他のエラー": (
                "エラーメッセージを詳細に確認してください\n"
                "関連するドキュメントを参照してください\n"
                "必要に応じてログを追加して問題を特定してください\n"
                "CLAUDE.mdのルールに照らし合わせて適切な対応を行ってください"
            )
        }

        # CLAUDE.mdルール適用: dict.get()使用禁止、明示的設定取得
        if error_type in guidance_map:
            return guidance_map[error_type]
        return ""

    def run_all_checks(self, args):
        """全てのチェックを実行"""
        # カバレッジレポートのみモード
        if args.coverage_only:
            self.test_runner.run_tests(args.pytest_args, False, args.html)
            self._print_grouped_summary()
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

        # クリーンアーキテクチャチェック
        self.clean_architecture_checker.check_clean_architecture()

        # check-onlyモード
        if args.check_only:
            self.type_checker.check_types()
            self._print_grouped_summary()
            return

        # テスト実行
        self.test_runner.run_tests(args.pytest_args, args.no_cov, args.html)

        # サマリー表示
        self._print_grouped_summary()


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
