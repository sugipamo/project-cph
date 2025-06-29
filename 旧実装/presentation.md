# Presentation層の処理概要

## 責務と役割

Presentation層は、ユーザーとの接点となるインターフェースを提供し、以下の責務を担当する：

- **CLIアプリケーション**: コマンドライン引数の解析とアプリケーション実行制御
- **ユーザー入力の解析と検証**: コマンドライン引数を適切な実行コンテキストに変換
- **フォーマット処理**: テンプレート文字列の展開と文字列整形
- **Docker関連コマンド構築**: Dockerコマンドの構築と管理
- **実行コンテキストの検証**: ユーザー入力データの妥当性確認

## ファイル別詳細分析

### cli_app.py
**主要クラス**: `MinimalCLIApp`

**主要機能**:
- DI（依存性注入）コンテナを使用したCLIアプリケーション実行
- ワークフロー実行サービスとの連携
- エラーハンドリングと分類
- デバッグモードの処理

**重要なメソッド**:
- `run_cli_application()`: メインのCLI実行ロジック
- `_execute_workflow()`: ワークフロー実行サービスの呼び出し
- `_handle_composite_step_failure()`: CompositeStepFailureErrorの処理
- `_handle_general_exception()`: 一般的な例外の処理

### context_formatter.py
**主要機能**:
- TypedExecutionConfigurationのフォーマット処理
- 実行データからフォーマット用辞書の作成
- テンプレート文字列の展開処理
- Docker命名情報の生成

**重要なクラス・関数**:
- `ExecutionFormatData`: フォーマット用データクラス
- `format_template_string()`: テンプレート文字列のフォーマット
- `validate_execution_data()`: データバリデーション
- `get_docker_naming_from_data()`: Docker命名情報生成

### context_validator.py
**主要クラス**: `ContextValidator`

**主要機能**:
- 実行コンテキストの基本バリデーション
- 必須フィールドの検証
- 言語固有設定の存在確認

**重要なメソッド**:
- `validate_execution_context()`: 基本的なコンテキスト検証
- `validate_required_fields()`: 必須フィールド検証

### docker_command_builder.py
**主要機能**:
- Docker関連コマンドの構築（純粋関数として実装）
- 設定管理の依存性注入対応
- Docker run/stop/remove/buildコマンドの構築

**重要な関数**:
- `build_docker_run_command()`: docker runコマンド構築
- `build_docker_build_command()`: docker buildコマンド構築
- `validate_docker_image_name()`: イメージ名の検証
- 各種docker関連コマンドビルダー（stop, remove, ps, inspect等）

### formatters.py
**主要機能**:
- 文字列フォーマット処理の基礎ユーティリティ
- テンプレートキーの抽出
- 部分的なデータでのフォーマット処理

**重要な関数**:
- `format_with_missing_keys()`: 欠損キーを返すフォーマット処理
- `format_string_simple()`: シンプルな文字列フォーマット
- `extract_format_keys()`: フォーマットキーの抽出
- `validate_template_keys()`: テンプレートキーの検証

### main.py
**主要機能**:
- アプリケーションのエントリーポイント
- 段階的依存性注入の実行
- Infrastructure層からPresentation層への依存関係構築

**処理フロー**:
1. Infrastructure層の基本サービス初期化
2. 設定ファイル読み込み
3. Configuration層の初期化
4. DIコンテナへの登録
5. Docker command builderへの設定注入
6. アプリケーション実行

### string_formatters.py
**主要機能**:
- 純粋関数による文字列処理ユーティリティ
- パス検証とセキュリティチェック
- ファイルシステムパスの正規化

**重要な関数**:
- `format_template_string()`: テンプレート文字列のフォーマット
- `validate_file_path_format()`: ファイルパスのセキュリティ検証
- `normalize_filesystem_path()`: パス正規化
- `is_potential_script_path()`: スクリプトパス判定

### user_input_parser.py
**主要機能**:
- コマンドライン引数の解析と実行コンテキスト生成
- 新設定システムとの統合
- 柔軟な引数順序対応

**重要な関数**:
- `parse_user_input()`: メインの入力解析処理
- `_parse_command_line_args()`: コマンドライン引数解析
- `_scan_and_apply_*()`: 各種パラメータのスキャンと適用
- `_create_execution_config()`: 実行設定の作成

### user_input_parser_integration.py
**主要クラス**: `UserInputParserIntegration`

**主要機能**:
- 新設定システムとの統合処理
- 旧システムとの互換性保持
- ExecutionConfigurationの生成

## 依存関係とデータフロー

### 外部依存関係
- **Domain層**: `WorkflowExecutionService`, `CompositeStepFailureError`, `WorkflowExecutionResult`
- **Infrastructure層**: DIコンテナ、各種プロバイダー（OS、JSON、FileDriver等）
- **Application層**: `ConfigLoaderService`, `ValidationService`, `PureConfigManager`
- **Configuration層**: `ConfigResolver`, 設定ノード関連
- **Context層**: `DockerfileResolver`
- **Operations層**: エラー分類、リクエストファクトリー

### データフロー
1. **入力**: コマンドライン引数 → `user_input_parser.py`
2. **解析**: 引数解析 → 実行コンテキスト生成
3. **検証**: `context_validator.py` → データ妥当性確認
4. **フォーマット**: `context_formatter.py` → テンプレート展開
5. **実行**: `cli_app.py` → ワークフロー実行
6. **出力**: 結果表示とログ出力

## 設計パターンと実装方針

### 設計パターン
- **依存性注入パターン**: DIコンテナによる依存関係管理
- **純粋関数パターン**: 副作用のない関数設計（formatters, string_formatters）
- **アダプターパターン**: 新旧設定システム間の互換性保持
- **ビルダーパターン**: Dockerコマンド構築

### 実装方針
- **フォールバック処理禁止**: エラーの見逃しを防ぐため、明示的な例外処理
- **デフォルト値禁止**: すべての設定値は明示的に提供
- **副作用の局所化**: Infrastructure層以外での副作用を禁止
- **互換性維持**: 既存コードとの後方互換性を保持

### セキュリティ対策
- **パストラバーサル防止**: `validate_file_path_format()`での検証
- **コマンドインジェクション防止**: Docker コマンド構築時の適切なエスケープ処理
- **入力検証**: ユーザー入力の徹底的な検証

## 注意事項とメンテナンス要点

### 注意事項
1. **DIコンテナの適切な初期化**: main.pyからの段階的な依存性注入が必須
2. **設定システムの一貫性**: 新設定システムとの整合性を保つ
3. **エラーハンドリング**: CompositeStepFailureErrorと一般例外の適切な処理
4. **デバッグモード**: --debugフラグでの詳細なログ出力

### メンテナンス要点
1. **純粋関数の維持**: formattersとstring_formattersの副作用なし原則を保持
2. **Docker関連機能の更新**: Dockerコマンド構築ロジックの機能拡張
3. **設定システム統合**: 新設定システムへの完全移行準備
4. **テストカバレッジ**: 各コンポーネントの単体テストと統合テスト
5. **パフォーマンス**: LRUキャッシュ等の最適化機能の活用

### 今後の改善点
1. **設定システム統合の完了**: 旧システムからの完全移行
2. **Docker機能の拡張**: より柔軟なDockerコマンド構築
3. **エラーメッセージの国際化**: 多言語対応
4. **入力解析の柔軟性向上**: より自然なコマンドライン引数の受け入れ