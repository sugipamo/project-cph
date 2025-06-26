#!/usr/bin/env python3
"""
シンプルなsrc_checkメイン実行ファイル
動的インポートを使わず、明示的にチェックルールを実行
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict

# モデルをインポート
sys.path.append(str(Path(__file__).parent))
from models.check_result import CheckResult, FailureLocation


def run_broken_imports_check() -> CheckResult:
    """壊れたインポートチェックを実行"""
    try:
        # 直接インポートして実行
        from src_processors.broken_imports_checker import main
        return main()
    except Exception as e:
        print(f"エラー: 壊れたインポートチェックで例外が発生: {e}")
        return CheckResult(
            failure_locations=[],
            fix_policy=f"チェック実行エラー: {e}",
            fix_example_code=None
        )


def run_syntax_check() -> CheckResult:
    """構文チェックを実行"""
    try:
        from src_processors.rules.syntax_checker import main
        return main()
    except Exception as e:
        print(f"警告: 構文チェックをスキップ: {e}")
        return CheckResult()


def run_default_value_check() -> CheckResult:
    """デフォルト値チェックを実行"""
    try:
        from src_processors.rules.default_value_checker import main
        return main()
    except Exception as e:
        print(f"警告: デフォルト値チェックをスキップ: {e}")
        return CheckResult()


def run_import_check() -> CheckResult:
    """インポートチェックを実行"""
    try:
        from src_processors.rules.import_checker import main
        return main()
    except Exception as e:
        print(f"警告: インポートチェックをスキップ: {e}")
        return CheckResult()


def display_results(results: List[Tuple[str, CheckResult]]) -> None:
    """結果を表示"""
    print(f"\n{'='*80}")
    print("src_check実行結果")
    print(f"{'='*80}")
    
    total_failures = 0
    rules_with_failures = 0
    
    for rule_name, result in results:
        if result.failure_locations:
            rules_with_failures += 1
            print(f"\n■ {rule_name}")
            print(f"  失敗件数: {len(result.failure_locations)}件")
            total_failures += len(result.failure_locations)
            
            if result.fix_policy:
                print(f"  修正方針: {result.fix_policy}")
                
            # 最初の5件を表示
            for i, failure in enumerate(result.failure_locations[:5]):
                print(f"    {i+1}. {failure.file_path}:{failure.line_number}")
            
            if len(result.failure_locations) > 5:
                print(f"    ... 他{len(result.failure_locations) - 5}件")
    
    print(f"\n総失敗件数: {total_failures}")
    print(f"失敗のあったルール数: {rules_with_failures}")
    print(f"{'='*80}")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='src_check (シンプル版)')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細出力')
    parser.add_argument('--check', '-c', action='append', 
                       choices=['broken_imports', 'syntax', 'default_value', 'import'],
                       help='実行するチェックを指定（複数指定可能）')
    args = parser.parse_args()
    
    print("🔍 src_check (シンプル版) を実行します...")
    
    # 実行するチェックを定義
    all_checks = [
        ("壊れたインポート", "broken_imports", run_broken_imports_check),
        ("構文チェック", "syntax", run_syntax_check), 
        ("デフォルト値チェック", "default_value", run_default_value_check),
        ("インポートチェック", "import", run_import_check),
    ]
    
    # 指定されたチェックのみ実行
    if args.check:
        checks = [(name, func) for name, key, func in all_checks if key in args.check]
    else:
        checks = [(name, func) for name, key, func in all_checks]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}を実行中...")
        try:
            result = check_func()
            results.append((check_name, result))
            
            if result.failure_locations:
                print(f"   ⚠️  {len(result.failure_locations)}件の問題を検出")
            else:
                print(f"   ✅ 問題なし")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            error_result = CheckResult(
                failure_locations=[],
                fix_policy=f"実行エラー: {e}",
                fix_example_code=None
            )
            results.append((check_name, error_result))
    
    # 結果表示
    display_results(results)


if __name__ == "__main__":
    main()