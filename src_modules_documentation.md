# Project CPH - src モジュール機能ドキュメント

## 概要
このドキュメントは、Project CPHのsrcディレクトリ以下の各モジュールの機能を説明します。

## メインエントリーポイント

### `main.py`
- **機能**: アプリケーションのメインエントリーポイント
- **概要**: ワークフロー実行の制御と結果の表示を担当
- **主な責務**:
  - WorkflowExecutionServiceを使用してワークフローを実行
  - 準備タスクとステップ実行の結果管理
  - 詳細な実行ログの出力
  - エラーハンドリングと例外管理

## アーキテクチャ概要

### `application/` - アプリケーション層
#### `factories/`
- **`unified_request_factory.py`**: 統一リクエストファクトリー
  - 様々なリクエストタイプを生成する統一インターフェース

#### `formatters/`
- **`base/base_format_engine.py`**: フォーマッタの基底クラス
- **`format_manager.py`**: フォーマット処理の管理
- **`python_format_engine.py`**: Python固有のフォーマット処理
- **`test_result_formatter.py`**: テスト結果のフォーマット処理

#### `orchestration/`
- **`unified_driver.py`**: 統一ドライバー
  - リクエストタイプに基づいて適切なドライバーを選択・実行
  - FILE、SHELL、DOCKER、PYTHONの各操作タイプを統一的に処理
- **`execution_controller.py`**: 実行制御
- **`output_manager.py`**: 出力管理

### `context/` - コンテキスト管理
#### 中核ファイル
- **`execution_context.py`**: 実行コンテキストのファサードクラス
  - コマンドタイプ、言語、コンテスト名、問題名などの実行環境情報を管理
  - 設定値の解決、フォーマット処理、Dockerネーミング機能を提供
- **`execution_data.py`**: 実行データの管理
- **`context_validator.py`**: コンテキストバリデーション
- **`config_resolver_proxy.py`**: 設定解決プロキシ
- **`dockerfile_resolver.py`**: Dockerfileの解決
- **`user_input_parser.py`**: ユーザー入力の解析

#### サブモジュール
- **`commands/`**: コマンド関連（`base_command.py`）
- **`parsers/`**: パーサー（`validation_service.py`）
- **`resolver/`**: 設定解決（`config_node.py`, `config_node_logic.py`, `config_resolver.py`）
- **`utils/`**: ユーティリティ（`format_utils.py`, `validation_utils.py`）

### `domain/` - ドメイン層
#### `constants/`
- **`operation_type.py`**: 操作タイプの定義（FILE、SHELL、DOCKER、PYTHON等）

#### `requests/` - リクエストオブジェクト
- **`base/base_request.py`**: 全リクエストの基底クラス
  - 実行制御、デバッグ情報、操作タイプの抽象化を提供
- **`composite/`**: 複合リクエスト（複数操作をまとめたもの）
- **`docker/`**: Docker操作リクエスト
- **`file/`**: ファイル操作リクエスト
- **`python/`**: Python実行リクエスト
- **`shell/`**: シェルコマンド実行リクエスト

#### `results/`
- **`result.py`**: 基本結果クラス
- **`docker_result.py`**: Docker操作結果
- **`file_result.py`**: ファイル操作結果
- **`shell_result.py`**: シェル実行結果

#### `types/`
- **`execution_types.py`**: 実行関連の型定義

### `infrastructure/` - インフラストラクチャ層
#### 中核ファイル
- **`di_container.py`**: 依存性注入コンテナ
  - 各種ドライバーやサービスの依存関係を管理
  - 自動依存解決とテスト用オーバーライド機能を提供
- **`build_infrastructure.py`**: インフラストラクチャの構築

#### `drivers/` - 実行ドライバー
- **`base/base_driver.py`**: 全ドライバーの基底クラス
  - execute、validate、初期化、クリーンアップの抽象インターフェース
- **`docker/`**: Docker操作ドライバー
- **`file/`**: ファイル操作ドライバー
- **`python/`**: Python実行ドライバー
- **`shell/`**: シェル実行ドライバー

#### その他
- **`config/di_config.py`**: DI設定
- **`environment/`**: 環境管理
- **`mock/`**: モックドライバー
- **`persistence/`**: 永続化（SQLite、JSON、基底クラス）

### `env_core/` - 環境コア機能
#### `step/`
- **`core.py`**: ステップ生成のコア機能
- **`dependency.py`**: 依存関係解決
- **`step.py`**: ステップの定義
- **`workflow.py`**: ワークフロー管理

#### `workflow/`
- **`graph_based_workflow_builder.py`**: グラフベースワークフロービルダー
  - JSONステップからRequestExecutionGraphを生成
  - 依存関係を考慮した実行計画の構築
  - リソース競合の検出と解決
- **`request_execution_graph.py`**: リクエスト実行グラフ

### `env_integration/` - 環境統合
#### `fitting/`
- **`docker_state_manager.py`**: Docker状態管理
- **`environment_inspector.py`**: 環境検査
- **`preparation_error_handler.py`**: 準備エラーハンドリング
- **`preparation_executor.py`**: 準備実行

### `executor/` - 実行エンジン
各操作タイプ（base、composite、docker、file、python、shell、sqlite）ごとに以下の構造:
- **`constants/`**: 定数定義
- **`drivers/`**: ドライバー実装
- **`exceptions/`**: 例外クラス
- **`formatters/`**: フォーマッタ
- **`mock/`**: モッククラス
- **`orchestration/`**: オーケストレーション
- **`persistence/`**: 永続化
- **`requests/`**: リクエスト実装
- **`results/`**: 結果クラス
- **`types/`**: 型定義
- **`utils/`**: ユーティリティ

### `pure_functions/` - 純粋関数
- **`execution_context_formatter_pure.py`**: 実行コンテキストフォーマット
- **`graph_builder_pure.py`**: グラフ構築純粋関数
- **`output_manager_formatter_pure.py`**: 出力管理フォーマット

### `shared/` - 共有機能
#### `exceptions/`
- **`composite_step_failure.py`**: 複合ステップ失敗例外

#### `utils/`
- **`pure_functions.py`**: 汎用純粋関数
  - 文字列フォーマット、パス検証、Docker コマンド生成等の副作用のない関数群
- **`docker/`**: Docker関連ユーティリティ
- **`python/`**: Python関連ユーティリティ
- **`shell/`**: シェル関連ユーティリティ

### `utils/` - ユーティリティ
- **`debug_logger.py`**: デバッグログ機能
- **`path_operations.py`**: パス操作ユーティリティ

### その他
- **`workflow_execution_service.py`**: ワークフロー実行サービス
- **`performance/`**: パフォーマンス関連

## アーキテクチャの特徴

1. **レイヤード・アーキテクチャ**: domain、application、infrastructureの3層構造
2. **依存性注入**: DIContainerによる疎結合設計
3. **統一インターフェース**: UnifiedDriverによる操作タイプの抽象化
4. **関数型プログラミング**: pure_functionsによる副作用のない処理
5. **グラフベース実行**: 依存関係を考慮した並列・順次実行の最適化
6. **モック対応**: テスタビリティを考慮した設計

## 実行フロー

1. **main.py** がエントリーポイントとして起動
2. **user_input_parser** がユーザー入力を解析して **ExecutionContext** を生成
3. **WorkflowExecutionService** がワークフローを実行
4. **GraphBasedWorkflowBuilder** が依存関係を解決して実行計画を生成
5. **UnifiedDriver** が適切なドライバーを選択して各ステップを実行
6. **main.py** が結果を整形して出力