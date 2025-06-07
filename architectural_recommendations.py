#!/usr/bin/env python3
"""
アーキテクチャ改善提案と理想的な依存構造の生成
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class ArchitecturalRecommendations:
    def __init__(self, analysis_report_path: str):
        with open(analysis_report_path, 'r', encoding='utf-8') as f:
            self.analysis = json.load(f)
    
    def get_ideal_layer_structure(self) -> Dict[str, Dict]:
        """理想的なレイヤー構造を定義"""
        return {
            "Level 0 - Foundation": {
                "description": "最も基本的なユーティリティ、型定義、定数",
                "modules": [
                    "src.domain.constants",
                    "src.domain.types", 
                    "src.shared.exceptions",
                    "src.utils"
                ],
                "dependencies": [],
                "principles": ["他に依存しない", "純粋関数中心", "副作用なし"]
            },
            "Level 1 - Domain Core": {
                "description": "ドメインロジックの中核、ビジネスルール",
                "modules": [
                    "src.domain.results",
                    "src.domain.requests.base",
                    "src.shared.utils.basic_formatter",
                    "src.shared.utils.pure_functions"
                ],
                "dependencies": ["Level 0"],
                "principles": ["ビジネスロジックのみ", "インフラに依存しない", "安定性重視"]
            },
            "Level 2 - Domain Extensions": {
                "description": "具体的なドメインリクエスト実装",
                "modules": [
                    "src.domain.requests.file",
                    "src.domain.requests.shell", 
                    "src.domain.requests.python",
                    "src.domain.requests.docker",
                    "src.shared.utils.docker",
                    "src.shared.utils.shell",
                    "src.shared.utils.python"
                ],
                "dependencies": ["Level 0", "Level 1"],
                "principles": ["ドメイン知識の具体化", "基本ドメインに依存"]
            },
            "Level 3 - Domain Orchestration": {
                "description": "ドメイン要素の組み合わせとワークフロー",
                "modules": [
                    "src.domain.requests.composite",
                    "src.env_core.step",
                    "src.env_core.workflow"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 2"],
                "principles": ["ドメインオブジェクトの組み合わせ", "複雑なワークフロー管理"]
            },
            "Level 4 - Application Services": {
                "description": "アプリケーション固有のサービスとフォーマッター",
                "modules": [
                    "src.application.formatters",
                    "src.shared.utils.unified_formatter",  # 移動候補
                    "src.pure_functions"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 2"],
                "principles": ["UI/表示ロジック", "ドメインの表現変換"]
            },
            "Level 5 - Application Orchestration": {
                "description": "アプリケーションレベルのオーケストレーション",
                "modules": [
                    "src.application.orchestration",
                    "src.application.factories"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 2", "Level 3", "Level 4"],
                "principles": ["ドメインとインフラの調整", "高レベルワークフロー"]
            },
            "Level 6 - Infrastructure Interfaces": {
                "description": "インフラストラクチャの抽象化",
                "modules": [
                    "src.infrastructure.drivers.base",
                    "src.infrastructure.environment.base_strategy"
                ],
                "dependencies": ["Level 0", "Level 1"],
                "principles": ["インフラ抽象化", "依存性逆転原則"]
            },
            "Level 7 - Infrastructure Implementation": {
                "description": "具体的なインフラ実装",
                "modules": [
                    "src.infrastructure.drivers.file",
                    "src.infrastructure.drivers.shell",
                    "src.infrastructure.drivers.python",
                    "src.infrastructure.drivers.docker",
                    "src.infrastructure.persistence"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 6"],
                "principles": ["外部システム連携", "技術詳細の実装"]
            },
            "Level 8 - Infrastructure Services": {
                "description": "高レベルインフラサービス",
                "modules": [
                    "src.infrastructure.environment",
                    "src.infrastructure.config",
                    "src.infrastructure.mock"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 6", "Level 7"],
                "principles": ["設定管理", "環境構築", "テスト支援"]
            },
            "Level 9 - Context & Integration": {
                "description": "コンテキスト管理と統合レイヤー",
                "modules": [
                    "src.context",
                    "src.env_integration"
                ],
                "dependencies": ["Level 0", "Level 1", "Level 2", "Level 3"],
                "principles": ["実行コンテキスト", "環境適応", "ドメインに集中"]
            },
            "Level 10 - Main & Entry Points": {
                "description": "アプリケーションエントリーポイント",
                "modules": [
                    "src.main",
                    "src.workflow_execution_service"
                ],
                "dependencies": ["全レベル"],
                "principles": ["全体調整", "外部インターフェース"]
            }
        }
    
    def analyze_current_violations(self) -> List[Dict]:
        """現在の違反を分析"""
        violations = []
        ideal_structure = self.get_ideal_layer_structure()
        
        # 既知の問題を構造化
        known_issues = [
            {
                "type": "Architecture Violation",
                "severity": "Critical",
                "module": "src.shared.utils.unified_formatter",
                "issue": "shared.utils depends on application.formatters",
                "recommendation": "Move unified_formatter to application layer or create interface"
            },
            {
                "type": "Architecture Violation", 
                "severity": "Critical",
                "module": "src.domain.requests.file.file_request",
                "issue": "Domain depends on application.orchestration",
                "recommendation": "Remove direct dependency, use dependency injection or observer pattern"
            },
            {
                "type": "Architecture Violation",
                "severity": "Critical", 
                "module": "src.domain.requests.docker.docker_request",
                "issue": "Domain depends on infrastructure.drivers",
                "recommendation": "Use interface abstraction instead of direct implementation dependency"
            },
            {
                "type": "Circular Dependency",
                "severity": "High",
                "module": "src.domain.requests.composite",
                "issue": "Circular dependency between composite_request and composite_structure",
                "recommendation": "Refactor to separate concerns or merge classes"
            },
            {
                "type": "High Coupling",
                "severity": "Medium",
                "module": "src.infrastructure.config.di_config", 
                "issue": "Too many dependencies (17)",
                "recommendation": "Split into smaller configuration modules"
            }
        ]
        
        return known_issues
    
    def generate_migration_plan(self) -> List[Dict]:
        """段階的な移行計画を生成"""
        return [
            {
                "phase": "Phase 1 - Critical Architecture Fixes",
                "priority": "Critical",
                "duration": "1-2 weeks",
                "tasks": [
                    {
                        "task": "Fix shared.utils.unified_formatter dependency",
                        "actions": [
                            "Create src.application.formatters.unified_formatter",
                            "Move UnifiedFormatter class to application layer",
                            "Create interface in shared.utils for backward compatibility",
                            "Update all imports to use new location"
                        ],
                        "files_affected": [
                            "src/shared/utils/unified_formatter.py",
                            "src/application/formatters/unified_formatter.py"
                        ]
                    },
                    {
                        "task": "Remove domain->application dependencies",
                        "actions": [
                            "Create interfaces for OutputManager and ExecutionController",
                            "Use dependency injection pattern",
                            "Remove direct imports from domain to application"
                        ],
                        "files_affected": [
                            "src/domain/requests/file/file_request.py",
                            "src/domain/requests/composite/composite_request.py",
                            "src/domain/requests/shell/shell_request.py"
                        ]
                    }
                ]
            },
            {
                "phase": "Phase 2 - Domain-Infrastructure Separation",
                "priority": "High",
                "duration": "2-3 weeks",
                "tasks": [
                    {
                        "task": "Create infrastructure interfaces",
                        "actions": [
                            "Define driver interfaces in domain layer",
                            "Implement dependency injection for drivers",
                            "Remove direct infrastructure imports from domain"
                        ],
                        "files_affected": [
                            "src/domain/requests/docker/docker_request.py"
                        ]
                    },
                    {
                        "task": "Fix circular dependency in composite requests",
                        "actions": [
                            "Analyze composite_request and composite_structure relationship",
                            "Merge classes or separate concerns properly",
                            "Ensure unidirectional dependency flow"
                        ],
                        "files_affected": [
                            "src/domain/requests/composite/composite_request.py",
                            "src/domain/requests/composite/composite_structure.py"
                        ]
                    }
                ]
            },
            {
                "phase": "Phase 3 - Layer Optimization",
                "priority": "Medium",
                "duration": "1-2 weeks", 
                "tasks": [
                    {
                        "task": "Reduce di_config coupling",
                        "actions": [
                            "Split di_config into smaller modules",
                            "Group related configurations",
                            "Use factory pattern for complex dependencies"
                        ],
                        "files_affected": [
                            "src/infrastructure/config/di_config.py"
                        ]
                    },
                    {
                        "task": "Optimize context layer dependencies",
                        "actions": [
                            "Review context dependencies on application layer",
                            "Ensure context focuses on execution environment",
                            "Remove unnecessary cross-layer dependencies"
                        ],
                        "files_affected": [
                            "src/context/execution_context.py",
                            "src/context/user_input_parser.py"
                        ]
                    }
                ]
            },
            {
                "phase": "Phase 4 - Documentation & Validation",
                "priority": "Low",
                "duration": "1 week",
                "tasks": [
                    {
                        "task": "Create architecture documentation",
                        "actions": [
                            "Document layer responsibilities",
                            "Create dependency rules",
                            "Add automated architecture tests"
                        ]
                    },
                    {
                        "task": "Implement continuous monitoring",
                        "actions": [
                            "Add pre-commit hooks for dependency checking",
                            "Create CI pipeline for architecture validation",
                            "Regular dependency analysis reports"
                        ]
                    }
                ]
            }
        ]
    
    def generate_specific_recommendations(self) -> Dict:
        """具体的な改善提案を生成"""
        return {
            "immediate_actions": [
                {
                    "action": "Move unified_formatter to application layer",
                    "rationale": "Shared utilities should not depend on application-specific components",
                    "implementation": "Create new file in src/application/formatters/unified_formatter.py",
                    "backward_compatibility": "Keep wrapper in shared.utils that delegates to new location"
                },
                {
                    "action": "Create domain interfaces for external dependencies",
                    "rationale": "Domain should not directly depend on infrastructure implementations",
                    "implementation": "Define abstract interfaces in domain layer",
                    "dependency_injection": "Use DI container to provide implementations"
                }
            ],
            "architectural_patterns": [
                {
                    "pattern": "Dependency Inversion Principle",
                    "usage": "Domain defines interfaces, infrastructure implements them",
                    "benefit": "Reduces coupling and improves testability"
                },
                {
                    "pattern": "Observer Pattern",
                    "usage": "For communication between domain and application layers",
                    "benefit": "Eliminates direct dependencies while maintaining communication"
                },
                {
                    "pattern": "Factory Pattern",
                    "usage": "For creating complex objects with many dependencies",
                    "benefit": "Centralizes object creation and reduces coupling"
                }
            ],
            "testing_strategy": [
                {
                    "level": "Unit Tests",
                    "focus": "Individual modules with mocked dependencies",
                    "coverage": "Each layer tested in isolation"
                },
                {
                    "level": "Integration Tests", 
                    "focus": "Layer interactions and dependency injection",
                    "coverage": "Cross-layer communication"
                },
                {
                    "level": "Architecture Tests",
                    "focus": "Dependency rules and layer violations",
                    "coverage": "Automated architecture validation"
                }
            ]
        }
    
    def generate_full_report(self):
        """完全な改善レポートを生成"""
        ideal_structure = self.get_ideal_layer_structure()
        violations = self.analyze_current_violations()
        migration_plan = self.generate_migration_plan()
        recommendations = self.generate_specific_recommendations()
        
        report = {
            "ideal_layer_structure": ideal_structure,
            "current_violations": violations,
            "migration_plan": migration_plan,
            "specific_recommendations": recommendations,
            "success_metrics": {
                "dependency_violations": "Reduce to 0",
                "circular_dependencies": "Eliminate completely", 
                "max_layer_depth": "Keep under 10",
                "high_coupling_modules": "Reduce modules with >8 dependencies to <3"
            }
        }
        
        return report

def main():
    # 分析レポートを読み込み
    analyzer = ArchitecturalRecommendations("/home/cphelper/project-cph/detailed_dependency_report.json")
    report = analyzer.generate_full_report()
    
    # レポートを保存
    with open("/home/cphelper/project-cph/architectural_recommendations.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 主要な推奨事項を表示
    print("="*80)
    print("🏗️  アーキテクチャ改善提案レポート")
    print("="*80)
    
    print("\n🎯 理想的なレイヤー構造:")
    for level_name, level_info in report["ideal_layer_structure"].items():
        print(f"\n  📊 {level_name}:")
        print(f"    📝 {level_info['description']}")
        print(f"    📦 代表モジュール: {level_info['modules'][:3]}{'...' if len(level_info['modules']) > 3 else ''}")
        print(f"    🔗 依存: {level_info['dependencies']}")
    
    print(f"\n⚠️  現在の問題 ({len(report['current_violations'])} 個):")
    for violation in report["current_violations"]:
        severity_emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "⚡"}
        emoji = severity_emoji.get(violation["severity"], "ℹ️")
        print(f"  {emoji} {violation['severity']}: {violation['module']}")
        print(f"    問題: {violation['issue']}")
        print(f"    推奨: {violation['recommendation']}")
    
    print(f"\n📋 移行計画 ({len(report['migration_plan'])} フェーズ):")
    for phase in report["migration_plan"]:
        priority_emoji = {"Critical": "🚨", "High": "⚠️", "Medium": "⚡", "Low": "ℹ️"}
        emoji = priority_emoji.get(phase["priority"], "📌")
        print(f"\n  {emoji} {phase['phase']} ({phase['duration']})")
        for task in phase["tasks"][:2]:  # 最初の2つのタスクのみ表示
            print(f"    ✅ {task['task']}")
            print(f"      {task['actions'][0]}")
    
    print(f"\n🎯 成功指標:")
    for metric, target in report["success_metrics"].items():
        print(f"  📈 {metric}: {target}")
    
    print(f"\n💾 完全なレポートを architectural_recommendations.json に保存しました")

if __name__ == "__main__":
    main()