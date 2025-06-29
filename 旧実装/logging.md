# Logging層の処理概要

## 責務と役割

src/logging配下は、アプリケーション全体のログ出力機能を統一的に提供する責務を担っています。主な役割は以下の通りです：

1. **ログレベル管理**: DEBUG, INFO, WARNING, ERROR, CRITICALの5段階
2. **フォーマット機能**: テキスト装飾（色、太字）やアイコンによる視覚的強化
3. **複数実装の提供**: ApplicationLoggerAdapter（シンプル）とUnifiedLogger（高機能）
4. **統一インターフェース**: LoggerInterfaceに準拠したアダプター設計
5. **構造化ログ**: 関連ID、操作追跡、セッション管理

## ファイル別詳細分析

### `__init__.py`
- 空ファイル（パッケージ定義のみ）

### `log_format_type.py`
- **責務**: ログ出力形式の定義
- **内容**: LogFormatType enum（PLAIN, COLORED, JSON, STRUCTURED）
- **特徴**: 将来的な拡張性を考慮した設計

### `log_types.py`
- **責務**: 基本的なログ型定義
- **主要クラス**:
  - `LogLevel(IntEnum)`: ログレベル定義（10-50の数値）
  - `BaseLogEntry`: ログエントリの基本構造（dataclass）
- **特徴**: タイムスタンプ自動設定、immutableな設計

### `types.py`
- **責務**: より高度なログエントリ型定義
- **主要クラス**:
  - `LogEntry`: FormatInfo対応のログエントリ
- **特徴**: 
  - Duck typingによるcontent処理（output()メソッド期待）
  - formatted_contentプロパティでフォーマット適用
  - BaseLogLevelとの互換性維持

### `application_logger_adapter.py`
- **責務**: LoggerInterfaceの基本実装
- **主要クラス**: ApplicationLoggerAdapter
- **機能**:
  - 標準的なログレベル出力（debug, info, warning, error, critical）
  - 構造化エラーログ（correlation ID、エラーコード）
  - 操作追跡ログ（operation start/end）
  - セッション追跡（UUID生成）
- **依存関係**:
  - OutputManagerInterfaceへの委譲
  - DIContainerからconfig_manager取得
  - FormatInfoによる装飾

### `unified_logger.py`
- **責務**: 包括的なログ機能の提供
- **主要クラス**: UnifiedLogger
- **高度な機能**:
  - アイコンベースの視覚的表現
  - ワークフロー向け専用メソッド（step_start, step_success, step_failure）
  - 環境情報ログ（言語、コンテスト、問題名）
  - 動的ログレベル変更
  - フォーマット引数の検証
- **設定依存**:
  - アイコン設定の3層構造（DEFAULT_ICONS < config < user）
  - 実行モード設定（並列/順次）
  - 環境情報表示設定

## 依存関係とデータフロー

```
外部呼び出し
    ↓
LoggerInterface実装
(ApplicationLoggerAdapter / UnifiedLogger)
    ↓
OutputManagerInterface
    ↓
LogEntry (types.py) 
    ↓
FormatInfo適用
    ↓
実際の出力
```

### 主要な依存関係
- **上位依存**: 
  - `src.operations.interfaces.utility_interfaces.LoggerInterface`
  - `src.operations.interfaces.utility_interfaces.OutputManagerInterface`
- **下位依存**:
  - `src.utils.format_info.FormatInfo`
  - `src.infrastructure.di_container.DIContainer`
- **設定依存**:
  - `config/system/logging_config.json`

### データフロー
1. **ログ要求受信**: アプリケーションからのログ出力要求
2. **メッセージ処理**: 引数フォーマット、装飾情報付与
3. **レベル判定**: ログレベルに基づく出力制御
4. **出力委譲**: OutputManagerへの実際の出力処理委譲
5. **フォーマット適用**: 色、太字、アイコンなどの視覚効果

## 設計パターンと実装方針

### アダプターパターン
- LoggerInterfaceを実装し、OutputManagerInterfaceに処理を委譲
- 異なる出力機構への統一的なアクセスを提供

### 設定駆動設計
- アイコン、色、ステータス文言を外部設定で制御
- 環境別・用途別のカスタマイズが可能

### レイヤード・アーキテクチャ
- logging層は純粋にログ機能のみに集中
- 実際の出力処理はapplication層に委譲

### 型安全性の確保
- dataclass、Enum、型ヒントを積極活用
- 実行時エラーを最小化

## 注意事項とメンテナンス要点

### 設定管理の注意点
- UnifiedLoggerは設定依存が強く、config_manager必須
- 設定不備時は適切な例外を発生（ValueError）
- フォールバック処理は原則禁止（CLAUDE.md準拠）

### フォーマット引数の検証
- UnifiedLoggerでは_validate_format_argsで厳密検証
- 不正なフォーマット文字列での実行時エラーを防止

### 互換性維持
- log_types.pyとtypes.pyでLogLevel再エクスポート
- BaseLogEntryとLogEntryの使い分け

### 拡張時の考慮点
- 新しいログレベル追加時はIntEnum値を適切に設定
- アイコン追加時は3層設定構造を維持
- 新しいアダプター追加時はLoggerInterface準拠を徹底

### テスト容易性
- DIContainer経由の依存注入によりモック化可能
- 各コンポーネントが疎結合で単体テスト実施しやすい

### パフォーマンス考慮
- realtime=Falseでバッファリング出力
- 不要な文字列処理を回避する設計