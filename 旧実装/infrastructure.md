# Infrastructure層の処理概要

## 責務と役割

Infrastructure層は、外部システムとの統合と技術的な関心事を担当するレイヤーです。主な責務は以下の通りです：

- **副作用の集約**: 外部システムやリソースへの副作用的操作を一箇所に集約
- **外部依存の抽象化**: データベース、ファイルシステム、Docker等の外部依存関係を抽象化
- **依存性注入**: DIコンテナを通じて依存関係を管理
- **ドライバー提供**: 統一されたインターフェースでさまざまな操作を実行
- **設定管理**: インフラストラクチャ設定の管理と提供

## ファイル別詳細分析

### 1. DIコンテナと依存性注入

#### di_container.py
- **DIContainer**: 依存性注入コンテナの実装
- **DIKey**: 依存関係の識別子定義（Enum）
- 機能：
  - プロバイダー登録・解決
  - オーバーライド機能（テスト用）
  - 自動依存関係解決

### 2. プロバイダー層（副作用集約）

#### file_provider.py
- **SystemFileProvider**: 実際のファイルシステム操作
- **MockFileProvider**: テスト用モック実装
- 機能：ファイル読み書き、ディレクトリ作成、存在チェック

#### json_provider.py
- **SystemJsonProvider**: JSON操作の実装
- **MockJsonProvider**: テスト用モック実装
- 機能：JSON シリアライゼーション・デシリアライゼーション

#### os_provider.py
- **SystemOsProvider**: OS操作の実装
- **MockOsProvider**: テスト用モック実装
- 機能：パス操作、ディレクトリ操作、現在ディレクトリ取得

#### sqlite_provider.py
- **SystemSQLiteProvider**: SQLite操作の実装
- **MockSQLiteProvider**: テスト用モック実装
- 機能：データベース接続、SQL実行、トランザクション管理

#### time_provider.py
- **SystemTimeProvider**: 時刻操作の実装
- **MockTimeProvider**: テスト用モック実装
- 機能：現在時刻取得、待機処理

#### registry_provider.py
- **SystemRegistryProvider**: レジストリ管理の実装
- **MockRegistryProvider**: テスト用モック実装
- 機能：グローバル状態管理、レジストリ操作

### 3. ドライバー層

#### drivers/generic/base_driver.py
- **ExecutionDriverInterface**: 全ドライバーの抽象基底クラス
- **BaseDriverImplementation**: 共通機能を持つベース実装
- **DriverUtils**: ドライバー用ユーティリティ関数
- 機能：
  - 設定ファイル読み込み（infrastructure_defaults.json）
  - ログ機能統合
  - パスバリデーション

#### drivers/generic/execution_driver.py
- **ExecutionDriver**: シェル・Python実行の統一ドライバー
- 機能：
  - シェルコマンド実行
  - Pythonコード・スクリプト実行
  - 権限変更（chmod）
  - コマンド可用性チェック

#### drivers/generic/persistence_driver.py
- **PersistenceDriver**: 永続化操作の抽象基底クラス
- **SQLitePersistenceDriver**: SQLite永続化の実装
- 機能：
  - データベース接続管理
  - クエリ実行
  - リポジトリ管理

#### drivers/generic/unified_driver.py
- **UnifiedDriver**: 全ドライバーを統合する統一ドライバー
- 機能：
  - リクエストタイプに基づくルーティング
  - Docker、ファイル、シェル、Python操作の統一インターフェース
  - 結果オブジェクトの変換

#### drivers/file/file_driver.py
- **FileDriver**: ファイルシステム操作の統一ドライバー
- 機能：
  - ファイル・ディレクトリ操作（作成、削除、移動、コピー）
  - パス解決・存在チェック
  - Globパターンマッチング
  - ファイルハッシュ計算
  - Docker cp操作

#### drivers/docker/docker_driver.py
- **DockerDriver**: Docker操作の統一ドライバー
- 機能：
  - コンテナ操作（実行、停止、削除）
  - イメージビルド
  - ログ取得、コンテナ一覧
  - トラッキング機能（オプション）
  - コマンドビルド機能

### 4. その他のコンポーネント

#### ast_analyzer.py
- **ASTAnalyzer**: Pythonコード解析機能
- **ImportInfo**: インポート情報のデータクラス
- 機能：
  - ソースコード解析
  - インポート・エクスポート情報抽出
  - 壊れたインポート検出

#### module_info.py
- **ModuleInfo**: モジュール情報のデータクラス
- **ExportedSymbol**: エクスポートシンボル情報
- 機能：モジュールメタデータ管理

#### docker_naming_provider.py
- **DockerNamingProvider**: Docker命名規則プロバイダー
- 機能：イメージ・コンテナ名の標準化生成

#### local_filesystem.py
- **LocalFileSystem**: ローカルファイルシステムの実装
- 機能：FileSystemInterfaceの実装

#### persistence_exceptions.py
- 永続化操作専用の例外クラス群
- **PersistenceError**: 基底例外
- **ConnectionError, MigrationError, QueryError等**: 特定操作用例外

### 5. 永続化コンポーネント

#### persistence/state/models/session_context.py
- **SessionContext**: セッション状態のデータモデル
- 機能：現在のコンテスト・問題・言語情報管理

#### persistence/sqlite/migrations/
- データベース移行スクリプト群
- 001_initial.sql: 初期テーブル作成
- 002_docker_tracking.sql: Dockerトラッキング機能
- 003_nullable_config_values.sql: NULL対応設定値
- 004, 006: コンテスト関連ファイル管理

#### requests/file/file_op_type.py
- **FileOpType**: ファイル操作タイプの列挙

## 依存関係とデータフロー

### 主要な依存関係
1. **外向き依存**: 外部システム（ファイルシステム、データベース、Docker、OS）
2. **内向き依存**: Domain層・Application層のインターフェース
3. **DIコンテナ**: 全コンポーネントの依存関係を管理

### データフロー
```
Application層 → DIContainer → Infrastructure Driver → Provider → 外部システム
                    ↓
            設定ファイル読み込み
                    ↓
         infrastructure_defaults.json
```

### 主要なパターン
1. **Provider Pattern**: 副作用をProviderクラスに集約
2. **Driver Pattern**: 統一インターフェースで複数操作を提供
3. **Dependency Injection**: DIコンテナによる依存関係管理
4. **Mock Pattern**: テスト用Mock実装を全Providerで提供

## 設計パターンと実装方針

### 1. 副作用の分離
- 全ての副作用的操作をInfrastructure層に集約
- SystemXxxProvider: 実際の副作用を持つ実装
- MockXxxProvider: 副作用なしのテスト実装

### 2. 抽象化とテスタビリティ
- 抽象インターフェースによる実装の隠蔽
- モック実装による単体テストサポート
- 依存性注入による疎結合設計

### 3. 統一ドライバーパターン
- UnifiedDriver: 全操作の統一エントリーポイント
- 専門ドライバー: 特定技術領域の詳細実装
- BaseDriver: 共通機能の提供

### 4. 設定駆動設計
- infrastructure_defaults.json: インフラ設定の外部化
- デフォルト値の一元管理
- 実行時設定注入

### 5. エラーハンドリング
- 専用例外クラス（persistence_exceptions.py）
- 操作固有のエラー情報
- フォールバック処理の明示的禁止

## 注意事項とメンテナンス要点

### 1. 副作用の管理
- **重要**: 副作用は必ずInfrastructure層のProviderクラスに集約する
- main.pyからの依存性注入で副作用を制御
- テスト時はMockProviderを使用して副作用を排除

### 2. 設定値管理
- **禁止事項**: デフォルト値の直接使用
- 設定は infrastructure_defaults.json または専用設定ファイルから取得
- 存在しない設定は適切な例外を発生させる

### 3. 互換性維持
- 既存インターフェースの変更時は互換性コメントを追記
- hasattr()によるgetattr()デフォルト値の代替使用
- レガシーコードとの互換性を考慮した実装

### 4. テスト戦略
- 全Providerにモック実装を提供
- DIコンテナのオーバーライド機能を活用
- 副作用なしでの単体テスト実施

### 5. エラーハンドリング
- フォールバック処理は明示的に禁止
- 具体的で有用なエラーメッセージの提供
- 操作固有の例外クラス使用

### 6. 拡張性
- 新しい外部システム統合時はProvider+Driverパターンを踏襲
- DIKeyへの新しい依存関係追加
- 既存パターンとの一貫性維持

### 7. パフォーマンス
- 設定値のキャッシュ機能活用
- 遅延初期化（Lazy Loading）の実装
- リソースの適切なクリーンアップ