# 命名改善計画

## 🎯 改善対象と優先度

### 最優先（Priority 1）: 汎用的すぎるファイル名

#### 1. `src/utils/helpers.py` → 機能別分割
**現状の問題:**
- ファイル名が汎用的で機能が予想できない
- 複数の責務が混在（文字列処理 + Docker機能 + データ処理）

**分割提案:**
```
src/utils/helpers.py →
├── src/utils/string_formatters.py    # 文字列・テンプレート処理
├── src/utils/docker_wrappers.py      # Docker関連のラッパー関数
└── src/utils/data_processors.py      # リスト・辞書処理
```

**含まれる機能:**
- 文字列処理: `format_template_string`, `extract_missing_template_keys`
- パス検証: `validate_file_path_format`, `is_potential_script_path`
- Docker: 8個のDocker関連ラッパー関数
- データ処理: `filter_and_transform_items`, `group_items_by_key`, `merge_dictionaries`

#### 2. `src/workflow/step/core.py` → `step_generation_service.py`
**現状の問題:**
- "core"は抽象的すぎる
- 実際はステップ生成とコンテキスト変換の機能

**改善提案:**
```
src/workflow/step/core.py → src/workflow/step/step_generation_service.py
```

**含まれる主要機能:**
- `expand_template()` - テンプレート展開
- `expand_file_patterns()` - ファイルパターン展開
- `execution_context_to_simple_context()` - コンテキスト変換
- `validate_step_sequence()` - ステップ検証

### 高優先度（Priority 2）: 抽象的すぎる関数名

#### 1. `BaseDriver.execute()` → `execute_command()`
**場所:** `src/infrastructure/drivers/base/base_driver.py:11`
```python
# Before
def execute(self, request) -> OperationResult:

# After  
def execute_command(self, request) -> OperationResult:
```

#### 2. `FileDriver.create()` → `create_file()`
**場所:** `src/infrastructure/drivers/file/file_driver.py:128`
```python
# Before
def create(self, path, content):

# After
def create_file(self, path, content):
```

#### 3. `DockerDriver.build()` → `build_docker_image()`
**場所:** `src/infrastructure/drivers/docker/docker_driver.py:44`
```python
# Before
def build(self, ...):

# After
def build_docker_image(self, ...):
```

### 中優先度（Priority 3）: 汎用的すぎるクラス名

#### 1. `BaseDriver` → `ExecutionDriverInterface`
**場所:** `src/infrastructure/drivers/base/base_driver.py:7`
```python
# Before
class BaseDriver(ABC):

# After
class ExecutionDriverInterface(ABC):
```

#### 2. `ConfigNode` → `HierarchicalConfigNode`
**場所:** 設定関連ファイル内
```python
# Before
class ConfigNode:

# After
class HierarchicalConfigNode:
```

### 低優先度（Priority 4）: 長すぎるファイル名

#### 1. `graph_based_workflow_builder.py` → `workflow_builder.py`
```
src/workflow/builder/graph_based_workflow_builder.py (35文字)
→ src/workflow/builder/workflow_builder.py
```

#### 2. `execution_context_adapter_original.py` → `context_adapter.py`
```
src/configuration/adapters/execution_context_adapter_original.py (43文字)
→ src/configuration/adapters/context_adapter.py
```

## 🔄 実装計画

### ✅ Phase 1: helpers.pyの分割（完了）
1. **新ファイル作成** ✅
   - `string_formatters.py` - 文字列・テンプレート処理
   - `docker_wrappers.py` - Docker関連のラッパー関数
   - `data_processors.py` - リスト・辞書処理

2. **既存コードの移動** ✅
   - 各関数を適切なファイルに移動
   - インポート文の更新

3. **テストの更新** ✅
   - 新しいファイル構造に対応

4. **後方互換性の確保** ✅
   - `helpers.py`に deprecation warning付きの再エクスポート
   - 段階的な移行を可能にする

### ✅ Phase 2: core.pyのリネーム（完了）
1. **ファイル名変更** ✅
   - `core.py` → `step_generation_service.py`

2. **インポート文の更新** ✅
   - プロジェクト全体での参照更新（4ファイル）

### ✅ Phase 3: BaseDriverの改善（完了）
1. **クラス名変更** ✅
   - `BaseDriver` → `ExecutionDriverInterface`

2. **メソッド名の具体化** ✅
   - `execute()` → `execute_command()`

3. **継承関係の更新** ✅
   - 全ドライバークラスで継承・実装を更新

### 🔄 Phase 4: 残りの関数名の具体化（進行中）
1. **部分的に完了**
   - `FileDriver.create()` → `create_file()`
   - `DockerDriver.build()` → `build_docker_image()`

2. **残り作業**
   - その他の抽象的な関数名（低優先度）
   - リポジトリクラスの`create`メソッド

## 📊 影響範囲の分析

### helpers.py分割の影響
- **直接的影響:** 2ファイル（テストファイル）
- **間接的影響:** 低（純粋関数のため）
- **リスク:** 低

### core.py リネームの影響
- **直接的影響:** 中（複数ファイルからインポート）
- **間接的影響:** 中
- **リスク:** 中

### 関数名変更の影響  
- **直接的影響:** 高（多数のファイルで使用）
- **間接的影響:** 高
- **リスク:** 中

## 🎯 成功指標

1. **可読性の向上**
   - ファイル名から機能が予想可能
   - 関数名から動作が明確

2. **保守性の向上**
   - 責務の明確な分離
   - 変更影響範囲の局所化

3. **新規開発者の理解速度向上**
   - 直感的な命名による学習コスト削減

## 📝 実装ガイドライン

### 命名規則
- **ファイル名**: 15-25文字、機能を具体的に表現
- **クラス名**: 責務を明確に示す（Interface, Service, Builder等の接尾辞活用）
- **メソッド名**: 動詞+目的語で具体性を確保
- **変数名**: 省略形は一般的なもののみ許可

### 後方互換性の確保
- 段階的な移行期間の設定
- Deprecation warningの追加
- 移行ガイドの作成

この改善により、プロジェクト全体の可読性と保守性が大幅に向上し、新規開発者の参入障壁も下がることが期待されます。