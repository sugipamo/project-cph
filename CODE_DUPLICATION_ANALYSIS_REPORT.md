# コード重複分析レポート

プロジェクト内の重複コードを包括的に分析しました。以下に詳細な調査結果と推奨アプローチを記載します。

## 1. 関数・メソッドレベルの重複

### 1.1 高重要度の重複

#### パス解決ロジックの重複
- **ファイル**: 
  - `/home/cphelper/project-cph/src/operations/utils/path_utils.py` (行1-150)
  - `/home/cphelper/project-cph/src/env_resource/utils/path_utils.py` (行1-74)
- **重複内容**: 
  - `resolve_path()`, `ensure_parent_dir()`, `normalize_path()`等の基本的なパス操作関数
  - 両方とも`PathUtil`クラスとして実装
- **統合可能性**: ★★★★★
- **推奨アプローチ**: 
  - `src/utils/path_utils.py`に統一し、両方のモジュールから参照するように変更
  - 共通ベースクラスを作成して継承関係に整理

#### フォーマット関数の重複
- **ファイル**:
  - `/home/cphelper/project-cph/src/context/utils/format_utils.py` (行1-29)
  - `/home/cphelper/project-cph/src/utils/formatting.py` (行1-99)
- **重複内容**:
  - `extract_format_keys()` vs `extract_template_keys()`
  - `format_with_missing_keys()` vs `safe_format_template()`
- **統合可能性**: ★★★★★
- **推奨アプローチ**:
  - より包括的な`src/utils/formatting.py`に統一
  - `context/utils/format_utils.py`をdeprecated扱いにして段階的移行

### 1.2 中重要度の重複

#### execute()メソッドの共通パターン
- **ファイル**: 
  - `/home/cphelper/project-cph/src/operations/base_request.py` (行34-42)
  - 各Request系クラス（ShellRequest, FileRequest等）で同様の実装
- **重複内容**: 実行状態チェック、ドライバー検証、結果キャッシュ
- **統合可能性**: ★★★★☆
- **推奨アプローチ**: テンプレートメソッドパターンの強化

## 2. クラス・モジュールレベルの重複

### 2.1 高重要度の重複

#### Mock/Dummyドライバーの重複実装
- **ファイル**:
  - `/home/cphelper/project-cph/src/operations/mock/mock_docker_driver.py`
  - `/home/cphelper/project-cph/src/operations/docker/docker_driver.py` (DummyDockerDriver)
- **重複内容**: `DummyDockerDriver`が2箇所で重複定義
- **統合可能性**: ★★★★★
- **推奨アプローチ**: 
  - `mock_docker_driver.py`のDummyDockerDriverを削除
  - import文を調整して統一

#### ドライバーインターフェースの類似性
- **ファイル**:
  - `/home/cphelper/project-cph/src/operations/shell/shell_driver.py`
  - `/home/cphelper/project-cph/src/operations/file/file_driver.py`
  - `/home/cphelper/project-cph/src/operations/docker/docker_driver.py`
- **重複内容**: 抽象基底クラスパターン、メソッドシグネチャの一貫性
- **統合可能性**: ★★★☆☆
- **推奨アプローチ**: 共通ドライバーインターフェースの抽出を検討

### 2.2 Utils類の重複構造
- **ファイル**:
  - `/home/cphelper/project-cph/src/operations/shell/shell_utils.py`
  - `/home/cphelper/project-cph/src/operations/docker/docker_utils.py`
  - `/home/cphelper/project-cph/src/operations/python/python_utils.py`
- **重複内容**: Utilsクラスの構造と命名パターン
- **統合可能性**: ★★★☆☆
- **推奨アプローチ**: 共通Utilsベースクラスの検討

## 3. 設定・定数の重複

### 3.1 中重要度の重複

#### OperationType定数の散在
- **ファイル**: `/home/cphelper/project-cph/src/operations/constants/operation_type.py`
- **問題**: 各Requestクラスで同じ定数を参照するパターンの重複
- **統合可能性**: ★★★☆☆
- **推奨アプローチ**: 集約済みのため現状維持、使用パターンの標準化

#### デフォルト設定値の重複
- **ファイル**: 
  - `/home/cphelper/project-cph/src/operations/factory/driver_factory.py` (行14-18)
- **重複内容**: 複数箇所でのデフォルト値定義
- **統合可能性**: ★★★★☆
- **推奨アプローチ**: 設定管理クラスの導入

## 4. テストコードの重複

### 4.1 高重要度の重複

#### Mock/Dummyドライバーテストパターン
- **ファイル**:
  - `/home/cphelper/project-cph/tests/mock/test_mock_file_driver.py`
  - `/home/cphelper/project-cph/tests/mock/test_dummy_file_driver.py`
  - `/home/cphelper/project-cph/tests/file/test_local_file_driver.py`
- **重複内容**:
  - 同じテストケース構造（create_and_exists, move_and_copy等）
  - 類似したセットアップ処理
- **統合可能性**: ★★★★☆
- **推奨アプローチ**:
  - 共通テストベースクラス作成
  - parametrized testの活用

#### テストケース命名パターン
- **共通パターン**: `test_*_impl()`, `test_*_and_*_impl()`
- **重複内容**: 類似した振る舞いテストの繰り返し
- **推奨アプローチ**: テストユーティリティ関数の抽出

## 5. パターンやアーキテクチャの重複

### 5.1 高重要度の重複

#### ファクトリーパターンの重複実装
- **ファイル**:
  - `/home/cphelper/project-cph/src/operations/factory/driver_factory.py`
  - `/home/cphelper/project-cph/src/env_factories/unified_factory.py`
  - `/home/cphelper/project-cph/src/env_core/workflow/pure_request_factory.py`
- **重複内容**:
  - 同様のファクトリーメソッドパターン
  - タイプ判定ロジック
  - オブジェクト生成処理
- **統合可能性**: ★★★☆☆
- **推奨アプローチ**:
  - 責務の明確化（Driver生成 vs Request生成 vs Workflow生成）
  - 共通インターフェースの抽出

### 5.2 中重要度の重複

#### エラーハンドリングパターン
- **重複箇所**: 各Request実装でのtry-catch-finally
- **共通パターン**: start_time/end_time計測、OperationResult生成
- **推奨アプローチ**: デコレーターパターンによる共通化

#### ドライバー選択ロジック
- **重複箇所**: テスト/CI環境での自動選択ロジック
- **推奨アプローチ**: 環境検出ユーティリティの統一

## 重複解消の優先度と実装計画

### フェーズ1（高優先度）
1. **パス操作ユーティリティの統合**
   - `src/utils/path_utils.py`に統一
   - 既存コードの段階的移行

2. **フォーマット関数の統合**
   - `src/utils/formatting.py`に統一
   - deprecation warningの追加

3. **DummyDockerDriverの重複削除**
   - import文の整理
   - テストケースの調整

### フェーズ2（中優先度）
1. **テストベースクラスの導入**
   - 共通テストパターンの抽出
   - parametrized testへの移行

2. **ファクトリーパターンの整理**
   - 責務の明確化
   - 共通インターフェースの定義

### フェーズ3（低優先度）
1. **エラーハンドリングの共通化**
   - デコレーターパターンの導入
   - 統一的なロギング

2. **設定管理の統合**
   - 中央集権的な設定クラス
   - 環境別設定の整理

## 期待される効果

- **保守性向上**: 重複コード削減により、変更時の影響範囲を限定
- **テスト効率化**: 共通テストパターンにより、新機能のテスト作成コスト削減
- **一貫性向上**: 統一されたパターンによる開発者体験の改善
- **バグ削減**: 重複による不整合リスクの軽減

## 注意事項

- 段階的リファクタリングによる後方互換性の維持
- テストカバレッジの確保
- 既存機能への影響最小化
- チーム内での合意形成

このレポートに基づき、優先度の高い項目から段階的にリファクタリングを実施することを推奨します。