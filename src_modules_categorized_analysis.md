# Project CPH - モジュール機能重複分析・カテゴリ分類

## 概要
このドキュメントでは、srcディレクトリ内のモジュールを機能別にカテゴリ分類し、重複している機能や統合可能な機能を分析します。

---

## 🚨 機能重複の分析

### 重複度: 高（即座に統合検討が必要）

#### 1. **フォーマット機能の重複**
- **重複箇所**:
  - `application/formatters/` (FormatManager, PythonFormatEngine, BaseFormatEngine)
  - `context/utils/format_utils.py` (format_with_missing_keys, extract_format_keys)
  - `pure_functions/execution_context_formatter_pure.py` (format_template_string)
  - `shared/utils/pure_functions.py` (format_string_pure)

- **問題点**:
  - 4箇所で同様のテンプレート文字列フォーマット機能を提供
  - APIの不統一（一部は`{key}`形式、一部は他の形式もサポート）
  - パフォーマンスの最適化が分散している

- **統合案**:
  1. `application/formatters/format_manager.py`を中心に統一
  2. 他の場所は薄いラッパーとして実装
  3. 純粋関数は`shared/utils/pure_functions.py`に集約

#### 2. **Docker操作の重複**
- **重複箇所**:
  - `infrastructure/drivers/docker/docker_driver.py` (LocalDockerDriver)
  - `infrastructure/mock/mock_docker_driver.py` (MockDockerDriver)
  - `shared/utils/pure_functions.py` (build_docker_*_command_pure関数群)

- **問題点**:
  - Dockerコマンド構築ロジックが分散
  - 実装ドライバーとモックドライバーで微妙にAPIが異なる
  - pure_functionsにDocker固有のロジックが混在

- **統合案**:
  1. `shared/utils/docker/`にDocker関連の純粋関数を集約
  2. ドライバー間でのAPI統一
  3. コマンド構築ロジックの共通化

### 重複度: 中（将来的に統合検討）

#### 3. **出力管理の分散**
- **分散箇所**:
  - `application/orchestration/output_manager.py`
  - `pure_functions/output_manager_formatter_pure.py`
  - 各ドライバーでのshow_outputパラメータ処理

- **問題点**:
  - 出力制御のロジックが分散
  - 一貫性のない出力フォーマット

#### 4. **実行コンテキストの複数管理**
- **分散箇所**:
  - `context/execution_context.py` (ExecutionContext)
  - `pure_functions/execution_context_formatter_pure.py` (ExecutionFormatData)
  - `env_core/step/step.py` (StepContext)

- **問題点**:
  - 類似のコンテキスト情報を異なるデータ構造で管理
  - 変換処理のオーバーヘッド

---

## 📂 機能別カテゴリ分類

### 1. **Core Domain (コアドメイン)** ⭐
```
domain/
├── constants/operation_type.py        # 操作タイプ定義
├── requests/                          # リクエストオブジェクト
│   ├── base/base_request.py          # 基底リクエスト
│   ├── composite/, docker/, file/, python/, shell/
├── results/                          # 実行結果
└── types/execution_types.py          # 実行型定義
```
**責務**: ビジネスロジックの中核、型安全性の確保

### 2. **Infrastructure (インフラストラクチャ)** 🔧
```
infrastructure/
├── di_container.py                   # 依存性注入
├── drivers/                          # 実行ドライバー
│   ├── base/base_driver.py
│   ├── docker/, file/, python/, shell/
├── mock/                             # テスト用モック
└── persistence/                      # データ永続化
```
**責務**: 外部システムとの統合、依存性管理

### 3. **Application Services (アプリケーションサービス)** 🎯
```
application/
├── factories/unified_request_factory.py  # リクエスト生成
├── formatters/                           # フォーマット処理
├── orchestration/                        # 実行制御
│   ├── unified_driver.py                # 統一ドライバー
│   ├── execution_controller.py
│   └── output_manager.py
```
**責務**: ユースケースの実装、ドメインの協調

### 4. **Context Management (コンテキスト管理)** 📋
```
context/
├── execution_context.py             # 実行コンテキスト
├── execution_data.py                # データ管理
├── user_input_parser.py             # 入力解析
├── resolver/                        # 設定解決
└── utils/format_utils.py            # フォーマットユーティリティ
```
**責務**: 実行環境の管理、設定の解決

### 5. **Workflow Engine (ワークフローエンジン)** ⚙️
```
env_core/
├── step/                            # ステップ管理
│   ├── core.py, dependency.py, step.py, workflow.py
└── workflow/                        # ワークフロー構築
    ├── graph_based_workflow_builder.py
    └── request_execution_graph.py

env_integration/fitting/             # 環境統合
```
**責務**: 依存関係解決、並列実行、グラフベース最適化

### 6. **Pure Functions (純粋関数)** 🧮
```
pure_functions/
├── execution_context_formatter_pure.py
├── graph_builder_pure.py
├── output_manager_formatter_pure.py
shared/utils/pure_functions.py
```
**責務**: 副作用のない計算、テスタビリティ向上

### 7. **Legacy/Unused (レガシー・未使用)** ⚠️
```
executor/                            # 大量の空ディレクトリ
├── constants/, drivers/, exceptions/, formatters/
├── mock/, orchestration/, persistence/, requests/
├── results/, types/, utils/
└── (各カテゴリが空またはほぼ空)
```
**問題**: 180個のディレクトリの大部分が空で、メンテナンス負荷が高い

### 8. **Shared Utilities (共有ユーティリティ)** 🛠️
```
shared/
├── exceptions/composite_step_failure.py
└── utils/
    ├── pure_functions.py           # 汎用純粋関数
    ├── docker/, python/, shell/   # 特化ユーティリティ

utils/
├── debug_logger.py                 # デバッグ機能
└── path_operations.py              # パス操作
```

---

## 🎯 統合・整理の優先度

### 🔴 **HIGH**: 即座に対応すべき重複
1. **フォーマット機能の統一**: `application/formatters/`中心の統合
2. **executorディレクトリの整理**: 空ディレクトリの削除
3. **Docker操作の統合**: `shared/utils/docker/`への集約

### 🟡 **MEDIUM**: 次期リファクタリングで対応
1. **出力管理の統一**: OutputManagerの責務明確化
2. **コンテキスト管理の最適化**: ExecutionContext系の統合
3. **pure_functionsの整理**: 機能別モジュール分割

### 🟢 **LOW**: 長期的な改善
1. **型定義の統一**: domain/types/の拡充
2. **テストモックの標準化**: infrastructure/mock/の整理

---

## 📊 統計情報

- **総ディレクトリ数**: 180個
- **空ディレクトリ数**: 約140個 (78%)
- **重複機能箇所**: 4つの主要領域
- **コアモジュール**: 約40個
- **整理対象**: executor/配下の大部分

---

## 🚀 推奨アクション

1. **即座に実行**:
   - `executor/`内の空ディレクトリ削除
   - フォーマット機能の`application/formatters/`への統合

2. **短期目標** (1-2週間):
   - Docker操作の`shared/utils/docker/`への移動
   - 重複APIの統一

3. **中期目標** (1-2ヶ月):
   - Context管理の最適化
   - pure_functionsの機能別分割

この整理により、メンテナンス性の向上とコードの重複削減が期待できます。