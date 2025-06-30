# src_check - 品質管理ツール群

## 概要

src_checkは、src/配下の本番コードに対して品質管理を行うツール群です。動的インポートを活用し、雑に書いたスクリプトを高速に開発できる環境を提供します。重複を許すことで、コードの変更が意図しない結果を招くことを回避する思想で設計されています。

## 設計思想

- **高速開発**: 動的インポートにより、各チェックモジュールを独立して開発・実行可能
- **重複許容**: 同じチェックを複数の視点から実装できる（冗長性による安全性）
- **実行時隔離**: 各モジュールは独立した名前空間で実行され、相互干渉を防ぐ
- **柔軟な拡張**: main.pyを持つディレクトリを追加するだけで新しいチェックを追加可能

## ディレクトリ構造

```
src_check/
├── main.py                    # メインエントリーポイント
├── core/                      # コア機能
│   ├── dynamic_importer.py    # 動的インポート管理
│   ├── module_explorer.py     # モジュール探索（DFS）
│   └── result_writer.py       # 結果出力
├── processors/                # チェック処理群
│   ├── auto_correct/         # 自動修正機能
│   │   ├── argument_processors/    # 引数処理
│   │   ├── file_organizers/       # ファイル整理
│   │   ├── import_dependency_reorganizer/  # インポート依存関係整理
│   │   ├── import_fixers/         # インポート修正
│   │   ├── remnant_cleaners/      # 残骸クリーナー
│   │   └── type_hints/            # 型ヒント追加
│   └── rules/                # チェックルール
│       ├── default_value_checker.py    # デフォルト値チェック
│       ├── fallback_checker.py         # フォールバック処理チェック
│       ├── infrastructure_operations_checker.py  # 副作用チェック
│       └── ... (その他多数のルール)
├── orchestrator/             # 別実行方式（辞書順実行）
├── check_result/             # チェック結果出力
└── auto_correct_log/         # 自動修正ログ
```

## 動作原理

### 1. 動的インポートシステム

```python
# core/dynamic_importer.py
- importlib.utilを使用してmain.pyを動的に読み込み
- sys.modulesに一時的に追加し、実行後にクリーンアップ
- 各モジュールは独立した名前空間で実行される
```

### 2. モジュール探索（DFS）

```python
# core/module_explorer.py
- processors/配下をDFS探索
- main.pyを持つディレクトリを自動検出
- 実行順序は探索順（深さ優先）
```

### 3. 実行フロー

1. **インポート事前チェック**: 壊れたインポートを修正
2. **モジュール探索**: processors/配下のmain.pyを発見
3. **動的実行**: 各モジュールを順次実行
4. **結果集約**: CheckResult形式で統一された結果を収集
5. **レポート生成**: check_result/に結果を出力
6. **インポート事後チェック**: ファイル移動後のインポートを修正

## 使い方

### 基本実行

```bash
# src_checkのすべてのチェックを実行
python src_check/main.py
```

### 結果の確認

```bash
# サマリーを確認
cat src_check/check_result/summary.txt

# 個別のチェック結果を確認
cat src_check/check_result/default_value_checker.txt
```

### 新しいチェックの追加

1. `processors/rules/`または`processors/auto_correct/`に新しいディレクトリを作成
2. `main.py`を作成し、`main()`関数を実装
3. `CheckResult`を返すように実装

```python
# 例: processors/rules/my_new_checker/main.py
from pathlib import Path
from models.check_result import CheckResult, FailureLocation

def main() -> CheckResult:
    # チェック処理を実装
    violations = []
    
    # src/配下のファイルをチェック
    src_dir = Path(__file__).parent.parent.parent.parent / 'src'
    # ... チェック処理 ...
    
    return CheckResult(
        title="my_new_checker",
        failure_locations=violations,
        fix_policy="修正方針を記述",
        fix_example_code="修正例を記述"
    )
```

## チェック項目一覧

### ルールチェック（processors/rules/）

- **default_value_checker**: 引数のデフォルト値使用を検出
- **fallback_checker**: フォールバック処理を検出
- **infrastructure_operations_checker**: infrastructure以外での副作用を検出
- **clean_architecture_checker**: クリーンアーキテクチャ違反を検出
- **import_checker**: インポートルール違反を検出
- その他多数

### 自動修正（processors/auto_correct/）

- **argument_processors**: 不要な引数を削除
- **file_organizers**: ファイルを論理的に整理
- **import_dependency_reorganizer**: 依存関係に基づいてファイルを再配置
- **import_fixers**: 壊れたインポートを修正
- **type_hints**: 型ヒントを自動追加

## 重複を許す理由

src_checkでは意図的に重複を許容しています：

1. **異なる視点**: 同じ問題を異なるアプローチでチェック可能
2. **段階的改善**: 既存チェックを壊さずに新しい実装を試せる
3. **A/Bテスト**: 複数の実装を比較して最適なものを選択
4. **安全性**: 一つのチェックが失敗しても他でカバー可能

## 注意事項

- src_check内のコードは品質管理用であり、本番コードではない
- 高速開発を優先し、完璧なコード品質は求めない
- 動的インポートにより実行時エラーが発生する可能性がある
- 各モジュールは独立して動作することを前提とする

## トラブルシューティング

### インポートエラー

```
エラー: モジュール仕様の作成に失敗
解決: main.pyの構文エラーを確認
```

### 実行時エラー

```
エラー: main関数実行エラー
解決: main()関数がCheckResultを返しているか確認
```

### 結果が出力されない

```
原因: main()関数が見つからない
解決: def main(): が正しく定義されているか確認
```

## 拡張方法

### 新しい実行方式

orchestrator/のように、別の実行方式を追加可能：

- 並列実行
- 条件付き実行
- インタラクティブ実行

### カスタム結果フォーマット

core/result_writer.pyを拡張して、異なる出力形式に対応：

- JSON形式
- HTML形式
- CI/CD統合用フォーマット

## まとめ

src_checkは、本番コードの品質を多角的にチェックするための柔軟なフレームワークです。動的インポートと重複許容により、高速な開発サイクルを実現しながら、包括的な品質管理を可能にします。