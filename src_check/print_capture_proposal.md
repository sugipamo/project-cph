# src_check print出力制御の提案

## 概要
`src_check/main.py`でルールモジュールを動的に読み込む際、各モジュールの`print`出力を制御する機能を実装する。

## 背景
- 現在、`src_check`内の各ルールチェッカーが`print`文を使用している
- チェック実行時に不要な出力が発生し、結果の可読性が低下
- 各ルールファイルを個別に修正するのは実装コストが高い

## 提案する実装方法

### 1. contextlib.redirect_stdoutを使用した実装

```python
# src_check/main.py の load_and_execute_rules 関数内に追加

import io
import contextlib
from typing import List, Tuple, Set, Optional

def load_and_execute_rules(rules_dir: Path, di_container: DIContainer, capture_output: bool = True) -> List[Tuple[str, CheckResult]]:
    """
    指定ディレクトリ配下の.pyファイルを再帰的に検索し、main関数があるものを実行する
    
    Args:
        rules_dir: ルールファイルが格納されているディレクトリ
        di_container: 依存性注入コンテナ
        capture_output: print出力をキャプチャするかどうか（デフォルト: True）
    """
    results = []
    captured_outputs = {}  # ルール名と出力のマッピング
    
    # ... 既存のファイル探索処理 ...
    
    # main関数の実行部分を修正
    if hasattr(module, 'main'):
        # print出力のキャプチャ設定
        if capture_output:
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                result = execute_main_function(module, di_container)
            
            # キャプチャした出力を保存
            captured_output = output_buffer.getvalue()
            if captured_output:
                captured_outputs[module_name_with_path] = captured_output
        else:
            # キャプチャしない場合は通常実行
            result = execute_main_function(module, di_container)
```

### 2. オプション機能の追加

```python
# main関数にコマンドライン引数を追加
def main():
    import argparse
    parser = argparse.ArgumentParser(description='コード品質チェックツール')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='ルール実行時のprint出力を表示')
    parser.add_argument('--save-logs', action='store_true',
                       help='キャプチャした出力をログファイルに保存')
    
    args = parser.parse_args()
    
    # DIコンテナを初期化
    di_container = DIContainer()
    
    # verboseモードの場合はキャプチャしない
    capture_output = not args.verbose
    
    # ルールを実行
    results = load_and_execute_rules(
        src_processors_dir, 
        di_container, 
        capture_output=capture_output
    )
```

### 3. キャプチャした出力の活用

```python
def save_captured_outputs(captured_outputs: dict, output_dir: Path):
    """キャプチャした出力をファイルに保存"""
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    for rule_name, output in captured_outputs.items():
        log_file = logs_dir / f"{rule_name}.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(output)
```

## メリット

1. **実装コストが低い**: 標準ライブラリのみで実装可能
2. **非侵襲的**: 既存のルールファイルを一切変更しない
3. **柔軟性**: 必要に応じて出力の表示/非表示を切り替え可能
4. **デバッグ容易**: `--verbose`オプションで元の動作を確認可能
5. **後方互換性**: 既存の動作を変更せず、オプトインで機能追加

## デメリット

1. **stderr出力は制御不可**: `print(..., file=sys.stderr)`は別途対応が必要
2. **マルチスレッド非対応**: 並列実行時は考慮が必要

## 実装優先度

この方法は以下の理由から、AST変換アプローチより推奨されます：

- **シンプル**: 20行程度の追加で実装可能
- **安全**: 実行時エラーのリスクが低い
- **保守性**: 標準的なPythonの機能を使用
- **テスト容易**: 単体テストが書きやすい

## 段階的な実装計画

1. **Phase 1**: 基本的なprint出力キャプチャ機能の実装
2. **Phase 2**: コマンドライン引数の追加
3. **Phase 3**: キャプチャした出力の保存機能（必要に応じて）

この提案により、最小限の実装コストで効果的なprint出力制御が実現できます。