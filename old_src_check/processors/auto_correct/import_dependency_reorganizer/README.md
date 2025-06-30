# インポート依存関係ベースフォルダ構造整理ツール

Pythonプロジェクトのファイルを、インポート依存関係に基づいて自動的に整理するツールです。

## 概要

このツールは以下の機能を提供します：

1. **依存関係解析**: ASTを使用してPythonファイル間の依存関係を解析
2. **深度計算**: 各ファイルの依存深度を計算（トポロジカルソート）
3. **自動整理**: 深度に基づいてファイルを適切なフォルダに移動
4. **インポート更新**: 移動後も動作するようインポート文を自動更新
5. **安全性**: バックアップとロールバック機能

## インストール

```bash
# プロジェクトルートで実行
cd src_check/src_processors/auto_correct/import_dependency_reorganizer
```

## 基本的な使い方

### 1. シミュレーションモード（デフォルト）

```python
from src_check.src_processors.auto_correct.import_dependency_reorganizer.main_v2 import main

# 移動計画を表示するだけで実際の変更は行わない
result = main()
print(result.fix_policy)
```

### 2. 実行モード

```python
from src_check.src_processors.auto_correct.import_dependency_reorganizer.main_v2 import main
from src_check.src_processors.auto_correct.import_dependency_reorganizer.config import ReorganizerConfig

# 設定を作成
config = ReorganizerConfig(
    execute_mode=True,
    dry_run=False,
    max_file_count=250
)

# 実際にファイルを移動
result = main(config)
```

### 3. 設定ファイルを使用

```bash
# サンプル設定ファイルを生成
python config.py

# 設定ファイルを編集
vim reorganizer_config_example.json

# 設定ファイルを指定して実行
python main_v2.py --config reorganizer_config_example.json --execute
```

## 設定オプション

### 基本設定

- `max_file_count`: 処理可能な最大ファイル数（デフォルト: 250）
- `max_depth`: 最大依存深度（デフォルト: 5）
- `execute_mode`: 実行モードを有効化（デフォルト: False）
- `dry_run`: ドライラン（デフォルト: True）

### 解析設定

- `exclude_patterns`: 除外するファイルパターン（例: "__pycache__", "*.pyc"）
- `include_test_files`: テストファイルを含めるか（デフォルト: False）
- `exclude_type_checking`: TYPE_CHECKINGブロックを除外（デフォルト: True）

### フォルダマッピング

```json
{
  "depth_folder_mapping": {
    "0": "",          // ルートに残す
    "1": "core",      // 基本モジュール
    "2": "services",  // サービス層
    "3": "handlers",  // ハンドラー層
    "4": "controllers", // コントローラー層
    "5": "app"        // アプリケーション層
  }
}
```

### カスタムフォルダ名

```json
{
  "folder_name_patterns": {
    "*_manager": "{name}_mgmt",
    "*_service": "{name}_svc",
    "*_handler": "{name}_hdlr",
    "config*": "configuration",
    "util*": "utilities"
  }
}
```

## 実行例

### 小規模プロジェクトの整理

```python
# 1. 設定作成
config = ReorganizerConfig(
    max_file_count=50,
    max_depth=3,
    log_level="DEBUG",
    verbose=True
)

# 2. シミュレーション実行
result = main(config)
# 出力: "シミュレーション完了: 25ファイルの移動を計画"

# 3. 確認後、実際に実行
config.execute_mode = True
config.dry_run = False
result = main(config)
# 出力: "ファイル移動完了: 25/25成功"
```

### 大規模プロジェクトの段階的整理

```python
# 特定のモジュールのみを対象
config = ReorganizerConfig(
    exclude_patterns=["test_*", "docs/*", "scripts/*"],
    max_depth=4,
    create_init_files=True,
    cleanup_empty_dirs=True
)

# バックアップを確認
config.use_git_backup = True  # Gitでバックアップ

# 実行
result = main(config, execute_mode=True)
```

## トラブルシューティング

### 循環依存エラー

```
エラー: 循環依存が検出されました
解決方法:
1. 検出された循環を確認: module_a → module_b → module_a
2. 遅延インポートまたはTYPE_CHECKINGを使用して解決
3. または config.ignore_circular_deps = True で無視
```

### インポートエラー

```
エラー: インポートが解決できません
解決方法:
1. ログファイルで詳細を確認
2. 相対インポートが正しく変換されているか確認
3. __init__.pyが適切に配置されているか確認
```

### ファイル移動エラー

```
エラー: ファイル移動に失敗
解決方法:
1. ファイルの書き込み権限を確認
2. 移動先に同名ファイルがないか確認
3. バックアップからロールバック可能
```

## 高度な使い方

### カスタムロガー設定

```python
from logger import setup_logger

# 詳細ログをファイルに記録
logger = setup_logger(
    log_level="DEBUG",
    log_file=Path("logs/reorganizer.log"),
    enable_console=False
)
```

### エラーハンドリング

```python
from errors import ErrorCollector

# エラー収集器を使用
collector = ErrorCollector()

# 実行後にエラーレポートを取得
if collector.has_errors():
    print(collector.format_report())
    
    # JSON形式で保存
    summary = collector.get_summary()
    with open("errors.json", "w") as f:
        json.dump(summary, f, indent=2)
```

### プログラムからの統合

```python
# src_checkシステムと統合
from models.check_result import CheckResult

def check_and_reorganize():
    config = ReorganizerConfig.from_file("my_config.json")
    result = main(config)
    
    if result.failure_locations:
        # エラー処理
        for failure in result.failure_locations:
            print(f"エラー: {failure.file_path}:{failure.line_number}")
    
    return result
```

## 制限事項

1. **ファイル数制限**: デフォルトで250ファイルまで
2. **Python専用**: .pyファイルのみ対象
3. **src/ディレクトリ**: 現在はsrc/配下のみ対象
4. **循環依存**: 検出時は手動解決が必要

## 今後の拡張予定

- [ ] 並列処理による高速化
- [ ] 動的インポート（importlib）の検出
- [ ] 依存関係グラフの可視化
- [ ] インクリメンタル実行
- [ ] IDE統合（VSCode拡張）

## ライセンス

プロジェクトのライセンスに準拠

## 貢献

バグ報告や機能要望は、プロジェクトのイシュートラッカーまでお願いします。