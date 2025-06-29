# Domain層の処理概要

## 責務と役割

Domain層は競技プログラミング支援システムの中核となるビジネスロジックとドメインルールを管理する層です。クリーンアーキテクチャに基づき、外部の技術的詳細から独立したピュアなドメインモデルとビジネスルールを提供します。

### 主要責務
- **ワークフロー管理**: ステップベースのワークフロー生成・実行パイプライン
- **リクエスト抽象化**: 操作要求の型安全な表現とインターフェース定義
- **ステップ処理**: 実行単位となるステップの定義・依存関係解決・最適化
- **設定管理**: 階層的設定データの構造化とアクセス
- **エラーハンドリング**: ドメイン固有例外の定義と分類
- **サービス層**: ドメイン操作の調整とオーケストレーション

## ファイル別詳細分析

### 基盤インターフェース・型定義

#### `base_request.py`
- **RequestType列挙型**: リクエスト種別の型安全な識別（Docker, File, Shell, Python, Composite等）
- **操作インターフェース群**: 各種操作のピュアインターフェース定義
  - `ExecutionInterface`: 基本実行操作
  - `FileOperationInterface`: ファイル操作
  - `DockerOperationInterface`: Docker操作
  - `PythonOperationInterface`: Python実行
  - `ShellOperationInterface`: シェル実行
- **設計方針**: 副作用を持たない純粋インターフェースとしてドメインルールを表現

#### `base_composite_request.py`
- **CompositeRequestFoundation**: 複数リクエストを集約する基盤クラス
- **機能**:
  - サブリクエストの型安全な管理
  - 階層的な実行単位の提供
  - リーフリクエスト数のカウント機能
  - 実行結果の追跡
- **パターン**: Compositeパターンによる再帰的構造の実現

#### `config_node.py`
- **ConfigNode**: 階層的設定データの単一ノード表現
- **属性**:
  - `key`: ノードのキー
  - `value`: 設定値
  - `parent/next_nodes`: 親子関係
  - `matches`: エイリアス対応のマッチセット
- **設計**: 設定の木構造を効率的に表現

### ステップ処理システム

#### `step.py`
- **StepType列挙型**: 実行可能な操作種別（Shell, Python, Copy, Docker等33種類）
- **StepContext**: ステップ生成に必要な全ての不変コンテキスト情報
  - コンテスト情報（contest_name, problem_name）
  - 環境設定（language, env_type, command_type）
  - パス情報（workspace, current, stock, template）
  - ファイルパターン情報
- **Step**: 実行可能な単一ステップの不変表現
  - 型・コマンド・実行オプション・並列度設定
  - データ検証とタイプ別引数チェック
- **StepGenerationResult**: ステップ生成結果（ステップ配列・エラー・警告）

#### `step_runner.py`
- **ExecutionContext**: ステップ実行時のコンテキスト（StepContextより詳細）
- **テンプレート展開**: `{variable}`形式の文字列置換
  - 新旧設定システム対応
  - 複数のコンテキストタイプ対応
  - エラー時の明確な例外発生
- **ファイルパターン処理**: ワイルドカードパターンの実ファイル展開
- **test条件評価**: `test -d path`形式の条件式評価
- **ステップ実行パイプライン**: JSON→Step変換→実行の流れ

#### `dependency.py`
- **依存関係解決**: ステップ間の依存を分析し必要な準備ステップを自動挿入
- **主要機能**:
  - `resolve_dependencies`: メイン解決関数
  - `generate_preparation_steps`: MKDIR/TOUCHステップの自動生成
  - `analyze_step_dependencies`: ファイル作成/使用の依存分析
  - `optimize_mkdir_steps`: 連続MKDIRステップの最適化
  - `optimize_copy_steps`: 冗長コピー操作の除去
- **設計**: 純粋関数によるステップリスト変換

### ワークフロー管理

#### `workflow.py`
- **完全純粋関数パイプライン**: JSONステップ→最適化済みCompositeRequestまでの一貫した変換
- **主要関数**:
  - `generate_workflow_from_json`: メインパイプライン関数
  - `steps_to_requests`: Step配列のリクエスト変換
  - `optimize_workflow_steps`: ステップ最適化の統合
  - `validate_workflow_execution`: 実行前検証
- **依存性注入**: infrastructure層への直接依存を排除
- **デバッグ支援**: 各段階の詳細な状態追跡機能

### エラーハンドリング

#### `composite_step_failure.py`
- **CompositeStepFailureError**: 複合ステップ失敗時の専用例外
- **機能**:
  - エラーコード自動分類
  - 一意エラーID生成
  - 提案・回復手順の提供
  - 構造化されたエラーメッセージ
- **統合**: operations層のエラー分類システムとの連携

### ログ・結果管理

#### `workflow_logger_adapter.py`
- **WorkflowLoggerAdapter**: src/loggingとワークフロー固有ログの橋渡し
- **機能**:
  - 設定駆動のアイコン・フォーマット管理
  - ステップライフサイクルログ（開始・成功・失敗）
  - 環境情報・準備フェーズのログ
  - 動的ログレベル変更
- **設定統合**: ConfigManagerInterface経由の設定取得

#### `workflow_result.py`
- **WorkflowExecutionResult**: ワークフロー実行結果の統一表現
- **構成要素**:
  - 成功/失敗状態
  - 実行結果配列
  - 準備フェーズ結果
  - エラー・警告リスト

### サービス層

#### `services/config_node_service.py`
- **設定ノード操作**: ConfigNodeの操作ユーティリティ
- **機能**:
  - `init_matches`: エイリアス初期化
  - `add_edge`: ノード間関係の構築
  - `path`: ノードパスの取得
  - `next_nodes_with_key`: キーマッチによる子ノード検索
  - `find_nearest_key_node`: BFS による最近傍ノード検索

#### `services/step_generation_service.py`
- **ステップ生成統合**: 新旧システム互換性を持つステップ生成サービス
- **主要機能**:
  - コンテキスト変換（Typed↔Simple ExecutionContext）
  - JSON→Step変換パイプライン
  - テンプレート・ファイルパターン展開
  - ステップシーケンス検証・最適化
- **互換性**: 複数のコンテキストタイプに対応

#### `services/workflow_execution_service.py`
- **WorkflowExecutionService**: EnvWorkflowServiceの代替実装
- **実行フロー**:
  1. 設定取得（並列実行設定・ワークフローステップ）
  2. ワークフロー準備（JSON→最適化済みCompositeRequest）
  3. 環境準備フェーズ実行
  4. メインワークフロー実行（並列/逐次選択）
  5. 結果分析・エラーハンドリング
- **依存性注入**: infrastructure層のサービス利用

## 依存関係とデータフロー

### 層間依存関係
```
domain/ (本層)
├── ← operations/ (Request作成、エラー分類)
├── ← configuration/ (設定解決)
├── ← logging/ (ログ出力)
└── ← utils/ (フォーマット情報)
```

### 内部データフロー
```
JSON Steps → StepGenerationService → Step[] → dependency.py → Step[] (resolved)
                                                           ↓
CompositeRequest ← workflow.py ← optimize_workflow_steps ← Step[] (optimized)
       ↓
WorkflowExecutionService → infrastructure drivers → WorkflowExecutionResult
```

### 主要な変換パイプライン
1. **設定→コンテキスト**: 環境設定からStepContext/ExecutionContext生成
2. **JSON→ステップ**: 設定JSONから実行可能Step配列生成
3. **依存解決**: ステップ間依存関係分析と準備ステップ挿入
4. **最適化**: 冗長ステップ除去とシーケンス効率化
5. **リクエスト化**: StepからCompositeRequest変換
6. **実行**: infrastructure経由での実際の操作実行

## 設計パターンと実装方針

### 採用パターン
- **Strategy Pattern**: 各種操作インターフェースによる実装切り替え
- **Composite Pattern**: CompositeRequestFoundationによる階層的構造
- **Template Method Pattern**: ワークフロー実行の共通フレームワーク
- **Factory Pattern**: Step/Request生成の統一インターフェース
- **Adapter Pattern**: WorkflowLoggerAdapterによるログシステム統合

### 関数型プログラミング要素
- **純粋関数**: dependency.py, workflow.pyの変換関数群
- **不変データ**: Step, StepContext, StepGenerationResult
- **関数合成**: パイプライン形式のデータ変換

### 設計原則
- **単一責任**: 各クラス・関数が明確な単一責務
- **開放閉鎖**: インターフェースによる拡張性確保
- **依存性逆転**: 抽象への依存、具象からの独立
- **設定駆動**: ハードコードを排除し設定ファイルから値取得

## 注意事項とメンテナンス要点

### 設定管理の重要事項
- **デフォルト値禁止**: CLAUDE.mdに従い、設定ファイルから必須取得
- **フォールバック処理禁止**: エラーを隠蔽せず明示的な例外発生
- **設定パス**: 階層的パス指定による構造化アクセス

### 依存性注入の徹底
- **infrastructure層**: 全てmain.pyから注入
- **副作用の局所化**: infrastructure層のみに制限
- **テスト容易性**: モックインターフェースによる単体テスト

### 互換性維持
- **新旧システム対応**: TypedExecutionConfiguration ↔ ExecutionContext変換
- **段階的移行**: 既存コードとの共存期間を考慮
- **明示的コメント**: 互換性維持箇所の文書化

### エラーハンドリング
- **構造化例外**: エラーコード・提案・回復手順の統一
- **ログ統合**: 統一ログシステムによる一貫した出力
- **デバッグ支援**: 実行段階の詳細な状態追跡

### パフォーマンス考慮
- **並列実行**: ステップレベル・ワークフローレベルの並列化
- **最適化**: 冗長操作除去・シーケンス効率化
- **メモリ効率**: 不変データによるコピー最小化

### コードベース全体との整合性
- **命名規則**: 一貫したクラス・関数名
- **型安全性**: 列挙型・データクラスによる型チェック
- **文書化**: 各モジュール・関数の目的と責務の明記