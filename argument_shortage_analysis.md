# TypeError（引数不足）エラー分析レポート

## 概要
scripts/test.py実行時に発生したTypeError（引数不足）に関するエラーの詳細分析結果です。

## 主要なTypeErrorパターン

### 1. ConfigurationRepository関連
```
TypeError: ConfigurationRepository.__init__() missing 2 required positional arguments: 'json_provider' and 'sqlite_provider'
```

**影響を受けるファイル:**
- `tests/infrastructure/persistence/test_configuration_repository.py`

**問題箇所:**
- `ConfigurationRepository(temp_db_path)` で1つの引数のみで呼び出し
- 実際の定義では `__init__(self, db_path: str, json_provider, sqlite_provider)` で3つの引数が必須

### 2. FastSQLiteManager関連
```
TypeError: FastSQLiteManager.__init__() missing 1 required positional argument: 'sqlite_provider'
```

**影響を受けるファイル:**
- `tests/conftest.py` (line 145)
- 多数のdockerリポジトリテスト

**問題箇所:**
- `FastSQLiteManager(db_path=":memory:", skip_migrations=False)` で呼び出し
- 実際の定義では `sqlite_provider` が必須引数として追加されている

### 3. MockFileDriver関連
```
TypeError: MockFileDriver.__init__() missing 1 required positional argument: 'base_dir'
```

**影響を受けるファイル:**
- `tests/mock/test_mock_file_driver.py`
- `tests/shell/test_shell_driver.py`

**問題箇所:**
- `MockFileDriver()` で引数なしで呼び出し
- 実際の定義では `__init__(self, base_dir: Path)` で `base_dir` が必須

### 4. ShellResult関連
```
TypeError: ShellResult.__init__() missing 8 required positional arguments
```

**影響を受けるファイル:**
- 複数のshell関連テスト

**問題箇所:**
- `ShellResult` の初期化時に8個の必須引数が不足
- モックshellドライバーでデフォルトレスポンス作成時に発生

### 5. SystemConfigRepository関連
```
TypeError: SystemConfigRepository.__init__() missing 1 required positional argument: 'config_manager'
```

**影響を受けるファイル:**
- `tests/persistence/test_system_config_repository.py`

## 不足している引数の詳細

| クラス名 | 不足している引数 | 引数の型/目的 |
|---------|----------------|--------------|
| ConfigurationRepository | `json_provider`, `sqlite_provider` | JSON操作とSQLite操作のプロバイダー |
| FastSQLiteManager | `sqlite_provider` | SQLite操作プロバイダー |
| MockFileDriver | `base_dir` | ベースディレクトリのPath |
| ShellResult | 複数（8個） | 実行結果の詳細情報 |
| SystemConfigRepository | `config_manager` | 設定管理マネージャー |

## 影響範囲

### 失敗したテスト統計
- **FAILED**: 約70個のテスト失敗
- **ERROR**: 約60個のテストエラー
- **合計**: 約130個のテスト失敗

### 主要な影響ファイル
1. `tests/infrastructure/persistence/sqlite/test_fast_sqlite_manager.py`
2. `tests/infrastructure/persistence/test_configuration_repository.py`
3. `tests/mock/test_mock_file_driver.py`
4. `tests/shell/test_shell_driver.py`
5. `tests/persistence/test_docker_repositories.py`

## 根本原因

### プロジェクト指針との整合性問題
- CLAUDE.mdで「引数にデフォルト値を指定するのを禁止する」と明記
- テストコードでは従来のデフォルト値前提の呼び出し方法を使用
- 依存性注入の強化により、プロバイダーの明示的な注入が必須になった

### 主な問題点
1. **デフォルト値の削除**: 引数のデフォルト値が削除されたことで、従来の呼び出し方法が無効になった
2. **依存性注入の強化**: プロバイダーの明示的な注入が必要になった
3. **テストコードの更新不足**: 実装の変更に対してテストコードが追従していない

## 修正が必要な箇所の優先度

### 高優先度
1. **テストフィクスチャの修正** (`conftest.py`)
   - FastSQLiteManagerの初期化で`sqlite_provider`を追加
2. **MockFileDriverの引数指定**
   - `base_dir`引数の追加
3. **ConfigurationRepository関連テストの修正**
   - `json_provider`と`sqlite_provider`の注入

### 中優先度
1. **ShellResult初期化の修正**
   - 8個の必須引数の適切な指定
2. **SystemConfigRepository関連テストの修正**
   - `config_manager`の注入

## 推奨される対応策

1. **共通テストフィクスチャの作成**
   - 依存性注入に対応したテスト用プロバイダーの準備
2. **テストヘルパー関数の実装**
   - 頻繁に使用されるクラスの初期化をサポート
3. **段階的修正**
   - 高優先度の箇所から順次修正を実施

## 注意事項

- **互換性維持**: 既存の機能に影響を与えないよう注意
- **設定ファイルの編集**: ユーザーから明示された場合のみ許可
- **副作用の制限**: `src/infrastructure` と `tests/infrastructure` のみで許可