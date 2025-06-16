# JSON設定読み込み機能のデータフロー分析

## 概要

現在のコードベースにはJSON設定読み込みに関して過剰な実装が存在しています。複数の類似したクラスと重複した責任が混在しており、データフローが複雑化しています。

## 現在のJSON読み込み実装

### 1. 主要なクラス

#### JsonConfigLoader (`src/infrastructure/config/json_config_loader.py`)
- **行数**: 329行
- **主な責任**:
  - `contest_env/` ディレクトリからenv.jsonファイルを読み込み
  - 共有設定 (`shared/env.json`) と言語固有設定のマージ
  - システム設定ファイルの読み込み
  - ファイルパターン設定の取得
- **問題点**: 単一のクラスが多すぎる責任を持っている

#### UnifiedConfigLoader (`src/infrastructure/config/unified_config_loader.py`)
- **行数**: 228行
- **主な責任**:
  - JsonConfigLoaderと同様の機能を持つ統合版
  - FileProviderを通した副作用の分離
  - 新ConfigurationSource形式をサポート
- **問題点**: JsonConfigLoaderとの機能重複

#### ConfigurationLoader (`src/configuration/loaders/configuration_loader.py`)
- **行数**: 103行
- **主な責任**:
  - システム設定とenv設定の読み込み
  - ConfigurationSourceオブジェクトの生成
- **問題点**: UnifiedConfigLoaderとの機能重複

#### ExecutionConfigurationFactory (`src/configuration/factories/configuration_factory.py`)
- **行数**: 262行
- **主な責任**:
  - コマンドライン引数からExecutionConfigurationを生成
  - 設定のマージとExecutionConfigurationオブジェクトの構築
  - SQLiteからの前回値読み込み（行数222-247）
- **問題点**: ファクトリーパターンの中でSQLite操作を直接実行

## データフロー

### 1. アプリケーション起動フロー

```
CLIApplication.execute_cli_application()
├── build_operations() → DIContainer設定
├── parse_user_input() → コンテキスト解析
│   ├── _load_current_context_sqlite() → SQLiteから既存設定を読み込み
│   ├── JsonConfigLoader.get_env_config() → JSON設定読み込み
│   └── create_new_execution_context() → 新設定システムでコンテキスト作成
└── _execute_workflow() → ワークフロー実行
```

### 2. JSON設定読み込みフロー

```
env.json読み込み
├── システム設定 (config/system/*.json) [最低優先度]
├── 共有設定 (contest_env/shared/env.json)
└── 言語固有設定 (contest_env/{language}/env.json) [最高優先度]
↓
deep_merge() による設定マージ
↓
ExecutionContext/ExecutionConfiguration生成
```

### 3. 設定使用フロー

```
WorkflowExecutionService.execute_workflow()
├── _prepare_workflow_steps()
│   └── StepGenerationService → file_patterns使用
├── _execute_main_workflow()
│   └── UnifiedDriver → 各種設定値使用
└── WorkflowExecutionResult生成
```

## 問題点詳細

### 1. クラス設計の重複

**JsonConfigLoader vs UnifiedConfigLoader:**
- 両方とも同じJSON読み込み機能を実装
- メソッド名も類似 (`get_env_config`, `get_language_config`)
- UnifiedConfigLoaderはFileProviderを使用しているが、実質的な機能差はない

**ConfigurationLoader vs UnifiedConfigLoader:**
- 両方ともシステム設定+環境設定の読み込みを実装
- ConfigurationLoaderは103行でよりシンプルだが機能は限定的

### 2. ファイルパターン変換の複雑さ

**StepGenerationService (`step_generation_service.py:26-39`)**:
```python
# JsonConfigLoaderの形式からシンプルな形式に変換（必要な場合）
file_patterns = {}
for pattern_name, pattern_data in raw_patterns.items():
    if isinstance(pattern_data, dict):
        # {"workspace": ["patterns"], ...} の形式の場合
        for location in ['workspace', 'contest_current', 'contest_stock']:
            if pattern_data.get(location):
                file_patterns[pattern_name] = pattern_data[location]
                break
```

同様の変換ロジックが複数箇所に散在:
- `configuration_factory.py:94-107`
- `step_generation_service.py:78-84`

### 3. SQLite直接操作

**ExecutionConfigurationFactory (`configuration_factory.py:222-247`)**:
```python
# 直接SQLiteからデータを読み込む
import sqlite3
if os.path.exists('cph_history.db'):
    conn = sqlite3.connect('cph_history.db')
    # ... 直接SQL操作
```

ファクトリーパターンの中でインフラストラクチャ層の操作を直接実行している。

### 4. 設定形式の不統一

**shared/env.json の形式**:
```json
{
  "shared": {
    "paths": {...},
    "commands": {...}
  }
}
```

**アプリケーション内での使用**:
- あるところでは `config["shared"]["paths"]`
- 別のところでは `config.get("paths")`
- マージ後の形式とマージ前の形式が混在

## 推奨される改善策

### 1. 責任の分離

```
ConfigLoader (単一責任)
├── SystemConfigLoader → システム設定のみ
├── EnvConfigLoader → env.json読み込みのみ
└── ConfigMerger → 設定マージロジックのみ
```

### 2. 設定オブジェクトの統一

```
Configuration (Value Object)
├── paths: PathConfig
├── commands: CommandConfig
├── file_patterns: FilePatternConfig
└── runtime: RuntimeConfig
```

### 3. データアクセス層の分離

```
ConfigurationRepository
├── loadSystemConfig()
├── loadEnvConfig()
└── saveCurrentContext()
```

### 4. 重複クラスの整理

- **JsonConfigLoader** → 廃止（機能をより小さなクラスに分割）
- **UnifiedConfigLoader** → 廃止（ConfigLoaderで置き換え）
- **ConfigurationLoader** → 機能拡張してメインローダーに

## 結論

現在のJSON読み込み機能は以下の問題を抱えています:

1. **過度な責任集中**: 単一クラスが設定読み込み・マージ・変換・永続化を全て担当
2. **重複実装**: 3つの類似クラスが同じ機能を重複実装
3. **複雑な変換ロジック**: ファイルパターン形式変換が複数箇所に散在
4. **層の責任違反**: ファクトリーがインフラストラクチャ層を直接操作

リファクタリングにより、責任を適切に分離し、重複を排除することで、保守性と可読性を大幅に向上できます。