# Utils層の処理概要

## 責務と役割

Utils層は、アプリケーション全体で共有される汎用的なユーティリティ機能を提供する層です。主な責務は以下の通りです：

- **純粋関数による汎用的な処理機能の提供**：副作用を持たない関数を中心に、再利用可能な処理を実装
- **外部システム・ライブラリの抽象化**：DockerやShell、正規表現処理などの外部依存を抽象化し、テスタビリティを向上
- **設定データのバリデーションと変換**：設定ファイルからのデータ取得と検証
- **エラーハンドリングとリトライ機構**：失敗に対する堅牢性を提供
- **プラットフォーム固有操作の抽象化**：OS固有の処理やファイルシステム操作の統一インターフェース

## ファイル別詳細分析

### 1. config_validation_utils.py
**責務**: 設定関連のバリデーションと取得
**主要機能**:
- `get_steps_from_resolver()`: ConfigResolverから言語・コマンドタイプに対応するstepsを取得
- 設定ノードの配列処理とソート機能
- エラーハンドリングとメッセージ生成

**依存関係**: `src.configuration.config_resolver`

### 2. docker_path_ops.py
**責務**: Docker特化のパス操作
**主要機能**:
- `should_build_custom_docker_image()`: イメージがローカルビルド対象かレジストリプル対象かを判定
- `convert_path_to_docker_mount()`: ホストパスをDockerマウントパスに変換
- `get_docker_mount_path_from_config()`: 設定からマウントパスを取得

**特徴**: 静的メソッドのみで構成、純粋関数として設計

### 3. docker_utils.py
**責務**: Docker操作の汎用ユーティリティ
**主要クラス**: `DockerUtils`
**主要機能**:
- `build_docker_cmd()`: Dockerコマンドの構築
- `parse_image_tag()`: イメージ名とタグの分離
- `format_container_name()`: コンテナ名のフォーマット
- `validate_image_name()`: イメージ名の妥当性検証

**互換性**: `validate_docker_image_name()`関数で後方互換性を維持

### 4. execution_validation_utils.py
**責務**: 実行コンテキストのバリデーション
**主要機能**:
- `validate_execution_context_data()`: ExecutionContextの基本バリデーション
- 必須フィールドの存在チェック
- 環境設定ファイルの検証

**特徴**: 純粋関数として設計、タプル形式で結果とエラーメッセージを返却

### 5. format_info.py
**責務**: ログフォーマット情報の管理
**主要クラス**: `FormatInfo`
**主要機能**:
- カラー、太字、インデント情報の保持
- フォーマットタイプに応じた文字列変換
- ANSI エスケープシーケンスの除去
- 辞書型との相互変換

**依存関係**: `src.application.color_manager`, `src.logging.log_format_type`

### 6. mock_regex_provider.py / regex_provider.py
**責務**: 正規表現操作の抽象化
**設計パターン**: Strategy Pattern + Dependency Injection
**主要機能**:
- 正規表現パターンのコンパイル
- 検索、置換、マッチング処理
- テスト用モック実装（MockRegexProvider）

**インターフェース**: `RegexInterface`を実装

### 7. path_operations.py
**責務**: ファイルパス操作の統合機能
**主要クラス**: `PathOperations`
**主要機能**:
- パス解決とnormalization
- 安全なパス結合
- 相対パス取得
- サブディレクトリ判定
- ファイル拡張子操作

**特徴**: 
- 依存性注入でconfig_providerを受け取り
- strict mode対応（Result型 vs 例外ベース）
- 互換性維持のコメント記載

### 8. python_utils.py
**責務**: Python実行関連のユーティリティ
**主要クラス**: `PythonUtils`
**主要機能**:
- スクリプトファイルの実行
- コード文字列の実行
- Pythonインタープリター管理
- エラーコード変換

**エラーハンドリング**: 
- フォールバック処理禁止の実装
- 設定必須の強制
- 適切な例外型の使用

### 9. retry_decorator.py
**責務**: リトライ機構の提供
**主要クラス**: `RetryConfig`, `RetryableOperation`
**主要機能**:
- 指数バックオフによるリトライ実装
- Result型ベースのエラーハンドリング
- 設定可能なリトライ条件
- 事前定義された設定（NETWORK_RETRY_CONFIG等）

**特徴**: 例外ベースとResult型ベースの両方をサポート

### 10. shell_utils.py
**責務**: シェルコマンド実行のユーティリティ
**主要クラス**: `ShellUtils`
**主要機能**:
- サブプロセス実行（同期/非同期）
- インタラクティブプロセス管理
- タイムアウト制御
- 出力キューイング

**特徴**: 静的メソッドのみで構成

### 11. sys_provider.py
**責務**: sysモジュールの副作用抽象化
**設計パターン**: Abstract Factory Pattern
**主要クラス**: 
- `SysProvider` (抽象基底クラス)
- `SystemSysProvider` (実装)
- `MockSysProvider` (テスト用)

**主要機能**:
- コマンドライン引数取得
- プログラム終了制御
- プラットフォーム情報取得
- 標準出力操作

### 12. time_adapter.py
**責務**: TimeProviderとTimeInterfaceの橋渡し
**設計パターン**: Adapter Pattern
**主要機能**:
- 現在時刻取得
- スリープ機能

**特徴**: インフラストラクチャ層とオペレーション層の結合

## 依存関係とデータフロー

### 内部依存関係
```
utils → configuration (config_validation_utils)
utils → application (format_info)
utils → logging (format_info)
utils → operations (path_operations, retry_decorator)
utils → infrastructure (time_adapter)
```

### 外部依存関係
- **標準ライブラリ**: os, pathlib, subprocess, re, time, contextlib, io
- **サードパーティ**: なし（標準ライブラリのみ使用）

### データフロー
1. **設定データ** → config_validation_utils → バリデーション済み設定
2. **パス情報** → path_operations → 正規化済みパス
3. **Docker設定** → docker_utils → 構築済みコマンド
4. **実行コンテキスト** → execution_validation_utils → バリデーション結果
5. **外部プロセス** → shell_utils → 実行結果

## 設計パターンと実装方針

### 採用されている設計パターン
1. **Strategy Pattern**: RegexProvider/MockRegexProvider
2. **Abstract Factory Pattern**: SysProvider系
3. **Adapter Pattern**: TimeAdapter
4. **Dependency Injection**: PathOperations, PythonUtils
5. **Builder Pattern**: DockerUtils.build_docker_cmd

### 実装方針
1. **純粋関数優先**: 副作用を持たない関数を中心に設計
2. **依存性注入**: 外部依存をコンストラクタで注入
3. **インターフェース分離**: 機能ごとに明確なインターフェースを定義
4. **エラーハンドリング統一**: Result型と例外ベースの両方をサポート
5. **テスタビリティ**: モッククラスの提供

### アーキテクチャ原則の遵守
- **フォールバック処理禁止**: 明示的な設定を要求
- **デフォルト値禁止**: 引数にデフォルト値を設定しない
- **副作用の局所化**: infrastructure層のみに副作用を限定
- **互換性維持**: 既存インターフェースの保持

## 注意事項とメンテナンス要点

### 1. 設計上の注意点
- **循環依存の回避**: 特にconfiguration層との相互依存に注意
- **純粋関数の維持**: 副作用を持つ処理はinfrastructure層に委譲
- **インターフェース安定性**: 既存のAPIを破壊しないよう慎重に変更

### 2. パフォーマンス考慮事項
- **ファイルパス操作**: 大量のパス処理時は結果のキャッシュを検討
- **リトライ処理**: 適切なタイムアウトとバックオフ設定が必要
- **正規表現**: パターンのコンパイル結果をキャッシュ

### 3. セキュリティ要点
- **パス操作**: パストラバーサル攻撃の防止
- **コマンド実行**: インジェクション攻撃の防止
- **Docker操作**: 不正なイメージ名の検証

### 4. テスト戦略
- **単体テスト**: 各ユーティリティ関数の境界値テスト
- **統合テスト**: 依存性注入されたコンポーネントとの連携テスト
- **モックテスト**: 外部依存を持つ処理のモック化

### 5. 将来の拡張ポイント
- **新しいプラットフォーム対応**: SysProviderの拡張
- **追加のリトライ戦略**: RetryConfigの設定パターン追加
- **パフォーマンス最適化**: キャッシュ機構の導入
- **ログ強化**: より詳細なデバッグ情報の提供

### 6. 依存関係管理
- **上位層への依存**: configuration, application層への依存は最小限に
- **インターフェース使用**: 具象クラスではなくインターフェースに依存
- **循環依存監視**: 定期的な依存関係チェックの実施