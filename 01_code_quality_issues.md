# コード品質問題

## 概要
コード品質に関する問題の分類と修正計画です。

## 修正計画
### 優先度: 高
1. `.get()` メソッド使用違反の修正
   - docker_image_repository.py:57,59,60の修正
   - 呼び出し元で必要な値を明示的に指定するよう変更

### 優先度: 中
2. カバレッジ向上（現在69% → 目標80%）
   - 低カバレッジファイルへのテスト追加
   - 特に0%カバレッジファイルの優先対応

### 優先度: 低
3. 命名規則の改善
   - sqlite_provider.py:154の関数名改善

## 命名規則の問題
- **infrastructure/providers/sqlite_provider.py:154** - 抽象的関数名 `execute` の使用

## テスト失敗
- **tests/cli/test_default_value_prohibition.py::TestDefaultValueProhibition::test_no_get_method_usage_in_source** - .get()メソッド使用違反:
  - src/infrastructure/persistence/sqlite/repositories/docker_image_repository.py:57,59,60

## カバレッジ不足（80%未満）
### 現在のカバレッジ: 69%
### 低カバレッジファイル一覧
- context/formatters/context_formatter.py: 0%
- infrastructure/drivers/docker/docker_driver_with_tracking.py: 0%
- operations/factories/request_factory.py: 18%
- infrastructure/result/result_factory.py: 19%
- infrastructure/result/error_converter.py: 24%
- infrastructure/drivers/unified/unified_driver.py: 28%
- operations/requests/docker/docker_request.py: 31%
- operations/requests/shell/shell_request.py: 33%
- infrastructure/persistence/sqlite/repositories/operation_repository.py: 33%
- infrastructure/persistence/sqlite/repositories/session_repository.py: 34%
- operations/requests/composite/composite_request.py: 36%
- operations/requests/composite/composite_structure.py: 37%
- infrastructure/mock/mock_docker_driver.py: 39%
- context/resolver/config_node_logic.py: 40%
- operations/pure/formatters.py: 40%
- その他多数（合計2439行未カバー）

## 対応状況
- 構文チェック: ✅ 完了
- インポート解決チェック: ✅ 完了
- クイックスモークテスト: ✅ 完了
- Ruff自動修正: ✅ 完了
- コード品質チェック (ruff): ✅ 完了
- 未使用コード検出: ✅ 完了
- 命名規則チェック: ✅ 完了
- 依存性注入チェック: ✅ 完了
- print使用チェック: ✅ 完了
- Infrastructure重複生成チェック: ✅ 完了
- フォールバック処理チェック: ✅ 完了
- dict.get()使用チェック: ❌ 修正必要
- テスト実行: ❌ 1件失敗（.get()使用違反）
- カバレッジ向上: ❌ 69%（目標80%未満）