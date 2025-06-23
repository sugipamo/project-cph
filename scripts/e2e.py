#!/usr/bin/env python3
"""
E2E Tests for cph.sh - Contest Problem Helper
極シンプルなコマンド実行テスト
"""

# 副作用の直接インポートは禁止 - main.pyから注入が必要
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

# scripts/infrastructure modules
# sys.path.insert(0, str(Path(__file__).parent))  # 副作用の直接使用は禁止
from infrastructure.command_executor import CommandExecutor, create_command_executor
from infrastructure.file_handler import FileHandler, create_file_handler
from infrastructure.logger import Logger, create_logger


@dataclass
class TestStep:
    command: List[str]
    validator: Callable[[], bool]


class E2ETester:
    """E2Eテスト実行クラス"""

    def __init__(self, project_root: Path, command_executor: CommandExecutor, logger: Logger, file_handler: FileHandler):
        self.project_root = project_root
        self.command_executor = command_executor
        self.logger = logger
        self.file_handler = file_handler

    def cleanup_environment(self):
        """テスト環境のクリーンアップ"""
        dirs = ["contest_current", "contest_stock", "workspace"]
        for d in dirs:
            dir_path = self.project_root / d
            if self.file_handler.exists(dir_path):
                self.file_handler.remove_dir(dir_path, recursive=True)

        db_file = self.project_root / "cph_history.db"
        if self.file_handler.exists(db_file):
            self.file_handler.remove_file(db_file)

    def check_test_files_exist(self) -> bool:
        """テストファイルの存在チェック"""
        test_dir = self.project_root / "contest_current" / "test"
        if not self.file_handler.exists(test_dir):
            return False
        test_files = self.file_handler.glob("*.in", test_dir)
        return len(test_files) > 0

    def run_step(self, step: TestStep, cmd_index: int) -> None:
        self.logger.info(f"実行: {' '.join(step.command)}")
        result = self.command_executor.execute_command(
            cmd=step.command,
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            timeout=None,
            env=None,
            check=False
        )
        if not result.success:
            raise RuntimeError(f"コマンド失敗: {result.stderr}\n結果: FAIL")
        return

    def run_all_steps(self) -> bool:
        """全テストステップの実行"""
        steps = self.define_test_steps()
        results = []

        # 各ステップを実行
        for i, step in enumerate(steps):
            self.run_step(step, i)

        # 結果サマリー
        passed = sum(1 for r in results if r)
        total = len(results)
        self.logger.info("\n=== テスト結果サマリー ===")
        self.logger.info(f"結果: {passed}/{total} PASS")

        return passed == total

def main(args):
    """E2Eテストのメイン実行関数"""
    project_root = Path(args.project_root)

    # インフラストラクチャコンポーネントを初期化
    logger = create_logger()
    command_executor = create_command_executor(mock=False, subprocess_wrapper=None)
    file_handler = create_file_handler()

    logger.info("=== cph.sh E2E Test 開始 ===")

    # テスター初期化
    tester = E2ETester(project_root, command_executor, logger, file_handler)

    # run_step実行 - 何を実行するかが一目でわかる
    def run_step(cmd):
        step = TestStep(command=cmd, validator=None)
        return tester.run_step(step, 0)

    # 環境クリーンアップ
    logger.info("テスト環境をクリーンアップ中...")
    tester.cleanup_environment()

    # ステップ1: ABC300問題A(Python)をオープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A)")

    main_py_path = project_root / "contest_current" / "main.py"
    existing_content = file_handler.read_text(main_py_path)
    file_handler.write_text(main_py_path, existing_content + "raise Exception('test')")

    # ステップ2: ABC301問題A(前回値)をオープン
    run_step(["./cph.sh", "abc301", "open", "a", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC301 問題A)")

    # ステップ2直後: main.pyにraise Exception('test')が含まれていないことを確認
    main_py_path = project_root / "contest_current" / "main.py"
    content = file_handler.read_text(main_py_path)
    assert "raise Exception('test')" not in content, "main.pyにraise Exception('test')が含まれています（ステップ2直後）"

    # ステップ3: テスト実行(全問題)
    run_step(["./cph.sh", "test", "local"])

    # ステップ4: ABC300問題A(Python)を再オープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A 再オープン)")

    # ステップ4直後: main.pyにraise Exception('test')が含まれていることを確認
    main_py_path = project_root / "contest_current" / "main.py"
    content = file_handler.read_text(main_py_path)
    assert "raise Exception('test')" in content, "main.pyにraise Exception('test')が含まれていません（ステップ4直後）"

    # ステップ5: テスト実行(問題A指定)
    run_step(["./cph.sh", "test", "a", "local"])


    # 以下はdockerでのテスト
    logger.info("テスト環境をクリーンアップ中...")
    tester.cleanup_environment()

    # ステップ1: ABC300問題A(Python)をオープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A)")

    main_py_path = project_root / "contest_current" / "main.py"
    existing_content = file_handler.read_text(main_py_path)
    file_handler.write_text(main_py_path, existing_content + "raise Exception('test')")

    # ステップ2: ABC301問題A(前回値)をオープン
    run_step(["./cph.sh", "abc301", "open", "a", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC301 問題A)")

    # ステップ2直後: main.pyにraise Exception('test')が含まれていないことを確認
    main_py_path = project_root / "contest_current" / "main.py"
    content = file_handler.read_text(main_py_path)
    assert "raise Exception('test')" not in content, "main.pyにraise Exception('test')が含まれています（ステップ2直後）"

    # ステップ3: テスト実行(全問題)
    run_step(["./cph.sh", "test", "docker"])

    # ステップ4: ABC300問題A(Python)を再オープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A 再オープン)")

    # ステップ4直後: main.pyにraise Exception('test')が含まれていることを確認
    main_py_path = project_root / "contest_current" / "main.py"
    content = file_handler.read_text(main_py_path)
    assert "raise Exception('test')" in content, "main.pyにraise Exception('test')が含まれていません（ステップ4直後）"

    # ステップ5: テスト実行(問題A指定)
    run_step(["./cph.sh", "test", "a", "docker"])

    logger.info("\n=== テスト結果サマリー ===")
    logger.info("=== E2E Test 成功 ===")
    # sys.exit(0) は副作用のため削除 - 正常終了は関数のreturnで表現


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="cph.sh E2E Tests")
    parser.add_argument("--project-root", default=".", help="プロジェクトルートディレクトリ")
    args = parser.parse_args()

    main(args)
