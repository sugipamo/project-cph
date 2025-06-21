# Driver Test Failure Analysis

## 実行概要

`scripts/test.py`の実行結果から、driver関連のテスト失敗要因を分析。

## 失敗テスト数

- **Docker Driver**: 13件
- **Docker Command Builder**: 12件  
- **Logging Drivers**: 45件
- **Mock File Driver**: 8件
- **その他Infrastructure**: 多数

## 根本原因

### 1. デフォルト値禁止ポリシーの徹底実装

プロジェクトの「引数にデフォルト値を指定するのを禁止する」ポリシーに従い、実装が更新されたが、テストコードが古い期待値のままとなっている。

### 2. 主要な失敗パターン

#### A. Docker Driver (`tests/infrastructure/drivers/docker/test_docker_driver.py`)

```python
# テストの期待値
driver.remove_container("test-container")

# 実際の実装
def remove_container(self, name: str, force: bool, show_output: bool)

# エラー: missing 2 required positional arguments: 'force' and 'show_output'
```

**失敗メソッド**:
- `remove_container()` - force, show_outputパラメータ必須
- `exec_in_container()` - 追加の必須パラメータ
- `get_logs()` - パラメータ仕様変更
- `build_docker_image_success()` - 構築パラメータ必須
- `image_ls()`, `image_rm()` - イメージ操作パラメータ必須
- `ps_basic()`, `ps_names_only()` - プロセス一覧パラメータ必須

#### B. Docker Command Builder (`tests/infrastructure/drivers/docker/utils/test_docker_command_builder.py`)

```python
# テストの期待値
build_docker_ps_command()

# 実際の実装
def build_docker_ps_command(all: bool, filter_params: list[str], format_string: str)

# エラー: missing 3 required positional arguments
```

**失敗メソッド**:
- `build_docker_run_command_*()` - 実行コマンド構築
- `build_docker_stop_command()` - 停止コマンド構築
- `build_docker_build_command_*()` - ビルドコマンド構築
- `build_docker_ps_command_basic()` - プロセス一覧コマンド構築
- `build_docker_inspect_command_basic()` - 検査コマンド構築
- `build_docker_exec_command_basic()` - 実行コマンド構築
- `build_docker_logs_command_basic()` - ログコマンド構築

#### C. Mock File Driver (`tests/mock/test_mock_file_driver.py`)

```python
# テストの期待値
driver = MockFileDriver()

# 実際の実装
def __init__(self, base_dir: Path)

# エラー: missing 1 required positional argument: 'base_dir'
```

**失敗メソッド**:
- `__init__()` - base_dirパラメータ必須
- `open()` - encodingパラメータ必須
- すべてのファイル操作メソッド - 明示的パラメータ必須

#### D. Logging Drivers (複数ファイル)

**主な問題**:
- `UnifiedLogger` - 依存性注入の設定管理必須
- `OutputManager` - 構成管理の注入必須
- `ApplicationLoggerAdapter` - アダプタ設定の明示必須

### 3. ShellRequest構築の変更

```python
# テストの期待値
ShellRequest(["docker", "ps"], show_output=True)

# 実際の実装
ShellRequest(cmd, cwd=".", env={}, inputdata="", timeout=300, 
            debug_tag="docker_run", name="docker_run_request", 
            show_output=show_output, allow_failure=False)
```

### 4. 依存性注入の要求

- **Configuration Manager**: テストで適切にモックまたは注入が必要
- **DI Container**: 依存性注入コンテナの適切な設定が必要
- **Infrastructure Dependencies**: 基盤となる依存関係の初期化が必要

## 修正方針

### 1. テストシグネチャの更新

すべてのテストメソッド呼び出しを実際の実装シグネチャに合わせる。

### 2. 必須パラメータの提供

以前にオプションだったパラメータを明示的に提供する。

### 3. 依存関係のモック

構成管理、DIコンテナ、その他のインフラストラクチャを適切にモックする。

### 4. アサーションの更新

完全なパラメータ仕様を考慮してテストアサーションを更新する。

## 具体的な修正例

### Docker Driver
```python
# 修正前
driver.remove_container("test-container")

# 修正後
driver.remove_container("test-container", force=False, show_output=True)
```

### Command Builder
```python
# 修正前
build_docker_ps_command()

# 修正後
build_docker_ps_command(all=False, filter_params=[], format_string="")
```

### Mock File Driver
```python
# 修正前
driver = MockFileDriver()

# 修正後
driver = MockFileDriver(base_dir=Path("/tmp"))
```

## 結論

これらの失敗は**実装のバグではなく**、プロジェクトのアーキテクチャ原則の厳格な実装の結果である：

- デフォルト値の禁止（厳格なパラメータ仕様）
- すべての依存関係の明示的な注入
- インフラストラクチャコンポーネントの完全な設定要求

修正には、進化した実装シグネチャに合わせて包括的なテスト更新が必要である。