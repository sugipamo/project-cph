#!/usr/bin/env python3
"""
E2E Tests for cph.sh - Contest Problem Helper
極シンプルなコマンド実行テスト
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List


@dataclass
class TestStep:
    command: List[str]
    validator: Callable[[], bool]


class E2ETester:
    """E2Eテスト実行クラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def cleanup_environment(self):
        """テスト環境のクリーンアップ"""
        dirs = ["contest_current", "contest_stock", "workspace"]
        for d in dirs:
            dir_path = self.project_root / d
            if dir_path.exists():
                shutil.rmtree(dir_path)

        db_file = self.project_root / "cph_history.db"
        if db_file.exists():
            db_file.unlink()

    def check_test_files_exist(self) -> bool:
        """テストファイルの存在チェック"""
        test_dir = self.project_root / "contest_current" / "test"
        if not test_dir.exists():
            return False
        test_files = list(test_dir.glob("*.in"))
        return len(test_files) > 0

    def run_step(self, step: TestStep, cmd_index: int) -> None:
        print(f"\n[Step {cmd_index+1}]")
        print(f"実行: {' '.join(step.command)}")
        result = subprocess.run(
            step.command,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
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
        print("\n=== テスト結果サマリー ===")
        print(f"結果: {passed}/{total} PASS")

        return passed == total

def main(args):
    """E2Eテストのメイン実行関数"""
    project_root = Path(args.project_root)

    print("=== cph.sh E2E Test 開始 ===")

    # テスター初期化
    tester = E2ETester(project_root)

    # run_step実行 - 何を実行するかが一目でわかる
    def run_step(cmd):
        step = TestStep(command=cmd, validator=None)
        return tester.run_step(step, 0)

    # 環境クリーンアップ
    print("テスト環境をクリーンアップ中...")
    tester.cleanup_environment()

    # ステップ1: ABC300問題A(Python)をオープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A)")

    with open("contest_current/main.py", "a") as f:
        f.write("raise Exception('test')")

    # ステップ2: ABC301問題A(前回値)をオープン
    run_step(["./cph.sh", "abc301", "open", "a", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC301 問題A)")

    # ステップ2直後: main.pyにraise Exception('test')が含まれていないことを確認
    with open("contest_current/main.py") as f:
        content = f.read()
    assert "raise Exception('test')" not in content, "main.pyにraise Exception('test')が含まれています（ステップ2直後）"

    # ステップ3: テスト実行(全問題)
    run_step(["./cph.sh", "test", "local"])

    # ステップ4: ABC300問題A(Python)を再オープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "local"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A 再オープン)")

    # ステップ4直後: main.pyにraise Exception('test')が含まれていることを確認
    with open("contest_current/main.py") as f:
        content = f.read()
    assert "raise Exception('test')" in content, "main.pyにraise Exception('test')が含まれていません（ステップ4直後）"

    # ステップ5: テスト実行(問題A指定)
    run_step(["./cph.sh", "test", "a", "local"])


    # 以下はdockerでのテスト
    print("テスト環境をクリーンアップ中...")
    tester.cleanup_environment()

    # ステップ1: ABC300問題A(Python)をオープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A)")

    with open("contest_current/main.py", "a") as f:
        f.write("raise Exception('test')")

    # ステップ2: ABC301問題A(前回値)をオープン
    run_step(["./cph.sh", "abc301", "open", "a", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC301 問題A)")

    # ステップ2直後: main.pyにraise Exception('test')が含まれていないことを確認
    with open("contest_current/main.py") as f:
        content = f.read()
    assert "raise Exception('test')" not in content, "main.pyにraise Exception('test')が含まれています（ステップ2直後）"

    # ステップ3: テスト実行(全問題)
    run_step(["./cph.sh", "test", "docker"])

    # ステップ4: ABC300問題A(Python)を再オープン
    run_step(["./cph.sh", "abc300", "open", "a", "python", "docker"])
    if not tester.check_test_files_exist():
        raise RuntimeError("テストファイルが存在しません (ABC300 問題A 再オープン)")

    # ステップ4直後: main.pyにraise Exception('test')が含まれていることを確認
    with open("contest_current/main.py") as f:
        content = f.read()
    assert "raise Exception('test')" in content, "main.pyにraise Exception('test')が含まれていません（ステップ4直後）"

    # ステップ5: テスト実行(問題A指定)
    run_step(["./cph.sh", "test", "a", "docker"])

    print("\n=== テスト結果サマリー ===")
    print("=== E2E Test 成功 ===")
    sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="cph.sh E2E Tests")
    parser.add_argument("--project-root", default=".", help="プロジェクトルートディレクトリ")
    args = parser.parse_args()

    main(args)
