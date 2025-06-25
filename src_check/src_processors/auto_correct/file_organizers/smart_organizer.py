import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
# networkxの代わりに自力実装のgraphクラスを使用
from itertools import combinations

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation


@dataclass
class CodeElement:
    name: str
    type: str  # 'function', 'class', 'constant'
    file_path: Path
    line_start: int
    line_end: int
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


@dataclass
class Module:
    name: str
    elements: List[CodeElement]
    cohesion_score: float
    suggested_path: Path


@dataclass
class OrganizationPlan:
    modules: List[Module]
    migration_steps: List[str]
    risk_assessment: str
    estimated_impact: Dict[str, int]


class SmartOrganizer:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.code_elements: Dict[str, CodeElement] = {}
        self.dependency_graph = SimpleDiGraph()
        self.file_contents: Dict[Path, str] = {}
        
    def analyze_codebase(self) -> None:
        """コードベース全体を解析して依存関係グラフを構築"""
        for py_file in self.src_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                self._analyze_file(py_file)
        
        self._build_dependency_graph()
        
    def _analyze_file(self, file_path: Path) -> None:
        """ファイルを解析してコード要素を抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_contents[file_path] = content
                
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    element = CodeElement(
                        name=node.name,
                        type='function',
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno
                    )
                    self.code_elements[f"{file_path}:{node.name}"] = element
                    
                elif isinstance(node, ast.ClassDef):
                    element = CodeElement(
                        name=node.name,
                        type='class',
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno
                    )
                    self.code_elements[f"{file_path}:{node.name}"] = element
                    
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            
    def _build_dependency_graph(self) -> None:
        """依存関係グラフを構築"""
        for element_id, element in self.code_elements.items():
            self.dependency_graph.add_node(element_id, element=element)
            
        # 簡易的な依存関係検出（実際はより詳細な解析が必要）
        for element_id, element in self.code_elements.items():
            content = self.file_contents.get(element.file_path, "")
            
            for other_id, other in self.code_elements.items():
                if element_id != other_id and other.name in content:
                    # 同じファイル内または明示的なインポートがある場合
                    if element.file_path == other.file_path or f"import {other.name}" in content:
                        self.dependency_graph.add_edge(element_id, other_id)
                        element.dependencies.add(other_id)
                        other.dependents.add(element_id)
                        
    def find_cohesive_modules(self) -> List[Module]:
        """凝集度の高いモジュールを発見"""
        modules = []
        
        # コミュニティ検出アルゴリズムを使用
        try:
            communities = nx.community.greedy_modularity_communities(
                self.dependency_graph.to_undirected()
            )
            
            for i, community in enumerate(communities):
                elements = [
                    self.code_elements[node_id] 
                    for node_id in community
                ]
                
                if len(elements) > 1:  # 複数要素を含むモジュールのみ
                    cohesion = self._calculate_cohesion(community)
                    module = Module(
                        name=f"module_{i}",
                        elements=elements,
                        cohesion_score=cohesion,
                        suggested_path=self._suggest_module_path(elements)
                    )
                    modules.append(module)
                    
        except Exception as e:
            print(f"Community detection failed: {e}")
            
        return modules
        
    def _calculate_cohesion(self, community: Set[str]) -> float:
        """モジュールの凝集度を計算"""
        internal_edges = 0
        external_edges = 0
        
        for node in community:
            for neighbor in self.dependency_graph.neighbors(node):
                if neighbor in community:
                    internal_edges += 1
                else:
                    external_edges += 1
                    
        if internal_edges + external_edges == 0:
            return 0.0
            
        return internal_edges / (internal_edges + external_edges)
        
    def _suggest_module_path(self, elements: List[CodeElement]) -> Path:
        """モジュールの適切なパスを提案"""
        # 要素の名前から共通のテーマを抽出
        names = [e.name.lower() for e in elements]
        
        # 共通のプレフィックスやサフィックスを検出
        if all('repository' in name for name in names):
            return self.src_dir / 'repositories'
        elif all('service' in name for name in names):
            return self.src_dir / 'services'
        elif all('util' in name or 'helper' in name for name in names):
            return self.src_dir / 'utils'
        else:
            # デフォルトは機能別
            return self.src_dir / 'modules' / f"module_{hash(tuple(names)) % 1000}"
            
    def generate_organization_plan(self) -> OrganizationPlan:
        """整理計画を生成"""
        modules = self.find_cohesive_modules()
        
        migration_steps = []
        estimated_impact = {
            'files_affected': 0,
            'functions_moved': 0,
            'classes_moved': 0,
            'imports_updated': 0
        }
        
        for module in modules:
            migration_steps.append(
                f"Create module '{module.name}' at {module.suggested_path}"
            )
            
            unique_files = set(e.file_path for e in module.elements)
            estimated_impact['files_affected'] += len(unique_files)
            
            for element in module.elements:
                if element.type == 'function':
                    estimated_impact['functions_moved'] += 1
                elif element.type == 'class':
                    estimated_impact['classes_moved'] += 1
                    
                migration_steps.append(
                    f"  Move {element.type} '{element.name}' from {element.file_path}"
                )
                
        # リスク評価
        total_elements = len(self.code_elements)
        affected_ratio = sum(len(m.elements) for m in modules) / max(total_elements, 1)
        
        if affected_ratio < 0.2:
            risk_assessment = "低リスク: 影響範囲は限定的"
        elif affected_ratio < 0.5:
            risk_assessment = "中リスク: 慎重な実行が必要"
        else:
            risk_assessment = "高リスク: 段階的な実行を推奨"
            
        return OrganizationPlan(
            modules=modules,
            migration_steps=migration_steps,
            risk_assessment=risk_assessment,
            estimated_impact=estimated_impact
        )
        
    def validate_plan(self, plan: OrganizationPlan) -> List[str]:
        """計画の妥当性を検証"""
        issues = []
        
        for module in plan.modules:
            # 循環依存のチェック
            for i, elem1 in enumerate(module.elements):
                for elem2 in module.elements[i+1:]:
                    elem1_id = f"{elem1.file_path}:{elem1.name}"
                    elem2_id = f"{elem2.file_path}:{elem2.name}"
                    
                    if (elem1_id in elem2.dependencies and 
                        elem2_id in elem1.dependencies):
                        issues.append(
                            f"循環依存: {elem1.name} <-> {elem2.name}"
                        )
                        
            # 凝集度の閾値チェック
            if module.cohesion_score < 0.3:
                issues.append(
                    f"低凝集度警告: {module.name} (score: {module.cohesion_score:.2f})"
                )
                
        return issues


def main() -> CheckResult:
    project_root = Path(__file__).parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    print(f"🔍 スマートファイル整理解析を開始: {src_dir}")
    
    organizer = SmartOrganizer(str(src_dir))
    organizer.analyze_codebase()
    
    plan = organizer.generate_organization_plan()
    issues = organizer.validate_plan(plan)
    
    print(f"\n📊 解析結果:")
    print(f"  発見されたモジュール: {len(plan.modules)}")
    print(f"  影響を受けるファイル: {plan.estimated_impact['files_affected']}")
    print(f"  移動する関数: {plan.estimated_impact['functions_moved']}")
    print(f"  移動するクラス: {plan.estimated_impact['classes_moved']}")
    print(f"  リスク評価: {plan.risk_assessment}")
    
    if issues:
        print(f"\n⚠️  検証で問題が発見されました:")
        for issue in issues:
            print(f"  - {issue}")
    
    failure_locations = []
    
    # 整理が推奨されるファイルをfailure_locationsに追加
    for module in plan.modules:
        unique_files = set(e.file_path for e in module.elements)
        for file_path in unique_files:
            failure_locations.append(FailureLocation(
                file_path=str(file_path),
                line_number=0
            ))
    
    if failure_locations:
        fix_policy = (
            f"{len(plan.modules)}個のモジュールへの再編成を推奨します。"
            f"凝集度に基づいた論理的なグループ化により、"
            f"保守性とテスタビリティが向上します。"
        )
        fix_example = (
            "# 整理前: 様々な機能が混在\n"
            "utils.py\n"
            "  - parse_json()\n"
            "  - validate_email()\n"
            "  - calculate_tax()\n\n"
            "# 整理後: 機能別モジュール\n"
            "parsers/json_parser.py\n"
            "validators/email_validator.py\n"
            "calculations/tax_calculator.py"
        )
    else:
        fix_policy = "現在のファイル構造は適切です。"
        fix_example = None
        
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    # テスト実行
    result = main(None)
    print(f"\nCheckResult: {len(result.failure_locations)} files need reorganization")