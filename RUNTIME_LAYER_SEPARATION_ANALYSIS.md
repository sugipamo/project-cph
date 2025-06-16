# runtimeレイヤーと設定システム分離の詳細影響分析

## 1. 現在のruntimeレイヤー依存関係の特定

### 1.1 コアクラスの依存関係

#### RuntimeConfig (src/configuration/core/runtime_config.py)
- **データクラス**: 実行時設定のみを保持
- **フィールド**: language_id, source_file_name, run_command, timeout_seconds, retry_settings
- **特徴**: immutable (frozen=True)
- **依存**: 単純データクラス、外部依存なし

#### ExecutionConfiguration (src/configuration/core/execution_configuration.py)
- **統合クラス**: すべてのコンテキスト情報を統合
- **依存**: RuntimeConfig, ExecutionPaths, OutputConfig
- **機能**: テンプレート変数辞書生成、ファイルパターン取得
- **設計**: 不変オブジェクト

#### ExecutionContextAdapter (src/configuration/adapters/execution_context_adapter.py)
- **アダプターパターン**: 既存ExecutionContextとの互換性保持
- **依存**: ExecutionConfiguration, TemplateExpander
- **役割**: 新旧システムの橋渡し
- **可変状態**: resolver, env_json, dockerfile_resolver

### 1.2 依存ファイルの分類

#### 高依存度ファイル (直接的な依存)
1. **src/configuration/factories/configuration_factory.py**
   - ExecutionConfiguration生成の中核
   - RuntimeConfig作成処理
   - 既存コンテキストからの変換処理

2. **src/workflow/step/step_generation_service.py**
   - ExecutionContextAdapterを使用
   - ステップ生成でのコンテキスト変換
   - 後方互換性の維持

3. **src/workflow/workflow_execution_service.py**
   - ExecutionContextAdapterを必須とする
   - ワークフロー実行時の設定取得
   - 並列実行設定の管理

4. **src/configuration/user_input_parser/user_input_parser_integration.py**
   - 新設定システムの統合点
   - ExecutionContextAdapterの生成
   - 互換性検証

#### 中依存度ファイル (間接的な依存)
1. **src/context/user_input_parser.py**
   - 新設定システムとの統合
   - create_new_execution_context関数使用
   - SQLite設定保存処理

2. **src/application/orchestration/workflow_result_presenter.py**
   - ExecutionContextの属性アクセス
   - 出力設定の取得

3. **テストファイル群**
   - 統合テスト
   - 設定システムテスト
   - 互換性テスト

## 2. ExecutionConfiguration, RuntimeConfig, ExecutionContextの使用箇所

### 2.1 ExecutionConfiguration使用箇所
- **configuration_factory.py**: 生成・構築処理
- **execution_context_adapter.py**: 内部データ保持
- **template_expander.py**: テンプレート展開
- **config_resolver.py**: 設定解決
- **テストファイル群**: 機能検証

### 2.2 RuntimeConfig使用箇所
- **runtime_config.py**: 定義場所
- **execution_configuration.py**: 組み込み
- **configuration_factory.py**: 生成処理
- **execution_context_adapter.py**: 属性アクセス

### 2.3 ExecutionContext使用箇所（アダプター経由）
- **workflow_execution_service.py**: ワークフロー実行
- **step_generation_service.py**: ステップ生成
- **workflow_result_presenter.py**: 結果表示
- **simple_step_runner.py**: ステップ実行

## 3. user_input_parser.pyでのruntime処理分析

### 3.1 新設定システム統合
```python
# 新設定システムの統合
from src.configuration.integration.user_input_parser_integration import (
    create_new_execution_context,
)
```

### 3.2 設定保存・復元処理
- **_load_current_context_sqlite**: SQLiteからの設定読み込み
- **_save_current_context_sqlite**: SQLiteへの設定保存
- **SystemConfigLoader**: 設定管理の中核

### 3.3 コンテキスト生成処理
- **create_new_execution_context**: 新システムでのコンテキスト生成
- **ExecutionContextAdapter**: 既存システムとの互換性保持
- **引数解析**: 柔軟な順序対応での設定更新

## 4. SQLiteベースの設定保存・復元処理分析

### 4.1 SystemConfigLoader (src/infrastructure/persistence/sqlite/system_config_loader.py)
- **設定読み込み**: load_config(), get_current_context()
- **設定保存**: save_config(), update_current_context()
- **バックアップ**: old_contest_name, old_problem_name管理

### 4.2 SystemConfigRepository (src/infrastructure/persistence/sqlite/repositories/system_config_repository.py)
- **CRUD操作**: create, read, update, delete
- **カテゴリ管理**: get_configs_by_category()
- **JSON処理**: 設定値のシリアライズ/デシリアライズ
- **NULL処理**: ユーザー指定判定

### 4.3 ContestManager (src/infrastructure/persistence/sqlite/contest_manager.py)
- **コンテスト状態管理**: get_current_contest_state()
- **設定フォールバック**: NULL値の履歴からの復元
- **SystemConfigLoader統合**: 設定管理との連携

## 5. 分離による既存コードへの影響詳細評価

### 5.1 直接影響（破壊的変更）

#### 高リスク領域
1. **ExecutionContextAdapter**
   - 現在の設計では分離困難
   - RuntimeConfigへの直接依存
   - 新旧システムの橋渡し役

2. **ConfigurationFactory**
   - RuntimeConfig生成処理
   - ExecutionConfiguration構築
   - 既存コンテキスト変換

#### 中リスク領域
1. **WorkflowExecutionService**
   - ExecutionContextAdapterへの依存
   - 実行時設定の取得
   - 並列実行設定

2. **StepGenerationService**
   - コンテキスト変換処理
   - テンプレート展開
   - ファイルパターン処理

### 5.2 間接影響（波及効果）

#### 設定システム
- **ConfigurationLoader**: 設定読み込み方式の変更
- **TemplateExpander**: テンプレート変数の取得方式
- **PropertyProvider**: プロパティ解決方式

#### 永続化システム
- **SystemConfigLoader**: 設定構造の変更
- **SystemConfigRepository**: データスキーマの変更
- **ContestManager**: 設定取得方式の変更

## 6. 分離設計のための具体的移行戦略

### 6.1 段階的分離アプローチ

#### Phase 1: 設定管理層の分離
1. **新しい設定管理インターフェース作成**
   - `ISettingsManager`インターフェース定義
   - `IExecutionSettings`インターフェース定義
   - `IRuntimeSettings`インターフェース定義

2. **設定管理の実装分離**
   - `SettingsManager`クラス作成
   - SQLite実装の抽象化
   - 設定スキーマの正規化

#### Phase 2: Runtime設定の独立化
1. **Runtime設定専用層の作成**
   - `RuntimeSettingsProvider`クラス
   - `RuntimeConfigurationService`クラス
   - 言語レジストリとの統合

2. **ExecutionConfiguration依存の除去**
   - RuntimeConfig生成の独立化
   - 設定取得インターフェースの統一
   - テンプレート変数の分離

#### Phase 3: アダプター層の再設計
1. **新しいアダプター設計**
   - 設定管理への依存除去
   - インターフェースベースの設計
   - 責務の明確化

2. **既存システムとの互換性維持**
   - 移行期間中の互換性レイヤー
   - 段階的な置き換え
   - テスト体制の強化

### 6.2 具体的実装手順

#### Step 1: インターフェース定義
```python
# src/configuration/interfaces/settings_manager.py
class ISettingsManager:
    def get_execution_settings(self) -> IExecutionSettings
    def get_runtime_settings(self, language: str) -> IRuntimeSettings
    def save_execution_context(self, context: dict) -> None

# src/configuration/interfaces/execution_settings.py
class IExecutionSettings:
    def get_contest_name(self) -> str
    def get_problem_name(self) -> str
    def get_language(self) -> str
    def get_env_type(self) -> str
```

#### Step 2: 設定管理実装
```python
# src/configuration/services/settings_manager.py
class SettingsManager(ISettingsManager):
    def __init__(self, config_repo: SystemConfigRepository):
        self.config_repo = config_repo
    
    def get_execution_settings(self) -> ExecutionSettings:
        return ExecutionSettings(self.config_repo)
```

#### Step 3: Runtime設定の独立化
```python
# src/configuration/services/runtime_settings_provider.py
class RuntimeSettingsProvider:
    def __init__(self, language_registry: LanguageRegistry):
        self.language_registry = language_registry
    
    def get_runtime_config(self, language: str) -> RuntimeConfig:
        return RuntimeConfig(
            language_id=language,
            source_file_name=self.language_registry.get_source_file_name(language),
            run_command=self.language_registry.get_run_command(language),
            timeout_seconds=30,
            retry_settings={}
        )
```

#### Step 4: 依存関係の再構築
```python
# src/configuration/adapters/execution_context_adapter_v2.py
class ExecutionContextAdapterV2:
    def __init__(self, settings_manager: ISettingsManager, 
                 runtime_provider: RuntimeSettingsProvider):
        self.settings_manager = settings_manager
        self.runtime_provider = runtime_provider
    
    def get_runtime_config(self) -> RuntimeConfig:
        execution_settings = self.settings_manager.get_execution_settings()
        return self.runtime_provider.get_runtime_config(
            execution_settings.get_language()
        )
```

### 6.3 移行リスク軽減策

#### 1. テスト体制強化
- 既存機能の回帰テスト整備
- 統合テストの充実
- 段階的リリース体制

#### 2. 互換性保証
- 既存APIの維持
- 非推奨化期間の設定
- 移行ガイドの整備

#### 3. モニタリング
- 設定システムの動作監視
- パフォーマンス測定
- エラー監視・アラート

### 6.4 期待される効果

#### 1. アーキテクチャの改善
- 責務の明確化
- 依存関係の単純化
- テスタビリティの向上

#### 2. 保守性の向上
- 設定変更の影響範囲縮小
- 新機能追加の容易化
- バグ修正の効率化

#### 3. 拡張性の向上
- 新しい設定タイプの追加
- 異なる永続化方式の対応
- 設定管理機能の拡張

## 7. 結論

runtimeレイヤーと設定システムの分離は、システムの保守性と拡張性を大幅に向上させる重要な取り組みですが、既存システムへの影響が大きいため、段階的なアプローチが必要です。

特に以下の点に注意が必要です：

1. **ExecutionContextAdapter**の再設計が最も重要
2. **SQLite設定管理**の抽象化が必須
3. **段階的移行**により既存機能の安定性を保持
4. **十分なテスト体制**でリスクを軽減

提案した移行戦略により、システムの品質を保ちながら効果的な分離を実現できると評価します。