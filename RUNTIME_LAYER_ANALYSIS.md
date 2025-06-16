# runtimeレイヤーの性質分析

## 分析結果

### 1. runtimeレイヤーの実態

詳細調査の結果、現在の「runtimeレイヤー」は**設定システムの一部ではなく、実行時状態管理と永続化の責務**を担っていることが判明しました。

### 2. 混在している責務の詳細

#### 2.1 SQLiteベースの動的管理（実行時状態）
- **場所**: `src/infrastructure/persistence/sqlite/`
- **責務**: 
  - 実行履歴の記録（operations）
  - セッション管理（sessions）
  - Docker資源追跡（docker_containers, docker_images）
  - **実行時コンテキストの保存**（system_config内の一部）

#### 2.2 実行設定の動的構築（実行時処理）
- **場所**: `src/configuration/core/runtime_config.py`
- **責務**: 実行時に動的に決定される設定値の保持
  ```python
  @dataclass(frozen=True)
  class RuntimeConfig:
      language_id: str
      source_file_name: str
      run_command: str
      timeout_seconds: int
      retry_settings: Dict[str, Any]
  ```

#### 2.3 実行時引数解析（実行時処理）
- **場所**: `src/context/user_input_parser.py`
- **責務**: コマンドライン引数から実行時設定を動的に構築

### 3. 4層（system, shared, language, runtime）の性質の違い

| レイヤー | 性質 | データソース | 変更頻度 | 責務 |
|---------|------|-------------|----------|------|
| **system** | 静的設定 | JSONファイル | 低（開発時のみ） | システム定数、制約 |
| **shared** | 静的設定 | JSONファイル | 低（環境構築時） | 共通設定、デフォルト値 |
| **language** | 静的設定 | JSONファイル | 中（言語固有調整） | 言語固有設定 |
| **runtime** | **動的状態** | **SQLite + 引数解析** | **高（実行毎）** | **実行時状態管理** |

### 4. system_configテーブルの性質分析

現在のsystem_configテーブルは2つの異なる責務を混在させています：

#### 4.1 設定データ（本来の責務）
```sql
-- 言語固有設定や環境設定
config_key: env_json
category: environment
```

#### 4.2 実行時状態データ（設定ではない）
```sql
-- 前回実行のコンテキスト情報
config_key: command, language, env_type, contest_name, problem_name
category: NULL（実行時状態として）
```

### 5. SystemConfigRepositoryの実際の役割

`SystemConfigRepository`は名前に反して、実際には：
- **設定の永続化** + **実行時状態の永続化** を同時に担当
- 汎用的なkey-valueストレージとして機能
- 本来の「設定リポジトリ」の責務を超えている

### 6. ExecutionConfiguration vs RuntimeConfigの違い

#### ExecutionConfiguration（統合設定）
```python
@dataclass(frozen=True)
class ExecutionConfiguration:
    # 基本情報（実行時に決定）
    contest_name: str
    problem_name: str
    language: str
    
    # 設定情報（静的 + 動的）
    paths: ExecutionPaths
    runtime_config: RuntimeConfig
    output_config: OutputConfig
```

#### RuntimeConfig（実行時決定設定）
```python
@dataclass(frozen=True)
class RuntimeConfig:
    # 実行時に動的に決定される値
    language_id: str
    source_file_name: str
    run_command: str
```

### 7. 境界線の問題

現在の実装では以下の境界があいまい：
- **設定** vs **実行時状態**
- **永続化すべき設定** vs **一時的な実行コンテキスト**
- **静的な設定値** vs **動的に生成される値**

### 8. 結論と推奨事項

#### 8.1 runtimeレイヤーの正体
runtimeレイヤーは**設定システムの一部ではなく**、以下の2つの異なる関心事を担当：
1. **実行時状態管理** - 前回実行情報の保存・復元
2. **動的設定構築** - 引数解析による実行時設定の生成

#### 8.2 分離すべき責務
```
現在のruntimeレイヤー
├── 実行時状態管理 → StateManagement層
│   ├── 前回実行情報の保存
│   ├── セッション管理
│   └── Docker資源追跡
└── 動的設定構築 → Configuration層
    ├── 引数解析
    ├── 設定値の動的決定
    └── ExecutionConfigurationの構築
```

#### 8.3 アーキテクチャ改善案
1. **設定システム**: 3層（system, shared, language）に純化
2. **状態管理システム**: 実行履歴・セッション・前回値の管理
3. **実行時処理**: 引数解析と動的設定構築

これにより、各システムの責務が明確になり、保守性が向上します。