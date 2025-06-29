# Operations層の処理概要

## 責務と役割

Operations層は、アプリケーション層とドメイン層の間で操作の標準化と結果処理を担当する中間層です。主な責務は以下の通りです：

### 主要責務
1. **操作リクエストの抽象化**: 具体的な実装に依存しない操作リクエストの統一インターフェース提供
2. **結果オブジェクトの標準化**: 各種操作の結果を統一された形式で表現
3. **エラーハンドリングの標準化**: 例外処理をResult型で明示的に管理
4. **コマンドパターンの実装**: 操作をオブジェクトとして扱い、検証・実行を分離
5. **複合操作の管理**: 複数の操作を組み合わせた処理の構造化

### アーキテクチャ上の位置付け
- インフラストラクチャ層への依存を抽象化
- ドメイン層の操作要求をインフラストラクチャ層向けに変換
- CLAUDE.mdの制約に従い、副作用はインフラストラクチャ層のみに限定

## ファイル別詳細分析

### コア抽象化レイヤー

#### `__init__.py`
- **役割**: モジュールの公開APIを定義
- **主要エクスポート**:
  - 結果型クラス群 (InfrastructureResult, CheckResult, ExecutionResultBase)
  - 専用結果型 (FileResult, OperationResult)
  - ファクトリクラス (ResultFactory)
- **設計方針**: 外部からは具体的な実装を隠蔽し、必要な抽象化のみを公開

#### `base_command.py`
- **役割**: コマンドパターンの基底クラス定義
- **主要クラス**: `Command` (ABC)
- **機能**:
  - コマンドの名前・エイリアス・説明の管理
  - 実行前の検証機能 (`validate`)
  - 実行ステップの取得 (`get_steps`)
  - コマンド文字列のマッチング (`matches`)
- **設計パターン**: Command Pattern + Template Method Pattern

#### `composite_structure.py`
- **役割**: 複合リクエストの構造管理
- **主要クラス**: `CompositeStructure`
- **機能**:
  - 複数のOperationRequestFoundationの管理
  - リーフリクエストの再帰的カウント
  - 最適化された構造の作成 (`make_optimal_structure`)
- **設計パターン**: Composite Pattern

### エラー処理・例外管理

#### `error_codes.py`
- **役割**: 構造化されたエラーコード管理
- **主要要素**:
  - `ErrorCode` enum: 標準化されたエラーコード定義
  - `ErrorSuggestion`: エラー回復のための提案機能
  - `classify_error`: 例外の自動分類機能
- **カバー範囲**: ファイル操作、シェル実行、Docker操作、Python実行、設定、ワークフロー、ネットワーク

#### `error_converter.py`
- **役割**: 例外をResult型に変換（CLAUDE.md準拠の唯一のtry-catch実装箇所）
- **主要クラス**: `ErrorConverter`
- **重要機能**:
  - `execute_with_conversion`: 汎用的な例外変換
  - `execute_with_error_mapping`: 例外の事前変換
  - 各種ドライバー専用変換メソッド（Shell, Docker, File）
- **設計原則**: インフラ層の副作用制約を守る唯一の例外処理実装

#### `python_exceptions.py`
- **役割**: Python固有の例外クラス定義
- **定義例外**:
  - `PythonConfigError`: Python設定エラー
  - `PythonEnvironmentError`: Python環境検出エラー
  - `PythonVersionError`: Pythonバージョン検証エラー
  - `PythonInterpreterError`: Pythonインタープリター関連エラー

### データ型・定数定義

#### `path_types.py`
- **役割**: パス操作専用のデータ型定義
- **主要クラス**:
  - `PathOperationResult`: パス操作結果の統一データクラス
  - `PathInfo`: 不変パス情報クラス（依存性注入対応）
- **特徴**: immutableデザインによる安全性確保

#### `constants/operation_type.py`
- **役割**: 操作種別の定数定義
- **主要enum**:
  - `OperationType`: 基本操作タイプ（SHELL, FILE, DOCKER, COMPOSITE, PYTHON等）
  - `FileOperationType`: ファイル操作種別
  - `DirectoryName`: ディレクトリ名定数
  - `FilePattern`: ファイルパターン定数
  - `PreparationAction`: Docker準備アクション

### インターフェース定義

#### `interfaces/execution_interfaces.py`
- **役割**: 実行系インターフェースの統合定義
- **主要インターフェース**:
  - `ExecutionInterface`: 純粋な実行インターフェース
  - `DockerDriverInterface`: Docker操作の完全インターフェース
  - `ShellExecutionInterface`: シェルコマンド実行
  - `PythonExecutionInterface`: Python実行

#### `interfaces/infrastructure_interfaces.py`
- **役割**: インフラストラクチャ系インターフェース定義
- **主要インターフェース**:
  - `FileSystemInterface`: ファイルシステム操作
  - `PersistenceInterface`: データベース永続化
  - `RepositoryInterface`: リポジトリパターン
  - `TimeInterface`: 時間操作

#### `interfaces/utility_interfaces.py`
- **役割**: ユーティリティ系インターフェース定義
- **主要インターフェース**:
  - `LoggerInterface`: ログ出力
  - `OutputManagerInterface`: 出力管理
  - `RegexInterface`: 正規表現操作
  - `DIContainerInterface`: 依存性注入コンテナ

### リクエスト処理

#### `requests/request_factory.py`
- **役割**: ステップオブジェクトからリクエストオブジェクトの生成
- **主要要素**:
  - `OperationRequestFoundation` Protocol: リクエスト基底プロトコル
  - `RequestCreator` Protocol: リクエスト作成抽象化
  - `RequestFactory`: 具体的なファクトリ実装
- **サポート操作**: Docker系操作、ファイル系操作、シェル実行、Python実行
- **設計原則**: クリーンアーキテクチャに準拠した依存性の逆転

#### `requests/composite_request.py`
- **役割**: 複合リクエストの具体実装
- **主要クラス**: `CompositeRequest`
- **機能**:
  - 複数リクエストの順次・並列実行
  - 実行制御との統合
  - リーフリクエスト数の管理
- **実行パターン**: 順次実行 (`_execute_core`) と並列実行 (`execute_parallel`)

### 結果処理

#### `results/base_result.py`
- **役割**: インフラストラクチャ層専用の基底Result型
- **主要クラス**:
  - `InfrastructureResult<T, E>`: ジェネリック結果型
  - `InfrastructureOperationResult`: 操作専用結果型
- **機能**: 関数型プログラミングスタイルのメソッド（`map`, `flat_map`, `or_else`）

#### `results/result.py`
- **役割**: 汎用Result型とバリデーション機能
- **主要クラス**:
  - `Result<T, E>`: 汎用結果型
  - `OperationResult`: 操作結果専用型
  - `ValidationResult`: バリデーション結果型
- **ユーティリティ**: バリデーション関数群（`validate_not_none`, `validate_not_empty`等）

#### `results/file_result.py`
- **役割**: ファイル操作専用の結果クラス
- **主要クラス**: `FileResult`
- **管理項目**: ファイルパス、内容、存在状態、操作種別、エラー情報、実行時間

#### `results/check_result.py`
- **役割**: インポートチェック専用の結果クラス
- **主要クラス**:
  - `CircularImport`: 循環インポート情報
  - `CheckResult`: チェック結果の統合データ
- **管理項目**: ファイル数、インポート数、循環インポート、エラー情報

#### `results/result_factory.py`
- **役割**: 標準化された結果オブジェクトの生成サービス
- **主要クラス**: `ResultFactory`
- **主要機能**:
  - 操作成功・失敗結果の統一生成
  - 各種ドライバー固有の結果生成（Shell, Docker, File）
  - 設定ファイルからのデフォルト値注入
  - エラー変換との統合

## 依存関係とデータフロー

### 依存関係構造
```
Operations層
├── Domain層 (base_request, base_composite_request)
├── Application層 (execution_results)
├── Configuration層 (設定ファイル読み込み)
└── Infrastructure層 (抽象化のみ、具体実装には非依存)
```

### データフロー
1. **リクエスト生成**: RequestFactory がワークフロー・ステップからリクエスト生成
2. **実行**: CompositeRequest が個別リクエストを実行制御
3. **結果変換**: ErrorConverter が例外をResult型に変換
4. **結果標準化**: ResultFactory が統一された結果オブジェクトを生成
5. **上位層への返却**: 標準化された結果がアプリケーション層に返却

### 抽象化レベル
- **高レベル**: Command抽象化、Result型
- **中レベル**: 各種Interface定義
- **低レベル**: 具体的なファクトリ実装、エラー分類

## 設計パターンと実装方針

### 採用パターン
1. **Command Pattern**: base_command.pyでのコマンド抽象化
2. **Composite Pattern**: 複合リクエストの階層構造管理
3. **Factory Pattern**: RequestFactory, ResultFactoryでのオブジェクト作成
4. **Strategy Pattern**: 各種インターフェースでの実装選択
5. **Result Pattern**: 例外に代わる明示的エラーハンドリング

### 実装方針
1. **CLAUDE.md準拠**: 副作用はインフラ層のみ、設定値の明示的解決
2. **依存性の逆転**: 抽象インターフェースに依存、具体実装には非依存
3. **型安全性**: Protocol, Generic, TypeVarを活用した厳密な型システム
4. **不変性**: dataclass(frozen=True)による安全なデータ管理
5. **テスタビリティ**: 依存性注入による単体テスト容易性

### エラーハンドリング戦略
1. **Result型の活用**: try-catchを廃止し、明示的な成功・失敗表現
2. **エラー分類**: 例外を構造化されたErrorCodeに分類
3. **回復提案**: ErrorSuggestionによる具体的な対処法提示
4. **集約地点**: ErrorConverterでの例外処理一元化

## 注意事項とメンテナンス要点

### 重要な制約事項
1. **例外処理の制限**: try-catchはErrorConverterのみで許可
2. **設定値の扱い**: デフォルト値使用禁止、設定ファイルからの明示的解決が必要
3. **副作用の制限**: 副作用を持つ処理はインフラ層に委譲
4. **互換性維持**: 既存インターフェースの変更時は互換性コメント必須

### メンテナンス要点
1. **インターフェース拡張**: 新機能追加時は対応するインターフェースを追加
2. **エラーコード管理**: 新しいエラータイプはErrorCodeとErrorSuggestionに追加
3. **結果型の統一**:新しい操作結果は既存のResult型に統合
4. **設定ファイル同期**: 新しいデフォルト値は対応する設定ファイルに記載

### 将来の拡張性
1. **非同期処理**: asyncインターフェースの追加余地
2. **分散処理**: リモート実行対応のインターフェース拡張
3. **メトリクス**: 実行時間・リソース使用量の詳細計測
4. **キャッシュ**: 操作結果のキャッシュメカニズム

### テスト戦略
1. **モック活用**: インターフェースベースのモック作成
2. **Result型テスト**: 成功・失敗ケースの網羅的テスト
3. **エラー分類テスト**: classify_error関数の例外パターン網羅
4. **ファクトリテスト**: 各種リクエスト・結果生成の正確性確認