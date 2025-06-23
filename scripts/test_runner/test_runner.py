#!/usr/bin/env python3
"""
テストランナークラス - メインのテスト実行機能
"""

import sys
import time
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.command_executor import CommandExecutor
from infrastructure.file_handler import FileHandler
from infrastructure.logger import Logger


class TestRunner:
    def __init__(self, verbose: bool, logger: Logger, command_executor: CommandExecutor, file_handler: FileHandler):
        self.verbose = verbose
        self.logger = logger
        self.command_executor = command_executor
        self.file_handler = file_handler
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.displayed_policies: set = set()  # 表示済み修正方針を追跡

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """コマンドを実行し、結果を返す"""
        # ProgressSpinnerクラスを直接定義
        from scripts.infrastructure.logger import Logger

        class ProgressSpinner:
            def __init__(self, message: str, logger: Logger):
                self.message = message
                self.logger = logger

            def start(self):
                pass  # チェック中表示は不要

            def stop(self, success: bool = True):
                self.logger.info(f"{'✅' if success else '❌'} {self.message}")

        spinner = None
        if not self.verbose:
            spinner = ProgressSpinner(description, self.logger)
            spinner.start()

        result = self.command_executor.execute_command(
            cmd=cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
            timeout=None,
            env=None,
            check=False
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

        # CommandExecutorを使用してテストを実行
        # ライブプログレス表示のため、CommandExecutorの結果を使用
        result = self.command_executor.execute_command(
            cmd=cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
            timeout=None,
            env=None,
            check=False
        )

        # プログレス表示
        self.logger.print("🧪 テスト実行", end="", flush=True)

        # 簡単なプログレス表示（実際のライブプログレスは省略）
        for _i in range(3):
            time.sleep(0.1)
            self.logger.print(".", end="", flush=True)

        success = result.success
        output = result.stdout

        # 最終結果を表示
        self.logger.print(f"\r{'✅' if success else '❌'} テスト実行".ljust(90), flush=True)

        return success, output

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
                    if test['details']:
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
                        if part[:-1].isdigit():
                            pass
                        else:
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
                            if part[:-1].isdigit():
                                coverage = int(part[:-1])
                                if coverage < 80:  # 80%未満のみ収集
                                    low_coverage_files.append((file_path, coverage))
                            else:
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
