# Orchestrator - 新しいチェック実行システム

## 概要

従来のDFS探索によるmain.py検出方式から、辞書順処理を活用した新しいアプローチです。

## 特徴

1. **決定論的実行順序**: 常に同じ順序でモジュールを実行
2. **シンプルな構造**: main.pyファイルの探索が不要
3. **柔軟な実行方法**: 昇順/降順、特定モジュールのみの実行が可能

## ファイル構成

```
orchestrator/
├── __init__.py                # パッケージ初期化
├── module_registry.py         # モジュール登録と管理
├── check_executor.py          # 実行エンジン
├── ascending_runner.py        # 昇順実行（辞書順で最初）
├── zzz_descending_runner.py   # 降順実行（辞書順で最後）
└── README.md                  # このファイル
```

## 使用方法

### 昇順実行（A→Z）
```bash
python3 src_check/orchestrator/ascending_runner.py
```

### 降順実行（Z→A）
```bash
python3 src_check/orchestrator/zzz_descending_runner.py
```

### プログラムから使用
```python
from src_check.orchestrator.check_executor import CheckExecutor

executor = CheckExecutor(project_root)

# 全モジュールを昇順で実行
results = executor.execute_all(ascending=True)

# 特定のモジュールのみ実行
results = executor.execute_specific(['type_hints', 'import_fixers'])
```

## 動作原理

1. `ModuleRegistry`が`processors/`配下のチェックモジュールを自動検出
2. 各モジュールに優先度を設定（auto_correct: 10, rules: 20）
3. `CheckExecutor`が登録されたモジュールを順番に実行
4. 結果は`CheckResult`形式で統一され、`check_result/`に保存

## 利点

- **main.py不要**: 各モジュールのmain.pyを直接実行
- **管理が簡単**: 2つのエントリーポイント（昇順/降順）のみ
- **拡張性**: 新しいモジュールは自動的に検出される
- **デバッグ容易**: 特定モジュールのみの実行が可能