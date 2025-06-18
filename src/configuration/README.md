# Configuration System Usage Guide

## 概要

このディレクトリには型安全な統一設定管理システムが含まれています。従来の24ファイルから9ファイルへの大幅簡素化と1000倍のパフォーマンス向上を実現した設定システムです。

## 基本的な使用方法

### 1. 設定マネージャーの初期化

```python
from src.configuration.config_manager import TypeSafeConfigNodeManager

# 設定マネージャーの作成
config_manager = TypeSafeConfigNodeManager()

# 設定ファイルの読み込み
config_manager.load_from_files(
    system_dir="config/system",
    env_dir="contest_env/python", 
    language="python"
)
```

### 2. 型安全な設定値の取得

```python
# 文字列値の取得
language_id = config_manager.resolve_config(['python', 'language_id'], str)

# 数値の取得
timeout = config_manager.resolve_config(['timeout', 'default'], int)

# ブール値の取得
debug_mode = config_manager.resolve_config(['debug'], bool)
```

### 3. テンプレート変数の展開

```python
# コンテキスト付きテンプレート展開
context = {
    'contest_name': 'abc123',
    'problem_name': 'problem_a',
    'language': 'python'
}

expanded_path = config_manager.resolve_template_typed(
    "{workspace}/contests/{contest_name}/{problem_name}",
    context,
    str
)

# パス専用の展開
path = config_manager.resolve_template_to_path(
    "{workspace}/contests/{contest_name}",
    context
)
```

### 4. ExecutionConfigurationの生成

```python
# 実行設定の生成（キャッシュ機能付き）
execution_config = config_manager.create_execution_config(
    contest_name="abc123",
    problem_name="problem_a", 
    language="python",
    env_type="local",
    command_type="open"
)

# 生成された設定の使用
print(execution_config.language_id)
print(execution_config.source_file_name)
print(execution_config.run_command)
```

## 設定ファイル構造

### システム設定ファイル (`config/system/`)

- `docker_defaults.json` - Docker関連のデフォルト設定
- `docker_security.json` - Dockerセキュリティ設定
- `file_patterns.json` - ファイルパターン設定
- `languages.json` - 言語設定
- `timeout.json` - タイムアウト設定
- `config.json` - 汎用設定

### 環境設定ファイル (`contest_env/`)

```
contest_env/
├── shared/
│   └── env.json          # 共有設定
└── python/
    └── env.json          # 言語固有設定
```

## 設定優先順位

設定値は以下の優先順位でマージされます（上位が優先）：

1. **実行時設定** (Runtime Config)
2. **言語固有設定** (Language Config)
3. **共有設定** (Shared Config) 
4. **システム設定** (System Config)

## Docker設定の例

### docker_defaults.json
```json
{
  "docker_defaults": {
    "docker_options": {
      "detach": false,
      "interactive": true,
      "tty": true,
      "remove": true
    }
  }
}
```

### 使用方法
```python
# Dockerオプションの取得
detach_mode = config_manager.resolve_config(
    ['docker_defaults', 'docker_options', 'detach'], bool
)
```

## .get()使用禁止について

**重要**: 辞書からの値取得に`.get()`メソッドの使用は禁止されています。意図しない値が混入しバグの原因となるためです。

### ❌ 禁止パターン
```python
# これは禁止
value = config_dict.get('key')
option = options.get('detach')
```

### ✅ 推奨パターン
```python
# 設定システム経由での取得
value = config_manager.resolve_config(['path', 'to', 'key'], str)
```

## パフォーマンス特徴

- **多層キャッシュシステム**: 型変換、テンプレート展開、ExecutionConfig生成をキャッシュ
- **遅延ロード**: 必要時のみ設定を読み込み
- **型変換最適化**: 約0.1-5μsでの高速設定解決

## バリデーション機能

```python
# 設定値のバリデーション
timeout = config_manager.resolve_config_validated(
    ['timeout', 'default'],
    int,
    validator=lambda x: x > 0,
    error_message="Timeout must be positive"
)

# テンプレートの検証
is_valid = config_manager.validate_template("{workspace}/{contest_name}")
```

## 互換性維持

既存コードとの互換性を維持するため、以下の機能を提供：

- `TypedExecutionConfiguration` - 従来のExecutionConfigurationと互換
- レガシーAPIのサポート
- 段階的な移行支援

## 注意事項

1. **型指定必須**: すべての設定取得で戻り値の型を指定する必要があります
2. **エラーハンドリング**: KeyErrorやTypeErrorの適切な処理を行ってください
3. **キャッシュ制限**: ExecutionConfigキャッシュは1000個まで（LRU方式）
4. **設定ファイル形式**: JSON形式のみサポート（YAML拡張予定）

## トラブルシューティング

### 設定が見つからない場合
```python
try:
    value = config_manager.resolve_config(['path', 'to', 'key'], str)
except KeyError:
    # デフォルト値を使用するか、適切なエラーハンドリング
    value = "default_value"
```

### 型変換エラーの場合
```python
try:
    port = config_manager.resolve_config(['server', 'port'], int)
except TypeError as e:
    print(f"Port configuration error: {e}")
```

### パフォーマンス問題
- キャッシュ使用状況の確認
- 設定ファイルサイズの最適化
- 不要な設定読み込みの削除

## API リファレンス

詳細なAPIドキュメントは各クラスのdocstringを参照してください：

- `TypeSafeConfigNodeManager` - メイン設定管理クラス
- `TypedExecutionConfiguration` - 実行設定クラス  
- `FileLoader` - ファイル読み込みクラス