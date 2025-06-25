import ast
import os
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import shutil
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation

@dataclass
class ImportInfo:
    module: str
    names: List[str]
    is_from_import: bool
    is_relative: bool
    level: int
    line_number: int

@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    methods: List[str]
    line_number: int

@dataclass
class FunctionInfo:
    name: str
    line_number: int

@dataclass
class FileAnalysis:
    path: Path
    imports: List[ImportInfo]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    has_type_checking_import: bool
    has_circular_reference: bool

@dataclass
class MoveStep:
    source: Path
    destination: Path
    reason: str

class ASTAnalyzer(ast.NodeVisitor):

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.imports: List[ImportInfo] = []
        self.classes: List[ClassInfo] = []
        self.functions: List[FunctionInfo] = []
        self.has_type_checking_import = False
        self.type_checking_imports: List[ImportInfo] = []
        self.in_type_checking = False

    def visit_If(self, node: ast.If) -> None:
        if isinstance(node.test, ast.Name) and node.test.id == 'TYPE_CHECKING':
            self.in_type_checking = True
            self.has_type_checking_import = True
            self.generic_visit(node)
            self.in_type_checking = False
        else:
            self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            import_info = ImportInfo(module=alias.name, names=[alias.asname or alias.name], is_from_import=False, is_relative=False, level=0, line_number=node.lineno)
            if self.in_type_checking:
                self.type_checking_imports.append(import_info)
            else:
                self.imports.append(import_info)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == 'typing' and any((alias.name == 'TYPE_CHECKING' for alias in node.names)):
            pass
        else:
            names = [alias.name for alias in node.names]
            import_info = ImportInfo(module=node.module or '', names=names, is_from_import=True, is_relative=node.level > 0, level=node.level, line_number=node.lineno)
            if self.in_type_checking:
                self.type_checking_imports.append(import_info)
            else:
                self.imports.append(import_info)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [self._get_name(base) for base in node.bases]
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        self.classes.append(ClassInfo(name=node.name, bases=bases, methods=methods, line_number=node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(FunctionInfo(name=node.name, line_number=node.lineno))
        self.generic_visit(node)

    def _get_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self._get_name(node.value)}.{node.attr}'
        return str(node)

class StructureOrganizer:

    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.file_analyses: Dict[Path, FileAnalysis] = {}
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.circular_references: List[Tuple[str, str]] = []
        self.delayed_imports: List[Tuple[str, str]] = []

    def analyze_project(self) -> None:
        for py_file in self.src_dir.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                self._analyze_file(py_file)
        self._build_import_graph()
        self._detect_circular_references()
        self._detect_delayed_imports()

    def _analyze_file(self, file_path: Path) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            analyzer = ASTAnalyzer(file_path)
            analyzer.visit(tree)
            analysis = FileAnalysis(path=file_path, imports=analyzer.imports + analyzer.type_checking_imports, classes=analyzer.classes, functions=analyzer.functions, has_type_checking_import=analyzer.has_type_checking_import, has_circular_reference=False)
            self.file_analyses[file_path] = analysis
        except Exception as e:
            print(f'Error analyzing {file_path}: {e}')

    def _build_import_graph(self) -> None:
        for file_path, analysis in self.file_analyses.items():
            module_name = self._path_to_module(file_path)
            for import_info in analysis.imports:
                if import_info.is_relative:
                    imported_module = self._resolve_relative_import(file_path, import_info.module, import_info.level)
                else:
                    imported_module = import_info.module
                if imported_module and self._is_project_module(imported_module):
                    self.import_graph[module_name].add(imported_module)

    def _path_to_module(self, path: Path) -> str:
        relative = path.relative_to(self.src_dir)
        parts = list(relative.parts)
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        elif parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        return '.'.join(parts)

    def _resolve_relative_import(self, file_path: Path, module: str, level: int) -> Optional[str]:
        current = file_path.parent
        for _ in range(level - 1):
            current = current.parent
        if module:
            target = current / module.replace('.', '/')
        else:
            target = current
        if target.is_file() and target.suffix == '.py':
            return self._path_to_module(target)
        elif (target / '__init__.py').exists():
            return self._path_to_module(target / '__init__.py')
        return None

    def _is_project_module(self, module: str) -> bool:
        parts = module.split('.')
        if not parts:
            return False
        path = self.src_dir
        for part in parts:
            path = path / part
        return path.with_suffix('.py').exists() or (path / '__init__.py').exists()

    def _detect_circular_references(self) -> None:
        visited = set()
        rec_stack = set()

        def has_cycle(module: str, path: List[str]) -> bool:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            for neighbor in self.import_graph.get(module, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    self.circular_references.append((cycle[0], cycle[-1]))
                    return True
            rec_stack.remove(module)
            return False
        for module in self.import_graph:
            if module not in visited:
                has_cycle(module, [])

    def _detect_delayed_imports(self) -> None:
        for file_path, analysis in self.file_analyses.items():
            if analysis.has_type_checking_import:
                module_name = self._path_to_module(file_path)
                self.delayed_imports.append((module_name, str(file_path)))

    def check_issues(self) -> bool:
        has_issues = False
        if self.circular_references:
            print('❌ 循環参照が検出されました:')
            for ref in self.circular_references:
                print(f'  - {ref[0]} <-> {ref[1]}')
            has_issues = True
        if self.delayed_imports:
            print('❌ 遅延インポートが検出されました:')
            for module, path in self.delayed_imports:
                print(f'  - {module} ({path})')
            has_issues = True
        return has_issues

    def determine_ideal_structure(self) -> Dict[str, str]:
        ideal_structure = {}
        for file_path, analysis in self.file_analyses.items():
            module_type = self._determine_module_type(analysis)
            ideal_path = self._get_ideal_path(file_path, module_type, analysis)
            if ideal_path != file_path:
                ideal_structure[str(file_path)] = str(ideal_path)
        return ideal_structure

    def _determine_module_type(self, analysis: FileAnalysis) -> str:
        path_str = str(analysis.path)
        if 'infrastructure' in path_str:
            return 'infrastructure'
        elif 'domain' in path_str or 'models' in path_str:
            return 'domain'
        elif 'application' in path_str or 'services' in path_str:
            return 'application'
        elif 'presentation' in path_str or 'api' in path_str:
            return 'presentation'
        elif 'configuration' in path_str or 'config' in path_str:
            return 'configuration'
        elif 'utils' in path_str or 'helpers' in path_str:
            return 'shared'
        else:
            if analysis.classes:
                if any(('Repository' in cls.name for cls in analysis.classes)):
                    return 'infrastructure'
                elif any(('Service' in cls.name for cls in analysis.classes)):
                    return 'application'
                elif any(('Model' in cls.name or 'Entity' in cls.name for cls in analysis.classes)):
                    return 'domain'
            return 'shared'

    def _get_ideal_path(self, current_path: Path, module_type: str, analysis: FileAnalysis) -> Path:
        relative = current_path.relative_to(self.src_dir)
        file_name = relative.name
        type_to_dir = {'infrastructure': 'infrastructure', 'domain': 'domain', 'application': 'application', 'presentation': 'presentation', 'configuration': 'configuration', 'shared': 'shared'}
        ideal_dir = self.src_dir / type_to_dir[module_type]
        if len(relative.parts) > 1:
            sub_path = Path(*relative.parts[1:-1])
            ideal_dir = ideal_dir / sub_path
        return ideal_dir / file_name

    def generate_move_plan(self, ideal_structure: Dict[str, str]) -> List[MoveStep]:
        move_steps = []
        for source_str, dest_str in ideal_structure.items():
            source = Path(source_str)
            dest = Path(dest_str)
            reason = self._get_move_reason(source, dest)
            move_steps.append(MoveStep(source, dest, reason))
        return self._validate_move_plan(move_steps)

    def _get_move_reason(self, source: Path, dest: Path) -> str:
        source_parts = source.parts
        dest_parts = dest.parts
        if 'infrastructure' in dest_parts:
            return '副作用を含むモジュールをinfrastructureに移動'
        elif 'domain' in dest_parts:
            return 'ドメインモデルをdomainレイヤーに移動'
        elif 'application' in dest_parts:
            return 'アプリケーションサービスをapplicationレイヤーに移動'
        elif 'configuration' in dest_parts:
            return '設定関連モジュールをconfigurationに移動'
        else:
            return f'{source.name}を適切なレイヤーに移動'

    def _validate_move_plan(self, move_steps: List[MoveStep]) -> List[MoveStep]:
        destinations = {}
        for step in move_steps:
            if step.destination in destinations:
                print(f'⚠️  警告: {step.destination}への重複移動が検出されました')
            destinations[step.destination] = step.source
        return move_steps

    def execute_reorganization(self, move_steps: List[MoveStep], dry_run: bool=True) -> None:
        if dry_run:
            print('\n📋 実行計画 (Dry Run):')
            for step in move_steps:
                print(f'  {step.source} → {step.destination}')
                print(f'    理由: {step.reason}')
            return
        import_updates = {}
        for step in move_steps:
            print(f'\n🚚 移動中: {step.source} → {step.destination}')
            step.destination.parent.mkdir(parents=True, exist_ok=True)
            old_module = self._path_to_module(step.source)
            new_module = self._path_to_module(step.destination)
            import_updates[old_module] = new_module
            shutil.copy2(step.source, step.destination)
            self._update_imports_in_file(step.destination, import_updates)
        for py_file in self.src_dir.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                self._update_imports_in_file(py_file, import_updates)
        for step in move_steps:
            if step.source.exists():
                step.source.unlink()
                print(f'🗑️  削除: {step.source}')
        self._cleanup_empty_dirs()

    def _update_imports_in_file(self, file_path: Path, import_updates: Dict[str, str]) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            modified = False
            for old_module, new_module in import_updates.items():
                patterns = [(f'from {old_module} import', f'from {new_module} import'), (f'import {old_module}', f'import {new_module}'), (f'"{old_module}"', f'"{new_module}"'), (f"'{old_module}'", f"'{new_module}'")]
                for old_pattern, new_pattern in patterns:
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        modified = True
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'✏️  インポート更新: {file_path}')
        except Exception as e:
            print(f'❌ エラー: {file_path}のインポート更新に失敗: {e}')

    def _cleanup_empty_dirs(self) -> None:
        for root, dirs, files in os.walk(self.src_dir, topdown=False):
            if not files and (not dirs):
                Path(root).rmdir()
                print(f'🗑️  空ディレクトリ削除: {root}')

    def generate_report(self) -> Dict[str, Any]:
        report = {'total_files': len(self.file_analyses), 'circular_references': len(self.circular_references), 'delayed_imports': len(self.delayed_imports), 'file_details': {}, 'issues': {'circular_references': [{'from': ref[0], 'to': ref[1]} for ref in self.circular_references], 'delayed_imports': [{'module': module, 'file': path} for module, path in self.delayed_imports]}}
        for file_path, analysis in self.file_analyses.items():
            report['file_details'][str(file_path)] = {'classes': len(analysis.classes), 'functions': len(analysis.functions), 'imports': len(analysis.imports), 'has_type_checking': analysis.has_type_checking_import}
        return report

def main() -> CheckResult:
    project_root = Path(__file__).parent.parent.parent.parent
    src_dir = project_root / 'src'
    report_path = project_root / 'structure_analysis_report.json'
    dry_run = True
    print(f'🔍 プロジェクト構造の解析を開始: {src_dir}')
    failure_locations = []
    organizer = StructureOrganizer(str(src_dir))
    organizer.analyze_project()
    if organizer.check_issues():
        print('\n❌ 循環参照または遅延インポートが検出されたため、処理を停止します。')
        print('これらの問題を解決してから再実行してください。')
        for ref1, ref2 in organizer.circular_references:
            failure_locations.append(FailureLocation(file_path=ref1, line_number=0))
        for delayed in organizer.delayed_imports:
            failure_locations.append(FailureLocation(file_path=delayed[0], line_number=0))
        if report_path:
            report = organizer.generate_report()
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f'\n📊 詳細レポートを保存しました: {report_path}')
        return CheckResult(failure_locations=failure_locations, fix_policy='循環参照と遅延インポートを解決してください', fix_example_code='# TYPE_CHECKINGブロック内でインポートを遅延させる例\nfrom typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from some_module import SomeClass')
    print('\n✅ 循環参照・遅延インポートは検出されませんでした。')
    ideal_structure = organizer.determine_ideal_structure()
    if not ideal_structure:
        print('✅ 現在の構造は適切です。変更の必要はありません。')
        return CheckResult(failure_locations=[], fix_policy='現在の構造は適切です', fix_example_code=None)
    print(f'\n📐 {len(ideal_structure)}個のファイルの再配置が必要です。')
    move_steps = organizer.generate_move_plan(ideal_structure)
    organizer.execute_reorganization(move_steps, dry_run=dry_run)
    for step in move_steps:
        failure_locations.append(FailureLocation(file_path=str(step.source), line_number=0))
    if report_path:
        report = organizer.generate_report()
        report['move_plan'] = [{'source': str(step.source), 'destination': str(step.destination), 'reason': step.reason} for step in move_steps]
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f'\n📊 レポートを保存しました: {report_path}')
    print('\n✅ 処理が完了しました。')
    return CheckResult(failure_locations=failure_locations, fix_policy='ファイルの再配置により構造を改善します。詳細はレポートを参照してください。', fix_example_code='# 適切なディレクトリ構造の例:\n# src/\n#   models/\n#   services/\n#   utils/')
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('使用方法: python structure_organizer.py <src_dir> [--execute] [--report <path>]')
        sys.exit(1)
    src_dir = sys.argv[1]
    dry_run = '--execute' not in sys.argv
    report_path = None
    if '--report' in sys.argv:
        report_idx = sys.argv.index('--report')
        if report_idx + 1 < len(sys.argv):
            report_path = sys.argv[report_idx + 1]
    main(src_dir, dry_run=dry_run, report_path=report_path)