# プロジェクト全体インポート関係分析レポート

## 📊 分析概要

### 基本統計
- **総モジュール数**: 132
- **現在のレイヤー数**: 11 (0-10)
- **循環依存数**: 1つ（2モジュール間）
- **アーキテクチャ違反**: 7件（重大な問題）
- **高結合モジュール**: 4つ

### レイヤー分布
```
Layer 0:  77 modules (基盤モジュール)
Layer 1:  16 modules 
Layer 2:  14 modules
Layer 3:  6 modules
Layer 4:  6 modules
Layer 5:  2 modules
Layer 6:  2 modules
Layer 7:  3 modules
Layer 8:  2 modules
Layer 9:  1 module
Layer 10: 1 module (main)
Cyclic:   2 modules (循環依存)
```

## 🔄 循環依存の詳細

### 発見された循環依存
1. **domain.requests.composite内の循環**
   - `src.domain.requests.composite.composite_request`
   - `src.domain.requests.composite.composite_structure`
   
   **影響**: ドメインレイヤーの不安定性、テストの困難性
   **推奨**: クラスの統合またはインターフェース分離

## ⚠️ 重大なアーキテクチャ違反

### 1. shared.utils → application 依存
```
src.shared.utils.unified_formatter
  ↓
src.application.formatters.format_manager
src.application.formatters.base.base_format_engine
```
**問題**: 共有ユーティリティがアプリケーション層に依存
**影響**: レイヤー逆転、再利用性の低下

### 2. domain → application 依存
```
src.domain.requests.file.file_request → src.application.orchestration.unified_driver
src.domain.requests.composite.composite_request → src.application.orchestration.output_manager
src.domain.requests.shell.shell_request → src.application.orchestration.unified_driver
```
**問題**: ドメインがアプリケーション層に依存
**影響**: Clean Architectureの違反、テスタビリティの低下

### 3. domain → infrastructure 依存
```
src.domain.requests.docker.docker_request → src.infrastructure.drivers.docker.docker_driver
```
**問題**: ドメインがインフラストラクチャに直接依存
**影響**: 依存性逆転原則の違反、柔軟性の欠如

## 📂 モジュール群別分析

### shared.utils (13 modules)
- **レイヤー分布**: Layer 0: 11, Layer 1: 1, Layer 4: 1
- **問題**: `unified_formatter`がapplication層に依存
- **推奨**: `unified_formatter`をapplication層に移動

### application.formatters (5 modules)  
- **レイヤー分布**: Layer 0: 2, Layer 2: 1, Layer 3: 1, Layer 4: 1
- **状態**: 比較的良好な構造
- **注意**: context.utils.format_utilsからの依存あり

### context (17 modules)
- **レイヤー分布**: Layer 0: 8, Layer 1: 3, Layer 2: 1, Layer 3: 2, Layer 4: 2, Layer 6: 1
- **結合度**: `execution_context` (7依存), `user_input_parser` (7依存)
- **推奨**: アプリケーション層への依存を削減

### infrastructure (36 modules)
- **レイヤー分布**: Layer 0: 20, Layer 1: 5, Layer 2: 7, Layer 3: 1, Layer 4: 1, Layer 7: 1, Layer 8: 1
- **高結合**: `di_config` (17依存)
- **推奨**: 設定モジュールの分割

### domain (26 modules)
- **レイヤー分布**: Layer 0: 15, Layer 1: 4, Layer 2: 4, Layer 4: 1, Cyclic: 2
- **重大問題**: applicationとinfrastructureへの依存
- **推奨**: 依存性逆転原則の適用

## 🎯 理想的なレイヤー構造提案

### Level 0 - Foundation
- **モジュール**: `domain.constants`, `domain.types`, `shared.exceptions`, `utils`
- **原則**: 他に依存しない、純粋関数中心

### Level 1 - Domain Core  
- **モジュール**: `domain.results`, `domain.requests.base`, `shared.utils.basic_formatter`
- **原則**: ビジネスロジックのみ、インフラに依存しない

### Level 2 - Domain Extensions
- **モジュール**: `domain.requests.*`, `shared.utils.{docker,shell,python}`
- **原則**: ドメイン知識の具体化

### Level 3 - Domain Orchestration
- **モジュール**: `domain.requests.composite`, `env_core.step`, `env_core.workflow`
- **原則**: ドメインオブジェクトの組み合わせ

### Level 4 - Application Services
- **モジュール**: `application.formatters`, `pure_functions`
- **原則**: UI/表示ロジック、ドメインの表現変換

### Level 5 - Application Orchestration
- **モジュール**: `application.orchestration`, `application.factories`
- **原則**: ドメインとインフラの調整

### Level 6-8 - Infrastructure Layers
- **Level 6**: インフラ抽象化 (`drivers.base`)
- **Level 7**: 具体実装 (`drivers.*`, `persistence`)
- **Level 8**: 高レベルサービス (`config`, `environment`)

### Level 9 - Context & Integration
- **モジュール**: `context`, `env_integration`
- **原則**: 実行コンテキスト、環境適応

### Level 10 - Entry Points
- **モジュール**: `main`, `workflow_execution_service`
- **原則**: 全体調整、外部インターフェース

## 📋 段階的改善計画

### Phase 1: Critical Architecture Fixes (1-2週間)
1. **unified_formatter移動**
   - `src/shared/utils/unified_formatter.py` → `src/application/formatters/unified_formatter.py`
   - 後方互換性のためのラッパー作成

2. **domain→application依存除去**
   - OutputManager, ExecutionControllerのインターフェース作成
   - 依存性注入パターンの適用

### Phase 2: Domain-Infrastructure Separation (2-3週間)
1. **インフラインターフェース作成**
   - ドライバーインターフェースをdomain層に定義
   - 依存性注入の実装

2. **循環依存修正**
   - composite_request と composite_structure の関係見直し
   - クラス統合または責務分離

### Phase 3: Layer Optimization (1-2週間)
1. **di_config分割**
   - 設定モジュールの細分化
   - ファクトリーパターンの適用

2. **context層最適化**
   - 不要な跨層依存の除去
   - 実行環境に集中

### Phase 4: Documentation & Validation (1週間)
1. **アーキテクチャ文書化**
   - レイヤー責務の明文化
   - 依存ルールの策定

2. **継続監視実装**
   - pre-commitフックでの依存チェック
   - CI/CDでのアーキテクチャ検証

## 🎯 成功指標

| 指標 | 現在 | 目標 |
|------|------|------|
| アーキテクチャ違反 | 7件 | 0件 |
| 循環依存 | 1件 | 0件 |
| 最大レイヤー深度 | 10 | 10以下 |
| 高結合モジュール (>8依存) | 4つ | 3つ以下 |

## 🛠️ 実装パターン推奨

### 1. 依存性逆転原則
```python
# Before: Domain → Infrastructure
class DockerRequest:
    def __init__(self):
        self.driver = DockerDriver()  # 直接依存

# After: Domain ← Infrastructure  
class DockerRequest:
    def __init__(self, driver: DockerDriverInterface):
        self.driver = driver  # インターフェース依存
```

### 2. オブザーバーパターン
```python
# Domain発のイベントをApplication層で受信
class RequestExecuted(DomainEvent):
    pass

# Application層でイベント処理
class OutputManagerEventHandler:
    def handle(self, event: RequestExecuted):
        # 出力処理
```

### 3. ファクトリーパターン
```python
# 複雑な依存関係を持つオブジェクトの生成
class RequestFactory:
    def create_docker_request(self, config: Config) -> DockerRequest:
        driver = self.driver_factory.create_docker_driver(config)
        return DockerRequest(driver)
```

## 📁 分析ファイル一覧

生成されたファイル:
- `import_analysis_report.json` - 基本分析結果
- `enhanced_import_analysis.json` - 強化分析結果  
- `detailed_dependency_report.json` - 詳細依存関係分析
- `architectural_recommendations.json` - 改善提案詳細

分析ツール:
- `analyze_imports.py` - 基本インポート分析
- `enhanced_import_analyzer.py` - 強化分析ツール
- `detailed_dependency_analyzer.py` - 詳細依存関係分析
- `architectural_recommendations.py` - 改善提案生成

---

**レポート作成日**: 2025-01-07  
**分析対象**: `/home/cphelper/project-cph/src` (132 modules)  
**分析ツール**: カスタムPython分析スクリプト群