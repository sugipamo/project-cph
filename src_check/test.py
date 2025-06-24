import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple

from models.check_result import CheckResult


def load_and_execute_rules(rules_dir: Path) -> List[Tuple[str, CheckResult]]:
    """rules配下の.pyファイルを動的にインポートし、main関数を実行する"""
    results = []
    
    if not rules_dir.exists():
        print(f"エラー: {rules_dir} ディレクトリが存在しません")
        return results
    
    for py_file in rules_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        module_name = py_file.stem
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                print(f"警告: {py_file} のロードに失敗しました")
                continue
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'main'):
                result = module.main()
                if isinstance(result, CheckResult):
                    results.append((module_name, result))
                else:
                    print(f"警告: {module_name}.main() がCheckResultを返しませんでした")
            else:
                print(f"警告: {module_name} にmain関数が見つかりません")
                
        except Exception as e:
            print(f"エラー: {module_name} の実行中にエラーが発生しました: {e}")
    
    return results


def display_results(results: List[Tuple[str, CheckResult]]) -> None:
    """チェック結果を表示する"""
    if not results:
        print("\n実行可能なルールが見つかりませんでした")
        return
    
    print(f"\n{'='*80}")
    print("品質チェック結果")
    print(f"{'='*80}\n")
    
    total_failures = 0
    
    for rule_name, result in results:
        print(f"■ ルール: {rule_name}")
        print(f"  失敗件数: {len(result.failure_locations)}")
        
        if result.failure_locations:
            total_failures += len(result.failure_locations)
            print(f"\n  失敗箇所:")
            for location in result.failure_locations:
                print(f"    - {location.file_path}:{location.line_number}")
            
            if result.fix_policy:
                print(f"\n  修正方針:")
                print(f"    {result.fix_policy}")
            
            if result.fix_example_code:
                print(f"\n  修正例:")
                print("    ```")
                for line in result.fix_example_code.split('\n'):
                    print(f"    {line}")
                print("    ```")
        else:
            print("  ✓ すべてのチェックをパスしました")
        
        print(f"\n{'-'*80}\n")
    
    print(f"総失敗件数: {total_failures}")
    print(f"{'='*80}\n")


def main():
    """メイン処理"""
    src_check_dir = Path(__file__).parent
    rules_dir = src_check_dir / "rules"
    
    results = load_and_execute_rules(rules_dir)
    display_results(results)


if __name__ == "__main__":
    main()