# テスト修正戦略 4: パラメータシグネチャの完全修正

## 問題の概要

プロジェクトの「引数にデフォルト値を指定するのを禁止する」ポリシーにより、実装のメソッドシグネチャが変更されたが、テストコードが古いシグネチャのままとなっている。

## 現在の進捗状況

**✅ 完全修正済み**:
- `test_docker_driver.py`: すべてのメソッド呼び出しでパラメータを明示的に指定
- `test_docker_command_builder.py`: すべてのビルダー関数でパラメータを明示的に指定  
- `test_mock_file_driver.py`: MockFileDriverの初期化で`base_dir`パラメータを指定

**🔄 部分修正済み**:
- Docker関連テスト: 基本的なパラメータ修正は完了
- Mock関連テスト: 基本的な初期化パラメータは修正済み

**❌ 未修正の課題**:
- Logging関連テスト: 大量の未修正テストが残存
- Infrastructure統合テスト: 複合的なパラメータ問題
- その他のドライバーテスト: 各種ドライバーの個別課題

## パラメータシグネチャ修正パターン

### 1. **完了した修正パターン**

#### A. Docker Driver修正例

```python
# 修正前（失敗）
driver.remove_container("test-container")

# 修正後（成功）  
driver.remove_container("test-container", force=False, show_output=True)

# 修正前（失敗）
driver.run_container("ubuntu")

# 修正後（成功）
driver.run_container("ubuntu", name="test", options={}, show_output=True)
```

#### B. Docker Command Builder修正例

```python
# 修正前（失敗）
build_docker_run_command("ubuntu")

# 修正後（成功）
build_docker_run_command("ubuntu", "container-name", {})

# 修正前（失敗）
build_docker_ps_command()

# 修正後（成功）  
build_docker_ps_command(all=False, filter_params=[], format_string="table")
```

#### C. Mock File Driver修正例

```python
# 修正前（失敗）
driver = MockFileDriver()

# 修正後（成功）
driver = MockFileDriver(base_dir=Path("/tmp"))
```

### 2. **未修正パターンの特定**

#### A. Logging Driver未修正例

```python
# 現在の失敗パターン
def test_init_success(self):
    logger = UnifiedLogger()  # ❌ 必須パラメータ不足

# 必要な修正パターン
def test_init_success(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    config_manager = infrastructure.get_config_manager()
    output_manager = infrastructure.get_output_manager()
    
    logger = UnifiedLogger(
        output_manager=output_manager,
        config_manager=config_manager
    )
```

#### B. Output Manager未修正例

```python
# 現在の失敗パターン
def test_init_default_values(self):
    manager = OutputManager()  # ❌ 必須パラメータ不足

# 必要な修正パターン
def test_init_default_values(self):
    manager = OutputManager(
        level=LogLevel.INFO,
        name="test_manager",
        config_manager=None  # テスト用
    )
```

#### C. Application Logger Adapter未修正例

```python
# 現在の失敗パターン
def test_log_error_with_correlation(self):
    adapter = ApplicationLoggerAdapter()  # ❌ 必須パラメータ不足

# 必要な修正パターン
def test_log_error_with_correlation(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    base_logger = infrastructure.get_logger().base_logger
    config_manager = infrastructure.get_config_manager()
    
    adapter = ApplicationLoggerAdapter(
        logger=base_logger,
        config_manager=config_manager
    )
```

## 体系的修正アプローチ

### Phase 1: 実装シグネチャの完全調査

```python
# 調査すべき実装ファイル
IMPLEMENTATION_FILES = [
    "src/infrastructure/drivers/logging/unified_logger.py",
    "src/infrastructure/drivers/logging/output_manager.py", 
    "src/infrastructure/drivers/logging/adapters/application_logger_adapter.py",
    "src/infrastructure/drivers/logging/mock_output_manager.py",
    "src/infrastructure/environment/environment_manager.py",
    "src/infrastructure/persistence/sqlite/system_config_loader.py",
    "src/operations/requests/base_request.py",
    "src/operations/requests/python/python_request.py",
    "src/utils/retry_decorator.py"
]
```

#### A. UnifiedLoggerのシグネチャ調査

```python
# 実装確認が必要
class UnifiedLogger:
    def __init__(self, output_manager: OutputManager, config_manager: ConfigManager):
        # 必須パラメータの確認
```

#### B. OutputManagerのシグネチャ調査

```python
# 実装確認が必要  
class OutputManager:
    def __init__(self, level: LogLevel, name: str, config_manager: Optional[ConfigManager]):
        # 必須パラメータの確認
```

### Phase 2: 段階的修正計画

#### A. Critical Priority（緊急修正）

**Logging Drivers（45件の失敗）**:
1. `test_unified_logger.py` - UnifiedLoggerの初期化パラメータ修正
2. `test_output_manager.py` - OutputManagerの初期化パラメータ修正
3. `test_mock_output_manager.py` - MockOutputManagerの初期化パラメータ修正
4. `test_application_logger_adapter.py` - ApplicationLoggerAdapterの初期化パラメータ修正

**修正テンプレート**:
```python
# Before
def test_logger_function(self):
    logger = UnifiedLogger()

# After
def test_logger_function(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    output_manager = infrastructure.get_output_manager() 
    config_manager = infrastructure.get_config_manager()
    
    logger = UnifiedLogger(
        output_manager=output_manager,
        config_manager=config_manager
    )
```

#### B. High Priority（重要修正）

**Environment Manager（16件の失敗）**:
```python
# Before
def test_init_with_env_type(self):
    manager = EnvironmentManager("docker")

# After  
def test_init_with_env_type(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    config_manager = infrastructure.get_config_manager()
    
    manager = EnvironmentManager(
        env_type="docker",
        config_manager=config_manager,
        force_local=False
    )
```

**Base Request（7件の失敗）**:
```python
# Before
def test_init(self):
    request = OperationRequestFoundation()

# After
def test_init(self):
    request = OperationRequestFoundation(
        operation_type="test_operation",
        debug_mode=False
    )
```

#### C. Medium Priority（段階的修正）

**Python Request（8件の失敗）**:
```python
# Before  
def test_python_request_repr(self):
    request = PythonRequest("print('hello')")

# After
def test_python_request_repr(self):
    request = PythonRequest(
        code="print('hello')",
        cwd=".",
        timeout=300,
        debug_mode=False
    )
```

**Retry Decorator（4件の失敗）**:
```python
# Before
def test_default_config(self):
    config = RetryConfig()

# After
def test_default_config(self):
    config = RetryConfig(
        max_attempts=3,
        delay=1.0,
        backoff_factor=2.0,
        exceptions=(Exception,)
    )
```

### Phase 3: 自動化可能な修正パターン

#### A. 正規表現による一括修正

```python
# パターン1: 引数なしインスタンス化
PATTERN_1 = r'(\w+)\(\s*\)'
REPLACEMENT_1 = r'\1(/* 必要なパラメータを追加 */)'

# パターン2: 部分的パラメータ
PATTERN_2 = r'(\w+)\(([^)]+)\)'  
REPLACEMENT_2 = r'\1(\2, /* 追加パラメータ */)'
```

#### B. テンプレート生成

```python
# 共通修正テンプレート
COMMON_PATTERNS = {
    "Logger": """
def test_{method_name}(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    logger = infrastructure.get_logger()
    config_manager = infrastructure.get_config_manager()
    
    component = {class_name}(
        logger=logger.base_logger,
        config_manager=config_manager
    )
""",
    "Manager": """
def test_{method_name}(self, mock_infrastructure):
    infrastructure = mock_infrastructure
    config_manager = infrastructure.get_config_manager()
    
    component = {class_name}(
        config_manager=config_manager,
        /* 追加パラメータ */
    )
"""
}
```

## 修正の優先順位マトリクス

| コンポーネント | 失敗件数 | 修正難易度 | 影響度 | 優先度 |
|---------------|----------|------------|--------|--------|
| Logging Drivers | 45 | Medium | High | **Critical** |
| Environment Manager | 16 | Low | High | **High** |
| Persistence Layer | 25 | High | Medium | **High** |
| Mock File Driver | 8 | Low | Low | **Medium** |
| Base Request | 7 | Low | Medium | **Medium** |
| Python Request | 8 | Low | Low | **Low** |
| Retry Decorator | 4 | Low | Low | **Low** |

## 検証とテスト戦略

### 1. 段階的検証

```bash
# Phase 1: Logging修正の検証
python3 -m pytest tests/infrastructure/drivers/logging/ -v

# Phase 2: Environment修正の検証  
python3 -m pytest tests/infrastructure/environment/ -v

# Phase 3: 全体統合テスト
python3 -m pytest tests/infrastructure/ -v
```

### 2. 修正後のパフォーマンス測定

```bash
# 修正前後のテスト実行時間比較
python3 -m pytest tests/infrastructure/drivers/logging/ --durations=10

# 修正による新しい失敗の検出
python3 -m pytest tests/ --tb=short
```

### 3. リグレッションテスト

```bash
# 修正が他のテストに影響しないことを確認
python3 -m pytest tests/ -x -v
```

## 期待される結果

- **即座の効果**: Logging関連45件の失敗解消
- **中期的効果**: Environment、Persistence関連41件の失敗解消
- **長期的効果**: 全168件のパラメータ関連失敗の完全解消
- **品質向上**: プロジェクトの設計原則に完全準拠したテストコード

## 注意事項

- **互換性維持**: 既存の動作するテストに影響を与えないこと
- **設計原則遵守**: "デフォルト値禁止"ポリシーの完全遵守
- **段階的適用**: 一度に全修正せず段階的に適用
- **依存性管理**: フィクスチャとパラメータ修正の協調