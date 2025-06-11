#!/usr/bin/env python3
"""
E2E Tests for cph.sh - Contest Problem Helper
極シンプルなコマンド実行テスト
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main(args):
    """引数を受け取り、テストコマンドを順次実行"""
    project_root = Path(args.project_root)
    
    # クリーンアップ
    dirs = ["contest_current", "contest_stock", "workspace"]
    for d in dirs:
        dir_path = project_root / d
        if dir_path.exists():
            shutil.rmtree(dir_path)
    
    db_file = project_root / "cph_history.db"
    if db_file.exists():
        db_file.unlink()
    
    # テストコマンド列
    commands = [
        ["./cph.sh", "abc300", "open", "a", "python", "local"],
        ["./cph.sh", "abc301", "open", "a", "local"],
        ["./cph.sh", "test", "local"],
        ["./cph.sh", "abc300", "open", "a", "python", "local"],
        ["./cph.sh", "test", "a", "local"]
    ]
    
    # 期待される結果チェック
    def check_test_files_exist():
        test_dir = project_root / "contest_current" / "test"
        if not test_dir.exists():
            return False
        test_files = list(test_dir.glob("*.in"))
        return len(test_files) > 0
    
    expected_checks = [
        check_test_files_exist,
        check_test_files_exist,
        lambda: True,  # テスト実行は成功すれば良い
        check_test_files_exist,
        lambda: True   # エラーありテストも実行されれば良い
    ]
    
    results = []
    for i, cmd in enumerate(commands):
        print(f"[{i+1}] 実行: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"コマンド失敗: {result.stderr}")
            results.append(False)
            break
        else:
            # 期待チェック実行
            check_passed = expected_checks[i]()
            results.append(check_passed)
            status = "PASS" if check_passed else "FAIL"
            print(f"結果: {status}")
            if not check_passed:
                break
    
    # サマリー
    passed = sum(results)
    total = len(results)
    print(f"\n結果: {passed}/{total} PASS")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="cph.sh E2E Tests")
    parser.add_argument("--project-root", default=".", help="プロジェクトルートディレクトリ")
    args = parser.parse_args()
    
    main(args)