# コード品質チェックツール 論理モデル設計書

## 1. 現在のプロジェクト構造分析

### 1.1 プロジェクト全体アーキテクチャ

```
project-cph/
├── src/                          # メインアプリケーション（クリーンアーキテクチャ）
│   ├── cli/                      # CLI インターフェース層
│   ├── configuration/            # 設定管理
│   ├── context/                  # コンテキスト処理
│   ├── infrastructure/           # インフラストラクチャ層
│   ├── operations/               # オペレーション層（ドメインロジック）
│   └── workflow/                 # ワークフロー管理
├── scripts/                      # 品質チェック・メンテナンスツール群
│   ├── quality_checks/           # 品質チェッカー実装
│   ├── quality/                  # 実用的品質ツール
│   ├── code_analysis/            # コード分析ツール
│   ├── analysis/                 # アーキテクチャ分析
│   └── infrastructure/           # スクリプト専用インフラ
├── config/                       # システム設定ファイル群
├── tests/                        # テストスイート
└── contest_template/             # コンテスト用テンプレート
```

### 1.2 現在の品質チェックツール構造

```
scripts/
├── quality_checks/              # 規約準拠チェッカー群
│   ├── base/                    # 共通基底クラス
│   │   ├── base_quality_checker.py      # 基底抽象クラス
│   │   ├── quality_config_loader.py     # 設定読み込み
│   │   └── progress_spinner.py          # 進捗表示
│   ├── none_default_checker.py          # デフォルト値禁止
│   ├── dependency_injection_checker.py  # 依存性注入
│   ├── fallback_checker.py              # フォールバック禁止
│   ├── clean_architecture_checker.py    # アーキテクチャ準拠
│   └── [その他12個のチェッカー]
├── quality/                     # 実用的品質ツール
│   ├── practical_quality_check.py       # 実用品質チェック
│   ├── check_generic_names.py          # 汎用名検出
│   └── quality_utils.py                # 共通機能
├── code_analysis/               # コード分析
│   ├── dead_code_checker.py            # 未使用コード検出
│   └── import_checker.py               # インポート検証
├── analysis/                    # アーキテクチャ分析
│   └── analyze_architecture.py         # Martin's Metrics
└── configuration/               # 設定管理
    └── quality_checks.json             # 統一設定
```

## 2. 論理モデル設計

### 2.1 機能単位の責務分離

#### 2.1.1 コア責務レイヤー

```
検出層 (Detection Layer)
├── 構文解析エンジン (Syntax Analysis Engine)
│   ├── AST解析器
│   ├── 正規表現マッチャー
│   └── 構造分析器
├── ルール実行エンジン (Rule Execution Engine)
│   ├── ルールセット管理
│   ├── 検証実行器
│   └── 結果集約器
└── パターン検出器 (Pattern Detector)
    ├── コード違反検出
    ├── 構造的問題検出
    └── 依存関係検出

診断層 (Diagnostic Layer)
├── 違反分類器 (Violation Classifier)
│   ├── エラー重要度判定
│   ├── カテゴリ分類
│   └── 影響範囲分析
├── 修正提案エンジン (Fix Suggestion Engine)
│   ├── 自動修正候補生成
│   ├── 手動修正指針提示
│   └── リファクタリング提案
└── レポート生成器 (Report Generator)
    ├── 構造化レポート出力
    ├── 修正優先度付け
    └── 進捗追跡情報

設定管理層 (Configuration Layer)
├── ルール定義管理 (Rule Definition Manager)
│   ├── 検出ルール設定
│   ├── 除外ルール管理
│   └── カスタムルール登録
├── 対象ファイル管理 (Target File Manager)
│   ├── スキャン対象制御
│   ├── 除外パターン管理
│   └── ファイル分類
└── 拡張ポイント管理 (Extension Point Manager)
    ├── プラグイン登録
    ├── カスタムチェッカー管理
    └── 外部ツール統合
```

#### 2.1.2 機能別モジュール責務

**1. 検出ルール管理モジュール (Rule Management Module)**
- 責務: 検出ルールの定義、登録、管理
- 機能: JSON/YAML設定からのルール読み込み、動的ルール追加、ルール有効化制御
- 拡張ポイント: カスタムルール型の追加、外部ルールセット統合

**2. パターンマッチングモジュール (Pattern Matching Module)**
- 責務: 正規表現・AST・構造的パターンによる違反検出
- 機能: 複数パターン同時検索、コンテキスト考慮マッチング、性能最適化
- 拡張ポイント: 新パターン型追加、マッチング戦略カスタマイズ

**3. 診断・修正提案モジュール (Diagnosis & Fix Suggestion Module)**
- 責務: 検出された違反の分析と修正方針の生成
- 機能: 違反コンテキスト分析、自動修正コード生成、修正手順提示
- 拡張ポイント: カスタム修正ロジック、ドメイン固有修正パターン

**4. レポーティングモジュール (Reporting Module)**
- 責務: 検出結果の整理・出力・可視化
- 機能: 多形式出力（JSON/HTML/テキスト）、統計情報生成、進捗追跡
- 拡張ポイント: カスタム出力形式、外部システム連携

### 2.2 検査ルールの定義方法

#### 2.2.1 統一ルール定義スキーマ

```json
{
  "rule_id": "unique_rule_identifier",
  "rule_name": "表示用ルール名",
  "category": "violation_category",
  "severity": "error|warning|info",
  "enabled": true,
  "detection": {
    "type": "regex|ast|structural|composite",
    "patterns": [
      {
        "pattern": "検出パターン",
        "context": "適用コンテキスト制約",
        "exclusions": ["除外パターン"]
      }
    ],
    "scope": {
      "file_types": [".py"],
      "directories": ["src/", "scripts/"],
      "exclude_paths": ["tests/", "migrations/"]
    }
  },
  "diagnosis": {
    "violation_message": "違反内容の説明",
    "fix_suggestion": {
      "auto_fixable": boolean,
      "fix_template": "自動修正テンプレート",
      "manual_steps": ["手動修正手順"],
      "examples": {
        "before": "修正前コード例",
        "after": "修正後コード例"
      }
    },
    "related_rules": ["関連ルールID"],
    "documentation_url": "詳細ドキュメントURL"
  },
  "metadata": {
    "created_by": "作成者",
    "created_date": "作成日",
    "last_updated": "最終更新日",
    "version": "ルールバージョン"
  }
}
```

#### 2.2.2 ルール種別とパターン定義

**1. 正規表現ベースルール (Regex-based Rules)**
```json
{
  "type": "regex",
  "patterns": [
    {
      "pattern": "def\\s+(\\w+)\\s*\\([^)]*=\\s*None",
      "context": "function_definition",
      "violation_capture_group": 1
    }
  ]
}
```

**2. AST構造ベースルール (AST-based Rules)**
```json
{
  "type": "ast",
  "patterns": [
    {
      "node_type": "FunctionDef",
      "conditions": [
        {
          "path": "args.defaults",
          "operator": "length_gt",
          "value": 0
        }
      ]
    }
  ]
}
```

**3. 構造的依存関係ルール (Structural Rules)**
```json
{
  "type": "structural",
  "patterns": [
    {
      "violation_type": "circular_import",
      "detection_scope": "module_level",
      "analysis_depth": 3
    }
  ]
}
```

**4. 複合ルール (Composite Rules)**
```json
{
  "type": "composite",
  "logic": "AND",
  "sub_rules": [
    {"rule_ref": "direct_import_check"},
    {"rule_ref": "layer_violation_check"}
  ]
}
```

### 2.3 拡張ポイント設計

#### 2.3.1 プラグインアーキテクチャ

```python
# 拡張インターfaces
class QualityRulePlugin(Protocol):
    def get_rule_definitions(self) -> List[RuleDefinition]:
        """カスタムルール定義を返す"""
        
    def detect_violations(self, 
                         code: str, 
                         context: AnalysisContext) -> List[Violation]:
        """違反検出を実行"""
        
    def suggest_fixes(self, 
                     violation: Violation, 
                     context: AnalysisContext) -> List[FixSuggestion]:
        """修正提案を生成"""

class PatternMatcherPlugin(Protocol):
    def supports_pattern_type(self, pattern_type: str) -> bool:
        """対応パターン型を確認"""
        
    def match_pattern(self, 
                     pattern: Pattern, 
                     code: str, 
                     context: AnalysisContext) -> List[Match]:
        """パターンマッチングを実行"""

class ReporterPlugin(Protocol):
    def get_output_formats(self) -> List[str]:
        """対応出力形式を返す"""
        
    def generate_report(self, 
                       results: AnalysisResults, 
                       format: str) -> ReportOutput:
        """レポートを生成"""
```

#### 2.3.2 設定ベース拡張ポイント

**1. カスタムルールセット登録**
```json
{
  "custom_rule_sets": [
    {
      "name": "project_specific_rules",
      "source": "config/rules/project_rules.json",
      "enabled": true,
      "priority": 100
    }
  ]
}
```

**2. 外部ツール統合**
```json
{
  "external_tools": [
    {
      "name": "custom_linter",
      "command": "custom-lint",
      "args": ["--config", "custom.conf"],
      "output_parser": "parsers.custom_linter_parser",
      "enabled": true
    }
  ]
}
```

**3. 修正テンプレート拡張**
```json
{
  "fix_templates": [
    {
      "rule_id": "none_default_violation",
      "template_type": "regex_replace",
      "template": {
        "search": "def\\s+(\\w+)\\s*\\(([^)]*)=\\s*None([^)]*)",
        "replace": "def $1($2$3",
        "additional_steps": [
          "add_explicit_none_check_in_function_body"
        ]
      }
    }
  ]
}
```

## 3. 将来要件対応設計

### 3.1 正規表現ベース違反検出・修正提示

#### 3.1.1 検出エンジン設計

```python
class RegexViolationDetector:
    def __init__(self, rule_manager: RuleManager):
        self.rule_manager = rule_manager
        self.pattern_cache = {}
    
    def detect_violations(self, 
                         file_content: str, 
                         file_path: str) -> List[RegexViolation]:
        """正規表現ベースの違反検出"""
        violations = []
        applicable_rules = self.rule_manager.get_regex_rules(file_path)
        
        for rule in applicable_rules:
            matches = self._find_pattern_matches(file_content, rule)
            for match in matches:
                violation = RegexViolation(
                    rule_id=rule.id,
                    file_path=file_path,
                    line_number=self._get_line_number(file_content, match.start()),
                    matched_text=match.group(),
                    context=self._extract_context(file_content, match),
                    fix_suggestions=self._generate_fix_suggestions(rule, match)
                )
                violations.append(violation)
        
        return violations
```

#### 3.1.2 修正提案生成設計

```python
class FixSuggestionGenerator:
    def generate_suggestions(self, 
                           violation: RegexViolation) -> List[FixSuggestion]:
        """違反に対する修正提案を生成"""
        rule = self.rule_manager.get_rule(violation.rule_id)
        suggestions = []
        
        # 1. 自動修正候補
        if rule.fix_config.auto_fixable:
            auto_fix = self._generate_auto_fix(violation, rule)
            suggestions.append(auto_fix)
        
        # 2. 手動修正手順
        manual_steps = self._generate_manual_steps(violation, rule)
        suggestions.extend(manual_steps)
        
        # 3. コンテキスト考慮修正
        context_fixes = self._generate_context_aware_fixes(violation, rule)
        suggestions.extend(context_fixes)
        
        return suggestions

    def _generate_auto_fix(self, 
                          violation: RegexViolation, 
                          rule: Rule) -> AutoFixSuggestion:
        """自動修正コードを生成"""
        template = rule.fix_config.fix_template
        replacement = template.apply(violation.matched_text, violation.context)
        
        return AutoFixSuggestion(
            description="自動修正: " + rule.fix_config.description,
            original_code=violation.matched_text,
            fixed_code=replacement,
            confidence=rule.fix_config.confidence,
            side_effects=rule.fix_config.potential_side_effects
        )
```

### 3.2 構造的問題検出・対処法出力

#### 3.2.1 循環依存検出設計

```python
class CircularDependencyDetector:
    def __init__(self, project_analyzer: ProjectAnalyzer):
        self.project_analyzer = project_analyzer
        self.dependency_graph = DependencyGraph()
    
    def detect_circular_dependencies(self) -> List[CircularDependency]:
        """循環依存を検出"""
        self.dependency_graph.build_from_project(self.project_analyzer)
        cycles = self.dependency_graph.find_cycles()
        
        circular_deps = []
        for cycle in cycles:
            dependency = CircularDependency(
                cycle_path=cycle,
                severity=self._calculate_severity(cycle),
                breaking_strategies=self._generate_breaking_strategies(cycle),
                impact_analysis=self._analyze_impact(cycle)
            )
            circular_deps.append(dependency)
        
        return circular_deps
    
    def _generate_breaking_strategies(self, 
                                    cycle: List[Module]) -> List[BreakingStrategy]:
        """循環依存解決戦略を生成"""
        strategies = []
        
        # 1. 依存性逆転戦略
        inversion_points = self._identify_inversion_candidates(cycle)
        for point in inversion_points:
            strategy = DependencyInversionStrategy(
                target_dependency=point,
                interface_extraction=self._suggest_interface_extraction(point),
                implementation_reorganization=self._suggest_reorganization(point)
            )
            strategies.append(strategy)
        
        # 2. 中間レイヤー導入戦略
        mediation_opportunities = self._identify_mediation_opportunities(cycle)
        for opportunity in mediation_opportunities:
            strategy = MediationLayerStrategy(
                proposed_layer=opportunity.layer_name,
                moved_responsibilities=opportunity.responsibilities,
                new_interfaces=opportunity.interfaces
            )
            strategies.append(strategy)
        
        return strategies
```

#### 3.2.2 依存逆転検出設計

```python
class DependencyInversionDetector:
    def detect_violations(self) -> List[DependencyInversionViolation]:
        """依存逆転原則違反を検出"""
        violations = []
        
        for module in self.project_analyzer.get_all_modules():
            if self._is_high_level_module(module):
                low_level_deps = self._find_low_level_dependencies(module)
                for dep in low_level_deps:
                    violation = DependencyInversionViolation(
                        high_level_module=module,
                        low_level_dependency=dep,
                        violation_type=self._classify_violation_type(module, dep),
                        refactoring_suggestions=self._generate_refactoring_suggestions(module, dep)
                    )
                    violations.append(violation)
        
        return violations
    
    def _generate_refactoring_suggestions(self, 
                                        high_module: Module, 
                                        low_dep: Dependency) -> List[RefactoringSuggestion]:
        """リファクタリング提案を生成"""
        suggestions = []
        
        # 1. インターフェース抽出提案
        interface_suggestion = InterfaceExtractionSuggestion(
            target_dependency=low_dep,
            proposed_interface_name=self._suggest_interface_name(low_dep),
            extracted_methods=self._identify_interface_methods(low_dep),
            implementation_placement=self._suggest_implementation_placement(low_dep)
        )
        suggestions.append(interface_suggestion)
        
        # 2. 依存性注入提案
        injection_suggestion = DependencyInjectionSuggestion(
            injection_point=high_module,
            injected_interface=interface_suggestion.proposed_interface_name,
            injection_method=self._suggest_injection_method(high_module),
            configuration_changes=self._suggest_configuration_changes(high_module)
        )
        suggestions.append(injection_suggestion)
        
        return suggestions
```

### 3.3 設定ファイルによる柔軟な拡張・管理

#### 3.3.1 統合設定管理設計

```python
class QualityCheckConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_loader = ConfigLoader()
        self.rule_registry = RuleRegistry()
        self.validator = ConfigValidator()
    
    def load_configuration(self) -> QualityCheckConfig:
        """統合設定を読み込み"""
        base_config = self.config_loader.load_base_config(self.config_path)
        
        # カスタムルールセット読み込み
        for ruleset_config in base_config.custom_rulesets:
            custom_rules = self.config_loader.load_custom_ruleset(ruleset_config)
            self.rule_registry.register_rules(custom_rules)
        
        # 外部ツール設定読み込み
        external_tools = self._load_external_tool_configs(base_config)
        
        # 設定統合・検証
        integrated_config = QualityCheckConfig(
            base_rules=base_config.rules,
            custom_rules=self.rule_registry.get_all_rules(),
            external_tools=external_tools,
            execution_settings=base_config.execution,
            output_settings=base_config.output
        )
        
        self.validator.validate_config(integrated_config)
        return integrated_config
```

#### 3.3.2 動的ルール管理設計

```json
{
  "quality_check_config": {
    "version": "2.0",
    "rule_management": {
      "rule_sources": [
        {
          "type": "local_file",
          "path": "config/rules/base_rules.json",
          "priority": 100,
          "enabled": true
        },
        {
          "type": "remote_repository",
          "url": "https://rules.example.com/python-quality-rules",
          "branch": "main",
          "priority": 90,
          "enabled": false
        },
        {
          "type": "plugin",
          "plugin_name": "project_specific_rules",
          "plugin_path": "plugins/project_rules.py",
          "priority": 110,
          "enabled": true
        }
      ],
      "rule_overrides": [
        {
          "rule_id": "none_default_check",
          "severity": "error",
          "enabled": true,
          "custom_message": "プロジェクト方針によりデフォルト値使用を禁止"
        }
      ]
    },
    "execution_control": {
      "parallel_execution": true,
      "max_workers": 4,
      "timeout_per_file": 30,
      "memory_limit_mb": 1024
    },
    "output_management": {
      "formats": ["json", "html", "console"],
      "output_path": "reports/quality_check",
      "include_fix_suggestions": true,
      "group_by": ["severity", "rule_category"],
      "filters": {
        "min_severity": "warning",
        "exclude_categories": ["informational"]
      }
    }
  }
}
```

## 4. 実装移行戦略

### 4.1 段階的移行アプローチ

**Phase 1: 基盤整備**
- 統一ルール定義スキーマの実装
- 設定管理システムの構築
- プラグインアーキテクチャの基盤実装

**Phase 2: 既存チェッカー統合**
- 既存チェッカーの新アーキテクチャへの移行
- 統一設定による既存機能の再実装
- 後方互換性の確保

**Phase 3: 拡張機能実装**
- 正規表現ベース違反検出・修正提示機能
- 構造的問題検出・対処法出力機能
- 高度なレポーティング機能

**Phase 4: 統合・最適化**
- 全機能の統合テスト
- パフォーマンス最適化
- ユーザビリティ向上

### 4.2 既存システムとの互換性維持

- 既存のCLAUDE.mdルール準拠の維持
- 現在の設定ファイル形式のサポート継続
- 段階的移行による運用継続性の確保
- 既存スクリプトの動作保証

この論理モデルに基づいて、コード品質チェックツールのリファクタリングを進めることで、保守性・拡張性・効率性を大幅に向上させることができます。