# Data層の処理概要

## 責務と役割

Data層は以下の責務を担当している：

1. **データ永続化処理**: SQLiteデータベースとのインターフェース
2. **Repository Pattern実装**: ドメインオブジェクトの永続化ロジック
3. **データ操作ユーティリティ**: リスト処理、辞書操作、データ変換
4. **実行時状態管理**: セッション状態やユーザー設定値の管理

## ファイル別詳細分析

### data_processors.py
**責務**: 純粋関数によるデータ処理ユーティリティ

**主要機能**:
- `filter_and_transform_items()`: リストのフィルタリングと変換
- `group_items_by_key()`: キーによるグループ化
- `merge_dictionaries()`: 辞書のマージ

**特徴**:
- 関数型プログラミング原則に従った副作用なし実装
- CLAUDE.mdルールに従いデフォルト値使用を禁止
- 明示的な設定取得を実装

### base/base_repository.py
**責務**: すべてのRepositoryクラスの基底クラス

**主要機能**:
- `DatabaseRepositoryFoundation`: データベースリポジトリの共通基盤
- 永続化マネージャーの管理
- 共通データベース接続処理
- エンティティ数カウント機能

**設計パターン**:
- Repository Pattern（基底クラス）
- Strategy Pattern（persistence_managerの注入）

### docker_container/docker_container_repository.py
**責務**: Dockerコンテナ情報の永続化

**主要機能**:
- コンテナレコードのCRUD操作
- コンテナ状態管理（running, created, started, removed）
- ライフサイクルイベント管理
- 条件検索（状態、言語、使用期間）
- JSONフィールドの自動パース

**設計パターン**:
- Repository Pattern
- Domain Model Pattern（コンテナ情報の構造化）

### docker_image/docker_image_repository.py
**責務**: Dockerイメージ情報の永続化

**主要機能**:
- イメージレコードのCRUD操作
- ビルド結果の更新
- 統計情報の取得
- イメージ使用状況の追跡
- 条件検索（ビルド状態、名前プレフィックス）

**設計パターン**:
- Repository Pattern
- Statistics Pattern（統計情報集約）

### operation/operation_repository.py
**責務**: 操作履歴の永続化

**主要機能**:
- 操作履歴のCRUD操作
- 統計情報の生成
- 条件検索（コマンド、コンテスト、言語）
- JSON詳細データの管理
- 成功率の計算

**設計パターン**:
- Repository Pattern
- Data Transfer Object（Operationデータクラス）
- Statistics Pattern

### session/session_repository.py
**責務**: 作業セッション情報の管理

**主要機能**:
- セッションのCRUD操作
- アクティブセッション管理
- セッション統計の取得
- 平均作業時間の計算

**設計パターン**:
- Repository Pattern
- Session Pattern（セッション管理）

### state/state_repository.py
**責務**: 状態管理の抽象化インターフェース

**主要機能**:
- 実行履歴の永続化
- セッションコンテキストの管理
- ユーザー指定値の管理
- セッション情報のクリア

**設計パターン**:
- Interface Segregation Principle
- Abstract Factory Pattern

### sqlite_state/sqlite_state_repository.py
**責務**: SQLiteベースの状態管理実装

**主要機能**:
- SystemConfigRepositoryを活用した状態管理
- JSON形式でのデータ保存
- カテゴリ別の状態分離
- 実行履歴の時系列管理

**設計パターン**:
- Repository Pattern
- Adapter Pattern（SystemConfigRepositoryの活用）

## 依存関係とデータフロー

### 外部依存関係
- `src.operations.interfaces.infrastructure_interfaces.RepositoryInterface`: 基底インターフェース
- `src.application.sqlite_manager.SQLiteManager`: データベース管理
- `src.configuration.system_config_repository.SystemConfigRepository`: 設定管理
- `src.application.execution_history.ExecutionHistory`: 実行履歴モデル
- `src.infrastructure.persistence.state.models.session_context.SessionContext`: セッションモデル

### データフロー
1. **Application層** → **Data層**: ビジネスロジックからのデータ永続化要求
2. **Data層** → **Infrastructure層**: SQLiteManager経由でのデータベース操作
3. **Configuration層** ← **Data層**: 状態管理での設定システム活用

### 内部依存関係
- 全リポジトリ → `base/base_repository.py`: 共通基盤の継承
- `sqlite_state_repository.py` → `state/state_repository.py`: インターフェース実装
- 各リポジトリ → `operations.interfaces.infrastructure_interfaces`: 標準インターフェース準拠

## 設計パターンと実装方針

### 採用パターン
1. **Repository Pattern**: 全リポジトリクラスで採用
2. **Interface Segregation**: 明確な責務分離
3. **Dependency Injection**: 永続化マネージャーの注入
4. **Data Transfer Object**: データクラスによる構造化
5. **Strategy Pattern**: 複数の永続化戦略対応

### CLAUDE.mdルール準拠
- デフォルト値の使用禁止
- 明示的な設定取得
- 副作用の制限（Infrastructure層のみ）
- 例外処理での適切なエラー情報提供

### 関数型プログラミング要素
- `data_processors.py`での純粋関数実装
- 副作用の最小化
- 不変性の重視

## 注意事項とメンテナンス要点

### 設計原則の遵守
1. **単一責任原則**: 各リポジトリは特定のドメインオブジェクトのみ管理
2. **開放閉鎖原則**: インターフェースによる拡張性確保
3. **リスコフ置換原則**: 基底クラスの契約遵守
4. **依存関係逆転原則**: 抽象化への依存

### メンテナンス指針
1. **データベーススキーマ変更**: 対応するリポジトリメソッドの更新が必要
2. **パフォーマンス最適化**: 大量データ処理時のクエリ最適化
3. **エラーハンドリング**: 永続化エラーの適切な処理と復旧
4. **テストカバレッジ**: 各リポジトリの完全なテスト実装

### 潜在的な課題
1. **トランザクション管理**: 複数テーブルにまたがる操作の整合性
2. **スケーラビリティ**: 大量データ処理時のパフォーマンス
3. **データ移行**: スキーマ変更時の既存データ移行
4. **同期処理**: 並行アクセスでの競合状態対策

### 拡張性の考慮
- 新しいドメインオブジェクト追加時の基底クラス活用
- 異なる永続化技術への移行可能性
- 分散システムへの発展可能性
- キャッシュ層の追加可能性