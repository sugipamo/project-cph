import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple, Set
import shutil

from models.check_result import CheckResult

def filter_failures_by_path(results: List[Tuple[str, CheckResult]], path_prefix: str, exclude_rules: List[str]) -> List[Tuple[str, CheckResult]]:
    """
    指定されたパスプレフィックスに一致する失敗のみをフィルタリングする
    
    Args:
        results: チェック結果のリスト
        path_prefix: フィルタリングするパスのプレフィックス
        exclude_rules: フィルタリングから除外するルール名のリスト
    """
    if exclude_rules is None:
        exclude_rules = []
    
    filtered_results = []
    
    for rule_name, result in results:
        if rule_name in exclude_rules:
            # 除外ルールはフィルタリングせずそのまま追加
            filtered_results.append((rule_name, result))
            continue
            
        filtered_locations = [
            location for location in result.failure_locations
            if location.file_path.startswith(path_prefix)
        ]
        
        if filtered_locations or not result.failure_locations:
            filtered_result = CheckResult(
                failure_locations=filtered_locations,
                fix_policy=result.fix_policy,
                fix_example_code=result.fix_example_code
            )
            filtered_results.append((rule_name, filtered_result))
    
    return filtered_results

def load_and_execute_rules(rules_dir: Path) -> List[Tuple[str, CheckResult]]:
    """指定ディレクトリ配下の.pyファイルを再帰的に検索し、main関数があるものを実行する"""
    results = []
    
    if not rules_dir.exists():
        print(f"エラー: {rules_dir} ディレクトリが存在しません")
        return results
    
    for py_file in rules_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        relative_path = py_file.relative_to(rules_dir)
        module_name_with_path = str(relative_path.with_suffix('')).replace(os.sep, '_')
        
        try:
            spec = importlib.util.spec_from_file_location(module_name_with_path, py_file)
            if spec is None or spec.loader is None:
                print(f"警告: {py_file} のロードに失敗しました")
                continue
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name_with_path] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'main'):
                result = module.main()
                if hasattr(result, '__class__') and result.__class__.__name__ == 'CheckResult':
                    results.append((module_name_with_path, result))
                else:
                    raise ValueError(f"警告: {module_name_with_path}.main() がCheckResultを返しませんでした: {type(result)}")
                
        except Exception as e:
            raise ValueError(f"エラー: {module_name_with_path} の実行中にエラーが発生しました: {e}")
    
    return results


def save_results_to_files(results: List[Tuple[str, CheckResult]], output_dir: Path) -> None:
    """チェック結果をファイルに保存する"""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for rule_name, result in results:
        if result.failure_locations:
            file_path = output_dir / f"{rule_name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"ルール: {rule_name}\n")
                f.write(f"失敗件数: {len(result.failure_locations)}\n")
                f.write(f"\n修正方針:\n{result.fix_policy}\n" if result.fix_policy else "")
                f.write(f"\n失敗箇所:\n")
                for location in result.failure_locations:
                    f.write(f"{location.file_path}:{location.line_number}\n")


def display_results(results: List[Tuple[str, CheckResult]]) -> None:
    """チェック結果を表示する"""
    if not results:
        print("\n実行可能なルールが見つかりませんでした")
        return
    
    print(f"\n{'='*80}")
    print("品質チェック結果")
    print(f"{'='*80}\n")
    
    total_failures = 0
    rules_with_failures = 0
    
    print(f"実行されたルール数: {len(results)}")
    
    for rule_name, result in results:
        if result.failure_locations:
            rules_with_failures += 1
            print(f"■ ルール: {rule_name}")
            print(f"  失敗件数: {len(result.failure_locations)}")
            
            total_failures += len(result.failure_locations)
            
            # 修正方針を表示
            if result.fix_policy:
                print(f"\n  修正方針:")
                print(f"    {result.fix_policy}")
            
            # 詳細はファイルを参照
            print(f"\n  詳細はsrc_check_result/{rule_name}.txtを参照してください")
            
            print(f"\n{'-'*80}\n")
    
    print(f"総失敗件数: {total_failures}")
    print(f"失敗のあったルール数: {rules_with_failures}")
    print(f"{'='*80}\n")


def main():
    """メイン処理"""
    src_check_dir = Path(__file__).parent
    rules_dir = src_check_dir / "rules"
    auto_correct_dir = src_check_dir / "auto_correct"
    output_dir = src_check_dir / "src_check_result"
    
    results = load_and_execute_rules(rules_dir)
    
    # auto_correctディレクトリのスクリプトも実行
    auto_correct_results = load_and_execute_rules(auto_correct_dir)
    results.extend(auto_correct_results)
    
    # src/以下のファイルのみをフィルタリング（テスト関連のルールは除外）
    test_related_rules = ["pytest_runner"]  # テストに関連するルールのリスト
    filtered_results = filter_failures_by_path(results, "src/", exclude_rules=test_related_rules)
    
    # 結果をファイルに保存
    save_results_to_files(filtered_results, output_dir)
    
    # 結果を表示（失敗が10件を超える場合は修正方針のみ）
    display_results(filtered_results)


if __name__ == "__main__":
    main()