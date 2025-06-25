import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple, Set, Optional, Dict
import shutil
import io
import contextlib
import argparse

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

def load_and_execute_rules(rules_dir: Path, capture_output: bool = True) -> Tuple[List[Tuple[str, CheckResult]], Dict[str, str]]:
    """
    指定ディレクトリ配下の.pyファイルを再帰的に検索し、main関数があるものを実行する
    
    Args:
        rules_dir: ルールファイルが格納されているディレクトリ
        di_container: 依存性注入コンテナ
        capture_output: print出力をキャプチャするかどうか（デフォルト: True）
    
    Returns:
        Tuple[List[Tuple[str, CheckResult]], Dict[str, str]]: 結果リストとキャプチャした出力の辞書
    """
    results = []
    captured_outputs = {}
    
    if not rules_dir.exists():
        print(f"エラー: {rules_dir} ディレクトリが存在しません")
        return results, captured_outputs
    
    for py_file in sorted(rules_dir.rglob("*.py")):
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
                # main関数を引数なしで実行
                def execute_main():
                    return module.main()
                
                # print出力のキャプチャ設定
                if capture_output:
                    output_buffer = io.StringIO()
                    with contextlib.redirect_stdout(output_buffer):
                        result = execute_main()
                    
                    # キャプチャした出力を保存
                    captured_output = output_buffer.getvalue()
                    if captured_output:
                        captured_outputs[module_name_with_path] = captured_output
                else:
                    # キャプチャしない場合は通常実行
                    result = execute_main()
                    
                if hasattr(result, '__class__') and result.__class__.__name__ == 'CheckResult':
                    results.append((module_name_with_path, result))
                else:
                    raise ValueError(f"警告: {module_name_with_path}.main() がCheckResultを返しませんでした: {type(result)}")
                
        except Exception as e:
            raise ValueError(f"エラー: {module_name_with_path} の実行中にエラーが発生しました: {e}")
    
    return results, captured_outputs


def save_results_to_files(results: List[Tuple[str, CheckResult]], output_dir: Path, captured_outputs: Optional[Dict[str, str]] = None) -> None:
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
                
                # キャプチャした出力を追加
                if captured_outputs and rule_name in captured_outputs:
                    f.write(f"\n\n実行時出力:\n")
                    f.write(f"{'-'*40}\n")
                    f.write(captured_outputs[rule_name])
                    f.write(f"{'-'*40}\n")


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
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='コード品質チェックツール')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='ルール実行時のprint出力を表示')
    args = parser.parse_args()
    
    src_check_dir = Path(__file__).parent
    src_processors_dir = src_check_dir / "src_processors"
    transformers_dir = src_check_dir / "transformers"
    output_dir = src_check_dir / "src_check_result"
    
    
    # verboseモードの場合はキャプチャしない
    capture_output = not args.verbose
    
    # 全体の結果リストとキャプチャした出力を保存
    all_results = []
    all_captured_outputs = {}
    
    # まずtransformersを適用
    transformer_results, transformer_outputs = load_and_execute_rules(
        transformers_dir, capture_output=capture_output
    )
    all_results.extend(transformer_results)
    all_captured_outputs.update(transformer_outputs)
    
    # その後src_processorsディレクトリ全体を再帰的に読み込み
    src_processor_results, src_processor_outputs = load_and_execute_rules(
        src_processors_dir, capture_output=capture_output
    )
    all_results.extend(src_processor_results)
    all_captured_outputs.update(src_processor_outputs)
    
    # src/以下のファイルのみをフィルタリング（テスト関連のルールは除外）
    test_related_rules = ["pytest_runner"]  # テストに関連するルールのリスト
    filtered_results = filter_failures_by_path(all_results, "src/", exclude_rules=test_related_rules)
    
    # フィルタリングされた結果に対応するキャプチャ出力も抽出
    filtered_outputs = {
        rule_name: output 
        for rule_name, output in all_captured_outputs.items()
        if any(r[0] == rule_name for r in filtered_results)
    }
    
    # 結果をファイルに保存
    save_results_to_files(filtered_results, output_dir, filtered_outputs)
    
    # 結果を表示（失敗が10件を超える場合は修正方針のみ）
    display_results(filtered_results)


if __name__ == "__main__":
    main()