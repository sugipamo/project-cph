# 永続化リポジトリ関連のエラー

## 概要
Docker関連のリポジトリテストで全41テストがエラーとなっています。

## 現在の状況
実際のテスト実行結果（2025-06-21確認）:
- ✅ **修正完了**: 全41テストが正常に通過
- 最初のエラー: `FastSQLiteManager.__init__() missing 1 required positional argument: 'sqlite_provider'`

## 根本原因
**FastSQLiteManagerのコンストラクタ引数の変更**
- 現在の実装: `__init__(self, db_path: str, skip_migrations: bool, sqlite_provider)`
- テストフィクスチャ: `FastSQLiteManager(db_path=":memory:", skip_migrations=False)` ← `sqlite_provider`引数が不足

## 修正内容

### 1. テストフィクスチャの修正 ✅
**対象**: `tests/conftest.py:145`
```python
# 修正前
manager = FastSQLiteManager(db_path=":memory:", skip_migrations=False)

# 修正後
from src.infrastructure.providers.sqlite_provider import SystemSQLiteProvider
sqlite_provider = SystemSQLiteProvider()
manager = FastSQLiteManager(db_path=":memory:", skip_migrations=False, sqlite_provider=sqlite_provider)
```

### 2. テストコードの実装に合わせた修正 ✅
**対象**: `tests/persistence/test_docker_repositories.py`
- `DockerContainerRepository.create_container`の全ての呼び出しを修正（必須引数13個を明示的に指定）
- `DockerImageRepository.update`メソッドの`update_image_build_result`呼び出しを修正

### 3. 検証結果 ✅
```bash
$ pytest tests/persistence/test_docker_repositories.py -v
41 passed in 0.16s
```

## エラーテスト一覧

### DockerContainerRepository エラー (20件)
- `test_create_container_basic`
- `test_create_container_with_full_config`
- `test_update_container_id`
- `test_update_container_status`
- `test_find_container_by_name_existing`
- `test_find_container_by_name_nonexistent`
- `test_find_containers_by_status`
- `test_find_containers_by_language`
- `test_get_active_containers`
- `test_mark_container_removed`
- `test_find_unused_containers`
- `test_repository_interface_methods`
- `test_json_field_parsing`
- `test_json_field_parsing_invalid`
- `test_create_container_record_alias`
- `test_find_all_with_pagination`
- `test_update_nonexistent_container`
- `test_delete_nonexistent_container`
- `test_create_container_with_minimal_params`
- `test_create_container_with_all_params`

### DockerImageRepository エラー (21件)
- `test_create_or_update_image_new`
- `test_create_or_update_image_update_existing`
- `test_find_image_existing`
- `test_find_image_by_name_only`
- `test_find_image_nonexistent`
- `test_find_images_by_name_prefix`
- `test_find_images_by_status`
- `test_update_image_build_result`
- `test_get_all_images`
- `test_repository_interface_methods`
- `test_find_unused_images`
- `test_update_last_used`
- `test_delete_image`
- `test_get_image_stats`
- `test_concurrent_image_operations`
- `test_create_image_record_alias`
- `test_find_by_id_without_tag`
- `test_find_all_with_pagination`
- `test_update_nonexistent_image`
- `test_delete_nonexistent_image`
- `test_delete_by_id_without_tag`