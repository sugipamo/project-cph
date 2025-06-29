# Configuration層の処理概要

## 責務と役割

Configuration層は、アプリケーション全体の設定管理を担当する重要な層です。主な責務は以下の通りです：

1. **統一設定管理**: 型安全な設定値の取得・管理
2. **多層設定マージ**: システム設定・環境設定・実行時設定の優先順位付きマージ
3. **依存性注入設定**: DIContainerを用いた依存関係の設定と管理
4. **実行環境管理**: ローカル・Docker環境の統一的な実行環境抽象化
5. **設定データ永続化**: SQLiteを用いた設定値の保存・読み込み
6. **テンプレート展開**: 設定値内の変数展開機能

## ファイル別詳細分析

### build_infrastructure.py
**責務**: DIContainer の構築とインフラストラクチャのセットアップ
- `build_infrastructure()`: 本番用DIContainer構築
- `build_mock_infrastructure()`: テスト用DIContainer構築  
- 遅延ローディングによる結合度低減と起動時間改善
- 後方互換性のためのエイリアス提供

**主要機能**:
- プロダクション環境とテスト環境の依存関係設定
- DIContainerへの依存性注入設定の委譲

### config_resolver.py
**責務**: ConfigNodeベースの設定値解決エンジン
- `create_config_root_from_dict()`: 辞書からConfigNode階層構築
- `resolve_by_match_desc()`: パス階層での設定値解決（マッチ順序付き）
- `resolve_best()`: 最適な設定ノードの選択
- `resolve_formatted_string()`: テンプレート変数の展開
- エイリアス機能による設定キーの複数名サポート

**主要アルゴリズム**:
- BFS（幅優先探索）による設定値探索
- マッチランクによる優先順位付け設定解決
- 循環参照回避の訪問済みノード管理

### configuration_repository.py
**責務**: 設定データの永続化レイヤー
- SQLiteデータベースからの設定読み込み・保存
- 前回実行値（contest_name, problem_name）の管理
- データベース操作の抽象化とエラーハンドリング
- JSON形式での設定値シリアライゼーション

**主要メソッド**:
- `load_previous_values()`: 前回実行時の設定値復元
- `save_current_values()`: 現在の設定値永続化
- `get_available_config_keys()`: 利用可能設定キーの取得

### di_config.py
**責務**: 依存性注入の設定と管理（最も複雑なファイル）
- プロダクション・テスト環境の依存関係定義
- 遅延ファクトリーパターンによる循環依存回避
- 多数のサービス・リポジトリ・ドライバーの登録管理

**主要ファクトリー**:
- `_create_docker_driver()`: Docker実行ドライバー
- `_create_shell_python_driver()`: Shell/Python実行ドライバー
- `_create_unified_logger()`: 統一ログシステム
- `_create_request_factory()`: リクエスト生成ファクトリー
- `_create_system_config_loader()`: システム設定ローダー

**環境別設定**:
- `configure_production_dependencies()`: 本番環境依存関係
- `configure_test_dependencies()`: テスト環境依存関係（モック使用）

### environment_manager.py
**責務**: 実行環境の抽象化と管理
- ローカル・Docker環境の統一インターフェース提供
- 環境準備・クリーンアップの管理
- 実行コンテキストに基づく環境切り替え
- 環境固有の設定値提供（作業ディレクトリ、タイムアウト等）

**主要メソッド**:
- `prepare_environment()`: 環境準備処理
- `cleanup_environment()`: 環境後処理
- `execute_request()`: 環境に応じたリクエスト実行
- `should_force_local()`: ローカル実行強制判定

### execution_config.py
**責務**: 実行時パス情報の集約
- `ExecutionPaths` データクラス: パス情報の不変オブジェクト
- ワークスペース・コンテスト・テンプレート等のパス管理
- 型安全なパス情報アクセス

### output_config.py
**責務**: 出力設定の管理
- `OutputConfig` データクラス: 出力形式設定の不変オブジェクト
- ワークフロー要約・ステップ詳細・実行完了通知の表示制御
- フォーマットプリセットの管理

### runtime_config_overlay.py
**責務**: 実行時設定オーバーレイシステム
- 元設定ファイルを変更せずに実行時設定変更
- `RuntimeConfigOverlay`: 階層設定のオーバーライド機能
- `DebugConfigProvider`: デバッグモード専用設定プロバイダー
- 設定の不変性保持と動的変更の両立

**主要機能**:
- ドット記法による階層設定アクセス
- オーバーレイのアクティブ状態管理
- デバッグモードの切り替え機能

### system_config_loader.py
**責務**: SQLiteベースのシステム設定管理
- SQLiteからの設定値読み込み・保存
- 実行コンテキスト（command, language, env_type等）の管理
- 言語設定の構造化管理
- ユーザー指定設定と自動設定の区別

**主要メソッド**:
- `load_config()`: SQLiteからの完全設定読み込み
- `get_env_config()`: 環境設定（env.json相当）取得
- `update_current_context()`: 実行コンテキスト更新
- `get_user_specified_context()`: ユーザー指定設定のみ取得

### system_config_repository.py
**責務**: システム設定のSQLiteリポジトリ実装
- `DatabaseRepositoryFoundation` を継承したリポジトリパターン実装
- JSON形式での設定値シリアライゼーション・デシリアライゼーション
- カテゴリー・説明文を含む設定メタデータ管理
- CRUD操作の完全実装

**主要機能**:
- `set_config()`: 設定値の挿入・更新
- `get_config()`: 設定値取得
- `get_configs_by_category()`: カテゴリー別設定取得
- `search_configs()`: 設定検索機能
- `get_execution_context_summary()`: 実行コンテキスト要約

## 依存関係とデータフロー

### 内部依存関係
```
build_infrastructure.py
 └─ di_config.py
     ├─ configuration_repository.py
     ├─ environment_manager.py
     ├─ system_config_loader.py
     └─ system_config_repository.py

config_resolver.py
 ├─ src.domain.config_node (ConfigNode)
 ├─ src.domain.services.config_node_service
 └─ src.presentation.formatters

environment_manager.py
 └─ src.operations.interfaces.utility_interfaces (LoggerInterface)
```

### 外部依存関係
- **Infrastructure層**: DIContainer, 各種Provider (JSON, SQLite, OS等)
- **Domain層**: ConfigNode, config_node_service
- **Application層**: 各種Manager クラス
- **Data層**: Repository パターン実装
- **Operations層**: Logger, Request/Result 系

### データフロー
1. **設定読み込み**: JSON/SQLite → config_resolver → 統一設定オブジェクト
2. **依存性注入**: di_config → DIContainer → 各サービス
3. **実行時解決**: environment_manager + config_resolver → 実行固有設定
4. **設定永続化**: configuration_repository → SQLite保存

## 設計パターンと実装方針

### 1. Repository パターン
- `ConfigurationRepository`, `SystemConfigRepository` でデータアクセス層抽象化
- SQLite操作の統一的なインターフェース提供

### 2. Factory パターン
- `di_config.py` で多数の遅延ファクトリー実装
- 循環依存回避と初期化順序の制御

### 3. Strategy パターン（簡略化）
- `EnvironmentManager` で環境別実行戦略の統一インターフェース
- ローカル・Docker環境の透過的切り替え

### 4. Overlay パターン
- `RuntimeConfigOverlay` で元設定を変更せずに実行時オーバーライド
- 設定の不変性と動的変更の両立

### 5. 依存性注入パターン
- DIContainer による疎結合設計
- インターフェース経由でのサービス利用

## 注意事項とメンテナンス要点

### 1. CLAUDE.md遵守事項
- **デフォルト値禁止**: 設定取得時は必ず型指定とエラーハンドリング必須
- **`.get()` 使用禁止**: 辞書アクセスでは例外ベースのエラーハンドリング
- **設定ファイル編集制限**: ユーザーから明示された場合のみ許可
- **フォールバック処理禁止**: 必要なエラーを見逃さないための方針

### 2. パフォーマンス特徴
- **多層キャッシュシステム**: 型変換・テンプレート展開・ExecutionConfig生成をキャッシュ
- **遅延ローディング**: 必要時のみ設定読み込み（約0.1-5μsでの高速設定解決）
- **LRUキャッシュ**: ExecutionConfigキャッシュは1000個まで

### 3. 型安全性
- 全ての設定取得で戻り値の型指定必須
- `TypeSafeConfigNodeManager` による型安全な設定管理
- テンプレート変数の型チェック機能

### 4. 互換性維持
- レガシーAPI向けのエイリアス提供
- 段階的移行支援のための互換性レイヤー
- 既存の24ファイルから9ファイルへの大幅簡素化実現

### 5. テスト容易性
- モック実装の完全分離（テスト用ファクトリー）
- DIContainerによる依存関係の差し替え容易性
- インメモリSQLiteによる高速テスト実行

### 6. エラーハンドリング
- KeyError, TypeError の適切な伝播
- SQLite操作でのトランザクション管理
- 設定ファイル不正時の明確なエラーメッセージ

この Configuration層は、アプリケーション全体の設定管理基盤として、型安全性・パフォーマンス・保守性を高次元で両立させた設計となっています。