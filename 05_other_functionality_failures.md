# その他機能関連のテスト失敗

## 概要
テストフィクスチャや設定関連など、その他の機能に関するテスト失敗です。

## 失敗したテスト（現在の状況）

### テストフィクスチャ関連
- `test_mock_infrastructure_fixture` - TypeError (DockerResult constructor)
- `test_mock_drivers_fixture` - TypeError (DockerResult constructor)  
- `test_clean_mock_state_fixture` - TypeError (依存関係エラー)

## 確認された具体的問題

### 1. MockDockerDriverのコンストラクタエラー
**ファイル**: `src/infrastructure/mock/mock_docker_driver.py:17`
**エラー**: `DockerResult.__init__() missing 2 required positional arguments: 'container_id' and 'image'`
**原因**: DockerResultクラスが新しく`container_id`と`image`引数を必須としたが、MockDockerDriverが古い署名で呼び出している

### 2. MockShellDriverの論理エラー  
**ファイル**: `src/infrastructure/mock/mock_shell_driver.py:57,80`
**問題**: 存在しないキーに対して`self._responses[cmd_str]`を直接参照してKeyErrorが発生する可能性

### 3. BaseRequestの署名変更
**影響**: `OperationRequestFoundation.__init__()`の署名変更によりテストの互換性が破綻

## 詳細修正計画

### 高優先度修正（必須）
1. **MockDockerDriverの修正** - `src/infrastructure/mock/mock_docker_driver.py`
   - DockerResultの呼び出しに`container_id`と`image`引数を追加
   - デフォルト値またはモック値を適切に設定

2. **MockShellDriverの修正** - `src/infrastructure/mock/mock_shell_driver.py`  
   - KeyError対策の条件分岐を追加
   - 未定義コマンドに対するデフォルト応答の実装

3. **BaseRequestテストの修正**
   - コンストラクタ署名の変更に対応
   - テストケースの引数を更新

### 中優先度修正
4. テストフィクスチャの依存関係整理
5. conftest.pyのクリーンアップ処理改善

## 現在の動作状況
- ✅ `temp_workspace`フィクスチャ - 正常動作
- ✅ `di_container`フィクスチャ - 正常動作  
- ✅ `mock_env_context`フィクスチャ - 正常動作
- ✅ MockFileDriverのテスト - 全て通過(8/8)
- ❌ `mock_infrastructure`フィクスチャ - MockDockerDriverエラー
- ❌ `mock_drivers`フィクスチャ - 上記依存関係でエラー
- ❌ `clean_mock_state`フィクスチャ - 上記依存関係でエラー

## 影響範囲
- `src/infrastructure/mock/mock_docker_driver.py` (即座修正必要)
- `src/infrastructure/mock/mock_shell_driver.py` (即座修正必要)
- `tests/conftest.py` (フィクスチャ定義)
- `tests/test_conftest_fixtures.py` (フィクスチャテスト)
- BaseRequestを使用する全テストケース

## 追加情報
### 低カバレッジファイル（80%未満）
以下のファイルはテストカバレッジが低く、テスト不足の可能性があります：

- context/formatters/context_formatter.py: 0%
- infrastructure/drivers/docker/docker_driver_with_tracking.py: 0%
- operations/factories/request_factory.py: 18%
- infrastructure/persistence/sqlite/repositories/docker_image_repository.py: 19%
- infrastructure/result/result_factory.py: 19%
- infrastructure/persistence/sqlite/repositories/docker_container_repository.py: 21%
- infrastructure/drivers/unified/unified_driver.py: 22%
- infrastructure/result/error_converter.py: 24%
- infrastructure/persistence/sqlite/repositories/system_config_repository.py: 28%
- infrastructure/mock/mock_docker_driver.py: 29%

これらのファイルについても、今後テストの追加や改善を検討する必要があります。