# SQLite/永続化関連のテスト失敗 - 現状と修正計画

## テスト状況サマリー（2025-06-21時点）

### ✅ 修正完了
- **FastSQLiteManager**: 全21テスト通過 - Mock object subscript エラーを修正

### ❌ 修正必要
- **SystemConfigLoader**: 3テスト失敗 - メソッドシグネチャ変更対応必要
- **ConfigurationRepository**: 2失敗/7エラー - 初期化引数不足

## 修正済みの問題

### FastSQLiteManagerクラス関連 ✅
**修正内容**: `_should_rollback_connection`メソッドでMockオブジェクトの添字アクセスエラーを修正
- 修正箇所: `src/infrastructure/persistence/sqlite/fast_sqlite_manager.py:266-279`
- 修正内容: Mock objectの配列アクセス時の適切なエラーハンドリング追加

**全テスト通過**: 21/21
- `test_init_memory_database_default` ✅
- `test_init_file_database` ✅
- `test_init_skip_migrations` ✅
- `test_init_custom_sqlite_provider` ✅
- `test_get_default_sqlite_provider` ✅
- `test_initialize_setup_file_database` ✅
- `test_initialize_shared_memory_db_first_time` ✅
- `test_initialize_shared_memory_db_subsequent_calls` ✅
- `test_setup_connection` ✅
- `test_get_connection_memory_database` ✅
- `test_get_connection_file_database` ✅
- `test_execute_query` ✅
- `test_execute_command_memory_database` ✅
- `test_execute_command_file_database` ✅
- `test_get_last_insert_id` ✅
- `test_get_last_insert_id_no_result` ✅
- `test_get_last_insert_id_zero_result` ✅
- `test_cleanup_test_data` ✅
- `test_reset_shared_connection` ✅
- `test_reset_shared_connection_when_none` ✅
- `test_thread_safety` ✅

## 現在の失敗

### SystemConfigLoader関連 ❌
**テスト結果**: 15通過/3失敗
**失敗原因**: CLAUDE.mdルール（デフォルト値禁止）によるメソッドシグネチャ変更

失敗テスト:
- `test_save_config_without_category` - `category`引数が必須になった
- `test_update_current_context_partial_params` - 複数の必須引数追加
- `test_update_current_context_with_old_values` - 複数の必須引数追加

### ConfigurationRepository関連 ❌
**テスト結果**: 0通過/2失敗/7エラー
**失敗原因**: 初期化時に`json_provider`と`sqlite_provider`引数が必須になった

失敗テスト:
- `test_init_with_default_path` - 必須引数不足
- `test_init_with_custom_path` - 必須引数不足

## 修正計画

### SystemConfigLoader修正計画
**対応方針**: テストケースを実装の変更に合わせて更新
1. `test_save_config_without_category` - `category`引数を明示的に指定するよう修正
2. `test_update_current_context_partial_params` - 必須引数を全て指定するよう修正
3. `test_update_current_context_with_old_values` - 必須引数を全て指定するよう修正

### ConfigurationRepository修正計画  
**対応方針**: テストケースで適切なProvider引数を注入
1. `test_init_with_default_path` - `json_provider`と`sqlite_provider`をモック注入
2. `test_init_with_custom_path` - `json_provider`と`sqlite_provider`をモック注入
3. 残りのエラーテスト - fixtureでプロバイダー引数追加

### その他の課題（未調査）
以下のテストは本修正の対象外だが、同様の問題の可能性:
- `tests_slow/test_sqlite_manager.py` の複数テスト
- `tests/persistence/test_docker_repositories.py` の複数テスト  
- `tests/persistence/test_system_config_repository.py` の複数テスト
- `tests/shell/test_shell_driver.py` の複数テスト

## 実装変更の背景

**CLAUDE.mdルール準拠**: デフォルト値禁止により、メソッドシグネチャが厳格化
- 引数にデフォルト値を指定するのを禁止
- 呼び出し元で値を用意することを徹底
- 副作用はsrc/infrastructure tests/infrastructure のみとする

**メンテナンス性向上**: 
- 依存性注入の明示化
- テストの保守性と実行速度向上
- 全体的な可読性とメンテナンス性向上