#!/usr/bin/env python3
"""
E2E Tests for cph.sh - Contest Problem Helper

このスクリプトは cph.sh の主要な機能をエンドツーエンドでテストします。

テストシナリオ:
contest_current/, contest_stock/, workspace/を削除

./cph.sh abc300 open a python
    contest_current/testが作成されて中にテストファイルがある
    contets_currentにmain.pyがあり、contest_template/python/main.pyのものと同一になっている
    contest_current/main.pyの末尾にraise Exception()を追加

./cph.sh abc301 open a
    contest_current/testが作成されて中にテストファイルがある
    contets_currentにmain.pyがあり、contest_template/python/main.pyのものと同一になっている

./cph.sh test
    テストが実行される。

./cph.sh abc300 open a python
    contest_stock/python/abc300/a/testのデータがcontest_currentに移動される
    contest_stock/python/abc300/a/main.pyのデータがcontest_currentに移動される

./cph.sh test a
    テストは実行されているが、それぞれエラーが起きている

"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class E2ETestRunner:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.cph_script = self.project_root / "cph.sh"
        self.contest_current = self.project_root / "contest_current"
        self.contest_stock = self.project_root / "contest_stock"
        self.workspace = self.project_root / "workspace"
        self.contest_template = self.project_root / "contest_template"

        # テスト用のコンテスト設定
        self.contest1 = "abc300"
        self.contest2 = "abc301"
        self.problem = "a"
        self.language = "python"

    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        print(f"[{level}] {message}")

    def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """コマンド実行"""
        self.log(f"実行: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            shell=len(cmd) == 1
        )
        if result.stdout:
            self.log(f"出力: {result.stdout.strip()}")
        if result.stderr:
            self.log(f"エラー: {result.stderr.strip()}", "ERROR")
        return result

    def check_file_exists(self, file_path: Path, should_exist: bool = True) -> bool:
        """ファイル存在チェック"""
        exists = file_path.exists()
        status = "存在" if exists else "不存在"
        expected = "期待通り" if exists == should_exist else "期待と異なる"
        self.log(f"ファイル確認: {file_path} -> {status} ({expected})")
        return exists == should_exist

    def check_file_content(self, file_path: Path, expected_content: Optional[str] = None) -> bool:
        """ファイル内容チェック"""
        if not file_path.exists():
            self.log(f"ファイルが存在しません: {file_path}", "ERROR")
            return False

        content = file_path.read_text()
        self.log(f"ファイル内容確認: {file_path}")
        self.log(f"内容: {content.strip()}")

        if expected_content is not None:
            matches = expected_content in content
            self.log(f"期待内容チェック: {'一致' if matches else '不一致'}")
            return matches
        return True

    def cleanup_environment(self) -> bool:
        """テスト環境のクリーンアップ"""
        self.log("=== 環境クリーンアップ ===")

        dirs_to_remove = [self.contest_current, self.contest_stock, self.workspace]
        for dir_path in dirs_to_remove:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"削除: {dir_path}")

        return True

    def test_open_new_contest(self) -> bool:
        """新しいコンテスト問題を開くテスト"""
        self.log(f"=== {self.contest1} {self.problem}問題を{self.language}で開く ===")

        self.run_command(["./cph.sh", self.contest1, "open", self.problem, self.language])

        # ファイル生成確認
        main_py = self.contest_current / "main.py"
        template_py = self.contest_template / self.language / "main.py"
        test_dir = self.contest_current / "test"

        checks = [
            self.check_file_exists(main_py),
            self.check_file_exists(test_dir),
        ]

        # テストファイルの存在確認
        if test_dir.exists():
            test_files = list(test_dir.glob("sample-*.in"))
            if test_files:
                self.log(f"テストファイル確認: {len(test_files)}個のサンプルファイルが生成")
                checks.append(True)
            else:
                self.log("テストファイルが見つかりません", "ERROR")
                checks.append(False)

        # テンプレートと同じ内容かチェック
        if template_py.exists() and main_py.exists():
            template_content = template_py.read_text()
            main_content = main_py.read_text()
            if template_content == main_content:
                self.log("テンプレートからの初期化: 成功")
                checks.append(True)
            else:
                self.log("テンプレートからの初期化: 失敗", "ERROR")
                checks.append(False)

        return all(checks)

    def modify_code_with_error(self) -> bool:
        """コードにエラーを追加"""
        self.log("=== main.pyにエラーを追加 ===")

        main_py = self.contest_current / "main.py"
        if not main_py.exists():
            self.log("main.pyが存在しません", "ERROR")
            return False

        # ファイルの末尾に raise Exception() を追加
        content = main_py.read_text()
        modified_content = content + "\nraise Exception()\n"
        main_py.write_text(modified_content)

        self.log("raise Exception() を追加しました")
        return self.check_file_content(main_py, "raise Exception()")

    def test_switch_contest(self) -> bool:
        """別のコンテストに切り替え"""
        self.log(f"=== {self.contest2} {self.problem}問題に切り替え ===")

        self.run_command(["./cph.sh", self.contest2, "open", self.problem])

        # バックアップが作成されたかチェック
        backup_path = self.contest_stock / self.language / self.contest1 / self.problem / "main.py"
        main_py = self.contest_current / "main.py"
        test_dir = self.contest_current / "test"

        checks = [
            self.check_file_exists(backup_path),
            self.check_file_exists(main_py),
            self.check_file_exists(test_dir),
            self.check_file_content(backup_path, "raise Exception()"),  # バックアップにエラーが保存されているか
        ]

        # 新しいコンテストのテストファイル確認
        if test_dir.exists():
            test_files = list(test_dir.glob("sample-*.in"))
            if test_files:
                self.log(f"新しいコンテストのテストファイル確認: {len(test_files)}個のサンプルファイルが生成")
                checks.append(True)
            else:
                self.log("新しいコンテストのテストファイルが見つかりません", "ERROR")
                checks.append(False)

        return all(checks)

    def test_run_test(self) -> bool:
        """テスト実行"""
        self.log("=== テスト実行 ===")

        result = self.run_command(["./cph.sh", "test"])

        # テストが実行されたかどうかを出力で判断
        # 具体的な成功/失敗は問題ないが、実行自体は成功すべき
        return result.returncode == 0

    def test_restore_contest(self) -> bool:
        """元のコンテストに復元"""
        self.log(f"=== {self.contest1} {self.problem}問題に復元 ===")

        self.run_command(["./cph.sh", self.contest1, "open", self.problem, self.language])

        # 復元されたファイルにエラーが含まれているかチェック
        main_py = self.contest_current / "main.py"
        test_dir = self.contest_current / "test"

        checks = [
            self.check_file_exists(main_py),
            self.check_file_exists(test_dir),
            self.check_file_content(main_py, "raise Exception()"),  # エラーが復元されているか
        ]

        # contest_stock/python/abc300/a/test のデータがcontest_currentに移動されるかチェック
        backup_test_dir = self.contest_stock / self.language / self.contest1 / self.problem / "test"
        if backup_test_dir.exists():
            self.log("バックアップされたテストディレクトリを確認")
            backup_test_files = list(backup_test_dir.glob("sample-*.in"))
            current_test_files = list(test_dir.glob("sample-*.in")) if test_dir.exists() else []

            if len(backup_test_files) > 0 and len(current_test_files) > 0:
                self.log(f"テストファイル復元確認: バックアップ{len(backup_test_files)}個、現在{len(current_test_files)}個")
                checks.append(True)
            else:
                self.log("テストファイル復元に問題があります", "ERROR")
                checks.append(False)

        return all(checks)

    def test_run_test_with_error(self) -> bool:
        """エラーありでのテスト実行"""
        self.log("=== エラーありでのテスト実行 ===")

        result = self.run_command(["./cph.sh", "test", self.problem])

        # エラーがあってもテストコマンド自体は実行される
        return result.returncode == 0

    def run_all_tests(self) -> bool:
        """全テストを実行"""
        self.log("E2Eテスト開始")
        self.log(f"プロジェクトルート: {self.project_root.absolute()}")

        test_steps = [
            ("環境クリーンアップ", self.cleanup_environment),
            ("新しいコンテスト問題を開く", self.test_open_new_contest),
            ("コードにエラーを追加", self.modify_code_with_error),
            ("別のコンテストに切り替え", self.test_switch_contest),
            ("テスト実行", self.test_run_test),
            ("元のコンテストに復元", self.test_restore_contest),
            ("エラーありでのテスト実行", self.test_run_test_with_error),
        ]

        results = []
        for step_name, test_func in test_steps:
            self.log(f"\n{'='*60}")
            self.log(f"テストステップ: {step_name}")
            try:
                result = test_func()
                status = "PASS" if result else "FAIL"
                self.log(f"結果: {status}")
                results.append((step_name, result))
            except Exception as e:
                self.log(f"例外発生: {e}", "ERROR")
                results.append((step_name, False))

        # 結果サマリー
        self.log(f"\n{'='*60}")
        self.log("テスト結果サマリー")
        self.log(f"{'='*60}")

        passed = 0
        for step_name, result in results:
            status = "PASS" if result else "FAIL"
            self.log(f"{step_name}: {status}")
            if result:
                passed += 1

        total = len(results)
        self.log(f"\n合計: {passed}/{total} PASS")

        if passed == total:
            self.log("全テストが成功しました！", "SUCCESS")
            return True
        self.log(f"{total - passed}個のテストが失敗しました", "ERROR")
        return False


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="cph.sh E2E Tests")
    parser.add_argument("--project-root", default=".", help="プロジェクトルートディレクトリ")
    args = parser.parse_args()

    runner = E2ETestRunner(args.project_root)

    if not runner.cph_script.exists():
        print(f"エラー: cph.sh が見つかりません: {runner.cph_script}")
        sys.exit(1)

    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
