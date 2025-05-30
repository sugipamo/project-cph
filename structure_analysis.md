# ファイル構造評価と改善提案

## 🔍 現在の構造分析

### ディレクトリ構造の問題点

#### 1. **混在する責務**
```
src/
├── context/          # 設定・コンテキスト関連
├── env/             # 環境・ワークフロー関連 (巨大)
├── operations/      # 低レベル操作 (巨大)
└── main.py         # エントリーポイント
```

**問題**:
- `env/`と`operations/`が巨大すぎる
- ビジネスロジックと技術的詳細が混在
- レイヤー間の依存関係が不明確

#### 2. **曖昧な命名**
```
src/env/                     # "environment"の略？不明確
src/operations/mock/         # テスト関連がsrcに混在
src/context/utils/          # ユーティリティが散在
src/operations/utils/       # ↑重複
```

#### 3. **Factory パターンの乱用**
```
src/env/factory/            # 17個のファクトリークラス
├── base_command_request_factory.py
├── build_command_request_factory.py
├── copy_command_request_factory.py
├── docker_command_request_factory.py
├── mkdir_command_request_factory.py
├── move_command_request_factory.py
├── movetree_command_request_factory.py
├── oj_command_request_factory.py
├── python_command_request_factory.py
├── remove_command_request_factory.py
├── rmtree_command_request_factory.py
├── shell_command_request_factory.py
├── touch_command_request_factory.py
└── ...
```

**問題**:
- 類似機能のファクトリーが分散
- 保守コストが高い
- 本質的に同じ処理の重複

## 📋 命名規則の問題

### クラス名の問題
```python
# 冗長すぎる名前
class BaseCommandRequestFactory           # → CommandFactory
class BuildCommandRequestFactory          # → BuildFactory
class CopyCommandRequestFactory           # → CopyFactory

# 意味が不明確
class EnvResourceController              # → ResourceManager
class EnvWorkflowService                 # → WorkflowRunner

# 省略語の不統一
class DockerUtil                         # Utils vs Util
class ProcessUtil                        # Utils vs Util
class PathUtil                          # ↑不統一
```

### 関数名の問題
```python
# 動詞が不明確
def format_string()                      # → format_template()
def create_request_from_node()           # → build_request()

# 長すぎる名前
def validate_step_configuration_pure()   # → validate_step()
def build_docker_run_command_pure()      # → docker_run_cmd()
```

## 🎯 改善提案

### 1. **ドメイン駆動設計による再構成**

#### 推奨構造:
```
src/
├── core/                    # コアドメイン
│   ├── models/             # ドメインモデル
│   │   ├── contest.py      # Contest, Problem
│   │   ├── execution.py    # Execution, Result
│   │   └── step.py         # Step, Command
│   ├── services/           # ドメインサービス
│   │   ├── workflow.py     # ワークフロー実行
│   │   ├── evaluation.py   # テスト実行・評価
│   │   └── submission.py   # 提出処理
│   └── repositories/       # データアクセス
│       ├── config.py       # 設定の永続化
│       └── contest.py      # コンテストデータ
├── infrastructure/         # インフラストラクチャ層
│   ├── docker/            # Docker操作
│   ├── filesystem/        # ファイル操作
│   ├── shell/            # シェル実行
│   └── networking/       # ネットワーク操作
├── application/           # アプリケーション層
│   ├── commands/         # コマンドハンドラ
│   ├── queries/          # クエリハンドラ
│   └── workflows/        # ワークフローオーケストレーション
├── adapters/             # アダプター層
│   ├── cli/              # CLI インターフェース
│   ├── parsers/          # 入力解析
│   └── formatters/       # 出力フォーマット
└── utils/                # 共通ユーティリティ
    ├── functional.py     # 純粋関数
    ├── validation.py     # バリデーション
    └── helpers.py        # ヘルパー関数
```

### 2. **命名規則の統一**

#### クラス名規則:
```python
# Before → After
BaseCommandRequestFactory    → CommandFactory
DockerCommandRequestFactory → DockerFactory
EnvResourceController      → ResourceManager
EnvWorkflowService         → WorkflowExecutor
MockFileDriver            → FileDriverMock
DummyFileDriver           → FileDriverStub
```

#### ファイル名規則:
```python
# Before → After
docker_command_request_factory.py → docker_factory.py
base_command_request_factory.py   → command_factory.py
env_workflow_service.py           → workflow_executor.py
user_input_parser.py              → input_parser.py
```

### 3. **Factory統合による簡略化**

#### 現在（17個のFactory）→ 提案（3個のFactory）:
```python
# 統合前: 17個の類似Factory
BaseCommandRequestFactory
BuildCommandRequestFactory
CopyCommandRequestFactory
DockerCommandRequestFactory
# ... 13個以上

# 統合後: 3個の責務別Factory
class CommandFactory:          # コマンド生成
    def create_shell_command()
    def create_python_command()
    def create_build_command()

class OperationFactory:        # 操作生成
    def create_file_operation()
    def create_docker_operation()

class WorkflowFactory:         # ワークフロー生成
    def create_workflow()
    def create_step_sequence()
```

### 4. **テストファイルの整理**

#### 現在の問題:
```
tests/
├── env/                    # 分散しすぎ
├── env_workflow_service/   # ↑重複
├── execution_context/      # ↑分散
├── factory/               # ↑分散
├── resource/              # ↑分散
└── unit/                  # ユニットテストが別途
```

#### 提案:
```
tests/
├── unit/                  # ユニットテスト
│   ├── core/             # コアドメインのテスト
│   ├── infrastructure/   # インフラのテスト
│   └── utils/           # ユーティリティのテスト
├── integration/          # 統合テスト
│   ├── workflows/       # ワークフローテスト
│   └── end_to_end/      # E2Eテスト
└── fixtures/            # テストデータ
    ├── configs/         # 設定ファイル
    └── samples/         # サンプルデータ
```

## 🚀 移行戦略

### Phase 1: ユーティリティの統合
1. `src/context/utils/` と `src/operations/utils/` を `src/utils/` に統合
2. 純粋関数を `src/utils/functional.py` に集約
3. 重複するユーティリティクラスを統合

### Phase 2: Factory の簡略化
1. 17個のFactoryクラスを3個に統合
2. 共通ロジックを基底クラスに抽出
3. 不要なファクトリーパターンを削除

### Phase 3: ドメインモデルの抽出
1. `src/core/models/` を作成
2. ビジネスロジックをドメインサービスに移動
3. データアクセスをリポジトリパターンに分離

### Phase 4: レイヤー分離
1. インフラストラクチャ層の明確化
2. アプリケーション層の作成
3. 依存関係の逆転適用

## 📊 改善効果予測

### コード量削減:
- Factory統合: **70%削減** (17個 → 3個)
- 重複コード: **40%削減**
- テストファイル: **30%削減**

### 保守性向上:
- 機能発見時間: **50%短縮**
- 新機能追加時間: **30%短縮**
- バグ修正時間: **40%短縮**

### 品質向上:
- 依存関係の明確化
- テスタビリティの向上
- コードの再利用性向上