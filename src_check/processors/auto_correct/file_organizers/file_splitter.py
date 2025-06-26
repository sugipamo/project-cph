import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from models.check_result import CheckResult, FailureLocation

@dataclass
class ImportDependency:
    name: str
    module: str
    is_type_only: bool = False

@dataclass
class FunctionDefinition:
    name: str
    code: str
    imports: List[ImportDependency]
    decorators: List[str]
    line_start: int
    line_end: int

@dataclass
class ClassDefinition:
    name: str
    code: str
    imports: List[ImportDependency]
    decorators: List[str]
    base_classes: List[str]
    line_start: int
    line_end: int
    methods: List[FunctionDefinition]

@dataclass
class ModuleAnalysis:
    path: Path
    module_imports: List[str]
    functions: List[FunctionDefinition]
    classes: List[ClassDefinition]
    constants: List[Tuple[str, str]]
    module_level_code: List[str]

@dataclass
class SplitPlan:
    source_file: Path
    target_dir: Path
    splits: List[Tuple[str, str, str]]

class DependencyAnalyzer(ast.NodeVisitor):

    def __init__(self):
        self.current_scope_imports: Set[str] = set()
        self.used_names: Set[str] = set()
        self.in_annotation = False

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.returns:
            self.in_annotation = True
            self.visit(node.returns)
            self.in_annotation = False
        for arg in node.args.args:
            if arg.annotation:
                self.in_annotation = True
                self.visit(arg.annotation)
                self.in_annotation = False
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.in_annotation = True
        self.visit(node.annotation)
        self.in_annotation = False
        if node.value:
            self.visit(node.value)

class FileSplitter:

    def __init__(self, src_dir: str, single_function_per_file: bool=True, single_class_per_file: bool=True):
        self.src_dir = Path(src_dir)
        self.single_function_per_file = single_function_per_file
        self.single_class_per_file = single_class_per_file
        self.module_analyses: Dict[Path, ModuleAnalysis] = {}
        self.import_mapping: Dict[str, str] = {}

    def analyze_file(self, file_path: Union[Path, str]) -> ModuleAnalysis:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        tree = ast.parse(content, filename=str(file_path))
        module_imports = []
        functions = []
        classes = []
        constants = []
        module_level_code = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_imports.append(ast.unparse(node))
            elif isinstance(node, ast.FunctionDef):
                func_def = self._extract_function(node, lines)
                functions.append(func_def)
            elif isinstance(node, ast.ClassDef):
                class_def = self._extract_class(node, lines)
                classes.append(class_def)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append((target.id, ast.unparse(node)))
            elif not isinstance(node, ast.Expr):
                module_level_code.append(ast.unparse(node))
        return ModuleAnalysis(path=file_path, module_imports=module_imports, functions=functions, classes=classes, constants=constants, module_level_code=module_level_code)

    def _extract_function(self, node: ast.FunctionDef, lines: List[str]) -> FunctionDefinition:
        line_start = node.lineno - 1
        line_end = node.end_lineno
        code_lines = lines[line_start:line_end]
        code = '\n'.join(code_lines)
        analyzer = DependencyAnalyzer()
        analyzer.visit(node)
        decorators = [ast.unparse(d) for d in node.decorator_list]
        imports = self._determine_imports(analyzer.used_names)
        return FunctionDefinition(name=node.name, code=code, imports=imports, decorators=decorators, line_start=line_start, line_end=line_end)

    def _extract_class(self, node: ast.ClassDef, lines: List[str]) -> ClassDefinition:
        line_start = node.lineno - 1
        line_end = node.end_lineno
        code_lines = lines[line_start:line_end]
        code = '\n'.join(code_lines)
        analyzer = DependencyAnalyzer()
        analyzer.visit(node)
        decorators = [ast.unparse(d) for d in node.decorator_list]
        base_classes = [ast.unparse(base) for base in node.bases]
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_def = self._extract_function(item, lines)
                methods.append(method_def)
        imports = self._determine_imports(analyzer.used_names)
        return ClassDefinition(name=node.name, code=code, imports=imports, decorators=decorators, base_classes=base_classes, line_start=line_start, line_end=line_end, methods=methods)

    def _determine_imports(self, used_names: Set[str]) -> List[ImportDependency]:
        imports = []
        for name in used_names:
            if name in {'Any', 'Dict', 'List', 'Set', 'Tuple', 'Optional', 'Union'}:
                imports.append(ImportDependency(name, 'typing', is_type_only=True))
            elif name in {'Protocol', 'runtime_checkable'}:
                imports.append(ImportDependency(name, 'typing', is_type_only=True))
            elif name in {'dataclass', 'field'}:
                imports.append(ImportDependency(name, 'dataclasses', is_type_only=False))
            elif name == 'Path':
                imports.append(ImportDependency(name, 'pathlib', is_type_only=False))
            elif name == 'defaultdict':
                imports.append(ImportDependency(name, 'collections', is_type_only=False))
        return imports

    def should_split_file(self, analysis: ModuleAnalysis) -> bool:
        if self.single_function_per_file and len(analysis.functions) > 1:
            return True
        if self.single_class_per_file and len(analysis.classes) > 1:
            return True
        if self.single_class_per_file and analysis.classes and analysis.functions:
            return True
        return False

    def generate_split_plan(self, analysis: ModuleAnalysis) -> SplitPlan:
        source_file = analysis.path
        target_dir = source_file.parent / f'{source_file.stem}_split'
        splits = []
        for func in analysis.functions:
            target_filename = f'{func.name}.py'
            splits.append((func.name, 'function', target_filename))
        for cls in analysis.classes:
            target_filename = f'{cls.name}.py'
            splits.append((cls.name, 'class', target_filename))
        if analysis.constants:
            splits.append(('constants', 'constants', 'constants.py'))
        return SplitPlan(source_file=source_file, target_dir=target_dir, splits=splits)

    def execute_split(self, analysis: ModuleAnalysis, plan: SplitPlan, dry_run: bool=True) -> None:
        if dry_run:
            print(f'\n📋 分割計画 (Dry Run): {plan.source_file}')
            for name, obj_type, target in plan.splits:
                print(f'  - {name} ({obj_type}) → {plan.target_dir}/{target}')
            return
        plan.target_dir.mkdir(exist_ok=True)
        self._create_init_file(plan.target_dir, plan.splits)
        for func in analysis.functions:
            self._write_function_file(func, plan.target_dir, analysis.module_imports)
        for cls in analysis.classes:
            self._write_class_file(cls, plan.target_dir, analysis.module_imports)
        if analysis.constants:
            self._write_constants_file(analysis.constants, plan.target_dir)
        print(f'✅ 分割完了: {plan.source_file} → {plan.target_dir}/')

    def _create_init_file(self, target_dir: Path, splits: List[Tuple[str, str, str]]) -> None:
        init_content = []
        for name, obj_type, filename in splits:
            if obj_type in ('function', 'class'):
                module_name = filename[:-3]
                init_content.append(f'from .{module_name} import {name}')
        if init_content:
            init_content.append('')
            init_content.append('__all__ = [')
            for name, obj_type, _ in splits:
                if obj_type in ('function', 'class'):
                    init_content.append(f'    "{name}",')
            init_content.append(']')
        init_file = target_dir / '__init__.py'
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(init_content))

    def _write_function_file(self, func: FunctionDefinition, target_dir: Path, module_imports: List[str]) -> None:
        content = []
        imports_by_module = defaultdict(list)
        for imp in func.imports:
            imports_by_module[imp.module].append(imp.name)
        for module, names in sorted(imports_by_module.items()):
            content.append(f'from {module} import {', '.join(sorted(names))}')
        needed_imports = self._filter_needed_imports(module_imports, func.code)
        content.extend(needed_imports)
        if content:
            content.append('')
            content.append('')
        content.append(func.code)
        target_file = target_dir / f'{func.name}.py'
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

    def _write_class_file(self, cls: ClassDefinition, target_dir: Path, module_imports: List[str]) -> None:
        content = []
        imports_by_module = defaultdict(list)
        for imp in cls.imports:
            imports_by_module[imp.module].append(imp.name)
        for module, names in sorted(imports_by_module.items()):
            content.append(f'from {module} import {', '.join(sorted(names))}')
        needed_imports = self._filter_needed_imports(module_imports, cls.code)
        content.extend(needed_imports)
        if content:
            content.append('')
            content.append('')
        content.append(cls.code)
        target_file = target_dir / f'{cls.name}.py'
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

    def _write_constants_file(self, constants: List[Tuple[str, str]], target_dir: Path) -> None:
        content = []
        for _, const_code in constants:
            content.append(const_code)
        target_file = target_dir / 'constants.py'
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

    def _filter_needed_imports(self, imports: List[str], code: str) -> List[str]:
        needed = []
        for imp in imports:
            if 'import' in imp:
                parts = imp.split()
                if len(parts) >= 2:
                    module_or_name = parts[-1]
                    if module_or_name in code:
                        needed.append(imp)
        return needed

    def update_imports_project_wide(self, old_module: str, new_modules: Dict[str, str]) -> None:
        for py_file in self.src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            self._update_imports_in_file(py_file, old_module, new_modules)

    def _update_imports_in_file(self, file_path: Path, old_module: str, new_modules: Dict[str, str]) -> None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            modified = False
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if f'from {old_module} import' in line or f'import {old_module}' in line:
                    imports = self._parse_import_line(line)
                    new_import_lines = self._generate_new_imports(imports, old_module, new_modules)
                    new_lines.extend(new_import_lines)
                    modified = True
                else:
                    new_lines.append(line)
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                print(f'✏️  インポート更新: {file_path}')
        except Exception as e:
            print(f'❌ エラー: {file_path}のインポート更新に失敗: {e}')

    def _parse_import_line(self, line: str) -> List[str]:
        match = re.match('from .+ import (.+)', line)
        if match:
            imports_str = match.group(1)
            return [imp.strip() for imp in imports_str.split(',')]
        return []

    def _generate_new_imports(self, imports: List[str], old_module: str, new_modules: Dict[str, str]) -> List[str]:
        new_lines = []
        for imp in imports:
            if imp in new_modules:
                new_module = new_modules[imp]
                new_lines.append(f'from {new_module} import {imp}')
            else:
                new_lines.append(f'from {old_module} import {imp}')
        return new_lines

    def analyze_and_split_project(self, dry_run: bool=True) -> Dict[str, Any]:
        results = {'files_analyzed': 0, 'files_to_split': 0, 'total_functions': 0, 'total_classes': 0, 'split_plans': []}
        for py_file in self.src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file) or '_split' in str(py_file):
                continue
            analysis = self.analyze_file(py_file)
            self.module_analyses[py_file] = analysis
            results['files_analyzed'] += 1
            results['total_functions'] += len(analysis.functions)
            results['total_classes'] += len(analysis.classes)
            if self.should_split_file(analysis):
                results['files_to_split'] += 1
                plan = self.generate_split_plan(analysis)
                results['split_plans'].append({'source': str(plan.source_file), 'target_dir': str(plan.target_dir), 'splits': plan.splits})
                self.execute_split(analysis, plan, dry_run=dry_run)
        return results

def main() -> CheckResult:
    import os
    project_root = Path(__file__).parent.parent.parent.parent
    src_dir = project_root / 'src'
    dry_run = bool(os.environ.get('SRC_CHECK_DRY_RUN', False))
    single_function = True
    single_class = True
    print(f'🔍 ファイル分割解析を開始: {src_dir}')
    print(f'設定: 1ファイル1関数={single_function}, 1ファイル1クラス={single_class}')
    failure_locations = []
    try:
        splitter = FileSplitter(str(src_dir), single_function_per_file=single_function, single_class_per_file=single_class)
        results = splitter.analyze_and_split_project(dry_run=dry_run)
        print('\n📊 解析結果:')
        print(f'  解析したファイル数: {results['files_analyzed']}')
        print(f'  分割対象ファイル数: {results['files_to_split']}')
        print(f'  総関数数: {results['total_functions']}')
        print(f'  総クラス数: {results['total_classes']}')
        for plan in results.get('split_plans', []):
            failure_locations.append(FailureLocation(file_path=plan['source'], line_number=0))
        if failure_locations:
            fix_policy = f'{len(failure_locations)}個のファイルが1ファイル1関数/1クラスの原則に違反しています。分割を推奨します。'
            fix_example = '# 分割前: utils.py\ndef function1(): ...\ndef function2(): ...\n\n# 分割後:\n# utils/function1.py\ndef function1(): ...\n\n# utils/function2.py\ndef function2(): ...'
        else:
            fix_policy = 'すべてのファイルが1ファイル1関数/1クラスの原則に従っています。'
            fix_example = None
        return CheckResult(failure_locations=failure_locations, fix_policy=fix_policy, fix_example_code=fix_example)
    except Exception as e:
        print(f'\n❌ エラーが発生しました: {e}')
        return CheckResult(failure_locations=[], fix_policy=f'ファイル分割解析中にエラーが発生しました: {str(e)}', fix_example_code=None)
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('使用方法: python file_splitter.py <src_dir> [--execute] [--no-single-function] [--no-single-class]')
        sys.exit(1)
    src_dir = sys.argv[1]
    dry_run = '--execute' not in sys.argv
    single_function = '--no-single-function' not in sys.argv
    single_class = '--no-single-class' not in sys.argv
    main(src_dir, dry_run=dry_run, single_function=single_function, single_class=single_class)