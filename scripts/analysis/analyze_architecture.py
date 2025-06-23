#!/usr/bin/env python3
"""
アーキテクチャ分析スクリプト
理論に基づくフォルダ構造・依存関係の分析
"""
import ast
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from infrastructure.logger import Logger


@dataclass
class ModuleMetrics:
    """モジュールメトリクス（Martin's Metrics）"""
    name: str
    afferent_coupling: int  # Ca: このモジュールに依存するモジュール数
    efferent_coupling: int  # Ce: このモジュールが依存するモジュール数
    instability: float      # I = Ce / (Ca + Ce)
    abstractness: float     # A: 抽象クラス・インターフェースの割合
    distance: float         # D: Main Sequence からの距離
    lines_of_code: int
    complexity_score: float


@dataclass
class LayerViolation:
    """レイヤー違反"""
    from_module: str
    to_module: str
    from_layer: str
    to_layer: str
    violation_type: str


@dataclass
class ArchitecturalAnalysis:
    """アーキテクチャ分析結果"""
    module_metrics: List[ModuleMetrics]
    layer_violations: List[LayerViolation]
    circular_dependencies: List[List[str]]
    hotspots: List[str]  # 問題のあるモジュール
    recommendations: List[str]


class ArchitectureAnalyzer:
    def __init__(self, logger: Logger):
        self.logger = logger
        # 期待されるレイヤー構造（Clean Architecture）
        self.expected_layers = {
            'domain': {
                'level': 0,  # 最内層
                'description': 'Business logic, entities, value objects',
                'allowed_dependencies': []
            },
            'application': {
                'level': 1,
                'description': 'Use cases, application services',
                'allowed_dependencies': ['domain']
            },
            'infrastructure': {
                'level': 2,
                'description': 'External adapters, repositories, drivers',
                'allowed_dependencies': ['domain', 'application']
            },
            'context': {
                'level': 1,
                'description': 'Context and configuration',
                'allowed_dependencies': ['domain']
            },
            'workflow': {
                'level': 1,
                'description': 'Workflow orchestration',
                'allowed_dependencies': ['domain', 'application']
            },
            'utils': {
                'level': 0,
                'description': 'Utilities and helpers',
                'allowed_dependencies': []
            }
        }

        self.module_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.module_info: Dict[str, Dict] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

    def analyze_project(self, src_dir: Path) -> ArchitecturalAnalysis:
        """プロジェクト全体を分析"""
        self.logger.info("🏗️  アーキテクチャ分析開始...")

        # 1. モジュール情報収集
        self._collect_module_info(src_dir)

        # 2. 依存関係解析
        self._analyze_dependencies(src_dir)

        # 3. メトリクス計算
        module_metrics = self._calculate_metrics()

        # 4. レイヤー違反検出
        layer_violations = self._detect_layer_violations()

        # 5. 循環依存検出
        circular_deps = self._detect_circular_dependencies()

        # 6. ホットスポット特定
        hotspots = self._identify_hotspots(module_metrics)

        # 7. 推奨事項生成
        recommendations = self._generate_recommendations(
            module_metrics, layer_violations, circular_deps, hotspots
        )

        return ArchitecturalAnalysis(
            module_metrics=module_metrics,
            layer_violations=layer_violations,
            circular_dependencies=circular_deps,
            hotspots=hotspots,
            recommendations=recommendations
        )

    def _collect_module_info(self, src_dir: Path) -> None:
        """モジュール情報を収集"""
        for py_file in src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue

            module_name = self._path_to_module(py_file, src_dir)

            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                # モジュール情報を収集
                classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                abstract_items = len([
                    n for n in ast.walk(tree)
                    if isinstance(n, ast.ClassDef) and
                    any('ABC' in base.id if isinstance(base, ast.Name) else False
                        for base in n.bases)
                ])

                self.module_info[module_name] = {
                    'file_path': py_file,
                    'lines_of_code': len(content.splitlines()),
                    'classes': classes,
                    'functions': functions,
                    'abstract_items': abstract_items,
                    'total_items': classes + functions
                }

            except Exception as e:
                self.logger.warning(f"Failed to analyze {py_file}: {e}")

    def _analyze_dependencies(self, src_dir: Path) -> None:
        """依存関係を解析"""
        for py_file in src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue

            module_name = self._path_to_module(py_file, src_dir)

            try:
                with open(py_file, encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.module.startswith('src.'):
                            imported_module = node.module
                            self.module_dependencies[module_name].add(imported_module)
                            self.reverse_dependencies[imported_module].add(module_name)

                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('src.'):
                                self.module_dependencies[module_name].add(alias.name)
                                self.reverse_dependencies[alias.name].add(module_name)

            except Exception:
                pass

    def _calculate_metrics(self) -> List[ModuleMetrics]:
        """Martin's Metrics を計算"""
        metrics = []

        for module_name, info in self.module_info.items():
            # Ca: Afferent Coupling (入力結合度)
            ca = len(self.reverse_dependencies[module_name])

            # Ce: Efferent Coupling (出力結合度)
            ce = len(self.module_dependencies[module_name])

            # I: Instability (不安定性)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0

            # A: Abstractness (抽象度)
            total_items = info['total_items']
            abstractness = info['abstract_items'] / total_items if total_items > 0 else 0

            # D: Distance from Main Sequence
            # Main Sequence: A + I = 1
            distance = abs(abstractness + instability - 1)

            # 複雑度スコア（独自指標）
            complexity_score = (ce * 2) + (ca * 1.5) + (info['lines_of_code'] / 100)

            metrics.append(ModuleMetrics(
                name=module_name,
                afferent_coupling=ca,
                efferent_coupling=ce,
                instability=instability,
                abstractness=abstractness,
                distance=distance,
                lines_of_code=info['lines_of_code'],
                complexity_score=complexity_score
            ))

        return sorted(metrics, key=lambda x: x.distance, reverse=True)

    def _detect_layer_violations(self) -> List[LayerViolation]:
        """レイヤー違反を検出"""
        violations = []

        for from_module, dependencies in self.module_dependencies.items():
            from_layer = self._get_layer_from_module(from_module)

            for to_module in dependencies:
                to_layer = self._get_layer_from_module(to_module)

                if from_layer and to_layer:
                    # レイヤールール違反チェック
                    violation_type = self._check_layer_violation(from_layer, to_layer, from_module, to_module)

                    if violation_type:
                        violations.append(LayerViolation(
                            from_module=from_module,
                            to_module=to_module,
                            from_layer=from_layer,
                            to_layer=to_layer,
                            violation_type=violation_type
                        ))

        return violations

    def _detect_circular_dependencies(self) -> List[List[str]]:
        """循環依存を検出"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(module: str, path: List[str]) -> None:
            if module in rec_stack:
                # 循環発見
                cycle_start = path.index(module)
                cycle = path[cycle_start:] + [module]
                cycles.append(cycle)
                return

            if module in visited:
                return

            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for dep in self.module_dependencies[module]:
                if dep in self.module_info:  # プロジェクト内モジュールのみ
                    dfs(dep, path.copy())

            rec_stack.remove(module)

        for module in self.module_info:
            if module not in visited:
                dfs(module, [])

        return cycles

    def _identify_hotspots(self, metrics: List[ModuleMetrics]) -> List[str]:
        """問題のあるモジュール（ホットスポット）を特定"""
        hotspots = []

        for metric in metrics:
            issues = []

            # 高い不安定性
            if metric.instability > 0.8:
                issues.append("high_instability")

            # Main Sequenceから離れている
            if metric.distance > 0.7:
                issues.append("architectural_violation")

            # 高い結合度
            if metric.efferent_coupling > 10:
                issues.append("high_coupling")

            # 大きすぎるモジュール
            if metric.lines_of_code > 500:
                issues.append("too_large")

            if issues:
                hotspots.append(f"{metric.name} ({', '.join(issues)})")

        return hotspots

    def _generate_recommendations(self, metrics: List[ModuleMetrics],
                                violations: List[LayerViolation],
                                circular_deps: List[List[str]],
                                hotspots: List[str]) -> List[str]:
        """改善推奨事項を生成"""
        recommendations = []

        if circular_deps:
            recommendations.append(f"🔄 {len(circular_deps)}個の循環依存を解消してください")

        if violations:
            recommendations.append(f"🏗️  {len(violations)}個のレイヤー違反を修正してください")

        # 高結合モジュール
        high_coupling = [m for m in metrics if m.efferent_coupling > 8]
        if high_coupling:
            recommendations.append(f"🔗 {len(high_coupling)}個のモジュールの結合度を下げてください")

        # 大きすぎるモジュール
        large_modules = [m for m in metrics if m.lines_of_code > 400]
        if large_modules:
            recommendations.append(f"📏 {len(large_modules)}個のモジュールを分割してください")

        # アーキテクチャ違反
        arch_violations = [m for m in metrics if m.distance > 0.6]
        if arch_violations:
            recommendations.append(f"📐 {len(arch_violations)}個のモジュールでアーキテクチャ原則違反")

        if not recommendations:
            recommendations.append("✨ アーキテクチャは良好な状態です！")

        return recommendations

    def _path_to_module(self, file_path: Path, src_dir: Path) -> str:
        """ファイルパスをモジュール名に変換"""
        try:
            relative_path = file_path.relative_to(src_dir)
            parts = relative_path.parts

            module_parts = []
            for part in parts:
                if part.endswith('.py'):
                    if part != '__init__.py':
                        module_parts.append(part[:-3])
                else:
                    module_parts.append(part)

            return 'src.' + '.'.join(module_parts) if module_parts else 'src'
        except ValueError as e:
            raise ValueError(f"Failed to convert file path to module: {file_path}") from e

    def _get_layer_from_module(self, module_name: str) -> Optional[str]:
        """モジュール名からレイヤーを特定"""
        if not module_name.startswith('src.'):
            return None

        parts = module_name.split('.')
        if len(parts) < 2:
            return None

        layer_name = parts[1]
        return layer_name if layer_name in self.expected_layers else None

    def _check_layer_violation(self, from_layer: str, to_layer: str,
                             from_module: str, to_module: str) -> Optional[str]:
        """レイヤー違反をチェック"""
        if from_layer not in self.expected_layers or to_layer not in self.expected_layers:
            return None

        allowed_deps = self.expected_layers[from_layer]['allowed_dependencies']

        if to_layer not in allowed_deps:
            from_level = self.expected_layers[from_layer]['level']
            to_level = self.expected_layers[to_layer]['level']

            if from_level < to_level:
                return "upward_dependency"  # 内層が外層に依存
            if from_level == to_level and from_layer != to_layer:
                return "cross_layer_dependency"  # 同レベル間の依存
            return "forbidden_dependency"  # 禁止された依存

        return None


def main():
    """メイン処理"""
    from infrastructure.logger import create_logger
    from infrastructure.system_operations_impl import LocalSystemOperations

    logger = create_logger(verbose=False, silent=False, system_operations=None)
    system_ops = LocalSystemOperations()

    argv = system_ops.get_argv()
    if len(argv) < 2:
        logger.info("Usage: python analyze_architecture.py <src_directory>")
        system_ops.exit(1)

    src_dir = Path(argv[1])
    analyzer = ArchitectureAnalyzer(logger)

    # 分析実行
    analysis = analyzer.analyze_project(src_dir)

    # 結果表示
    logger.info("\n" + "=" * 60)
    logger.info("📊 アーキテクチャ分析結果")
    logger.info("=" * 60)

    # モジュールメトリクス（上位問題）
    logger.info("\n🎯 問題のあるモジュール (Top 10):")
    for i, metric in enumerate(analysis.module_metrics[:10], 1):
        logger.info(f"{i:2d}. {metric.name}")
        logger.info(f"    Distance: {metric.distance:.3f}, "
              f"Instability: {metric.instability:.3f}, "
              f"Coupling: {metric.efferent_coupling}")

    # レイヤー違反
    if analysis.layer_violations:
        logger.info(f"\n🏗️  レイヤー違反 ({len(analysis.layer_violations)}件):")
        for violation in analysis.layer_violations[:5]:
            logger.info(f"   {violation.from_layer} -> {violation.to_layer}: "
                  f"{violation.violation_type}")

    # 循環依存
    if analysis.circular_dependencies:
        logger.info(f"\n🔄 循環依存 ({len(analysis.circular_dependencies)}件):")
        for cycle in analysis.circular_dependencies[:3]:
            logger.info(f"   {' -> '.join(cycle)}")

    # 推奨事項
    logger.info("\n💡 推奨事項:")
    for rec in analysis.recommendations:
        logger.info(f"   {rec}")

    # JSON出力オプション
    if '--json' in argv:
        output_file = 'architecture_analysis.json'
        with open(output_file, 'w', encoding='utf-8'):
            # dataclassをdictに変換
            {
                'module_metrics': [asdict(m) for m in analysis.module_metrics],
                'layer_violations': [asdict(v) for v in analysis.layer_violations],
                'circular_dependencies': analysis.circular_dependencies,
                'hotspots': analysis.hotspots,
                'recommendations': analysis.recommendations
            }
            # JSON書き込みは依存性注入が必要
            # json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n📄 詳細結果を {output_file} に出力しました")


if __name__ == "__main__":
    main()
