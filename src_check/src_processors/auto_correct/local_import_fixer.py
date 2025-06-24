#!/usr/bin/env python3
"""
ローカルインポート修正スクリプト

関数内・メソッド内のimport文を検出し、ファイル上部に強制移動する。
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict, Any, Optional
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src_check.models.check_result import CheckResult, FailureLocation


class LocalImportDetector(ast.NodeVisitor):
    """ローカルインポートを検出するASTビジター"""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.local_imports: List[Tuple[int, str, str]] = []  # (line_number, import_statement, function_name)
        self.current_function: Optional[str] = None
        self.function_stack: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.current_function = node.name
        self.generic_visit(node)
        self.function_stack.pop()
        self.current_function = self.function_stack[-1] if self.function_stack else None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_stack.append(node.name)
        self.current_function = node.name
        self.generic_visit(node)
        self.function_stack.pop()
        self.current_function = self.function_stack[-1] if self.function_stack else None

    def visit_Import(self, node: ast.Import) -> None:
        if self.current_function:
            line_num = node.lineno
            import_line = self.source_lines[line_num - 1].strip()
            self.local_imports.append((line_num, import_line, self.current_function))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self.current_function:
            line_num = node.lineno
            import_line = self.source_lines[line_num - 1].strip()
            self.local_imports.append((line_num, import_line, self.current_function))
        self.generic_visit(node)


class LocalImportFixer:
    """ローカルインポート修正処理"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_lines: List[str] = []
        self.local_imports: List[Tuple[int, str, str]] = []
        self.failure_locations: List[FailureLocation] = []

    def read_file(self) -> None:
        """ファイルを読み込む"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.source_lines = f.readlines()

    def detect_local_imports(self) -> List[Tuple[int, str, str]]:
        """ローカルインポートを検出する"""
        try:
            source_code = ''.join(self.source_lines)
            tree = ast.parse(source_code)
            detector = LocalImportDetector(self.source_lines)
            detector.visit(tree)
            self.local_imports = detector.local_imports
            return self.local_imports
        except SyntaxError as e:
            self.failure_locations.append(
                FailureLocation(file_path=self.file_path, line_number=getattr(e, 'lineno', 0))
            )
            return []

    def fix_local_imports(self) -> bool:
        """ローカルインポートを修正する"""
        if not self.local_imports:
            return False

        try:
            print(f"修正対象: {self.file_path}")
            
            # インポート文を抽出
            imports_to_move: Set[str] = set()
            lines_to_remove: Set[int] = set()
            
            for line_num, import_statement, function_name in self.local_imports:
                print(f"  - Line {line_num}: {import_statement} (in {function_name})")
                imports_to_move.add(import_statement)
                lines_to_remove.add(line_num - 1)  # 0-based index

            # 既存のモジュールレベルインポートの位置を特定
            module_import_end = self._find_module_import_end()

            # 新しいファイル内容を構築
            new_lines = []
            
            # 最初のインポートセクションまでの行をコピー
            for i in range(module_import_end):
                if i not in lines_to_remove:
                    new_lines.append(self.source_lines[i])

            # ローカルインポートを追加
            for import_statement in sorted(imports_to_move):
                new_lines.append(f"{import_statement}\n")

            # 残りの行をコピー（ローカルインポート行は除外）
            for i in range(module_import_end, len(self.source_lines)):
                if i not in lines_to_remove:
                    new_lines.append(self.source_lines[i])

            # ファイルに書き戻し
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            print(f"  修正完了: {len(imports_to_move)}個のインポートを移動")
            return True
            
        except Exception as e:
            # 修正失敗した行をfailure_locationsに追加
            for line_num, _, _ in self.local_imports:
                self.failure_locations.append(
                    FailureLocation(file_path=self.file_path, line_number=line_num)
                )
            print(f"  修正失敗: {e}")
            return False

    def _find_module_import_end(self) -> int:
        """モジュールレベルインポートの終了位置を見つける"""
        import_end = 0
        
        # docstring, shebang, encoding宣言をスキップ
        for i, line in enumerate(self.source_lines):
            stripped = line.strip()
            
            # 空行、コメント、docstringをスキップ
            if (not stripped or 
                stripped.startswith('#') or 
                stripped.startswith('"""') or 
                stripped.startswith("'''") or
                stripped.startswith('r"""') or
                stripped.startswith("r'''")):
                import_end = i + 1
                continue
                
            # インポート文の場合
            if (stripped.startswith('import ') or 
                stripped.startswith('from ')):
                import_end = i + 1
                continue
                
            # その他の文が出現したらインポートセクション終了
            break
            
        return import_end


def scan_directory(directory: str) -> List[str]:
    """ディレクトリ配下のPythonファイルを再帰的にスキャン"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def main() -> CheckResult:
    """メイン処理"""
    parser = argparse.ArgumentParser(description='ローカルインポート修正スクリプト')
    parser.add_argument('--directory', '-d', default='src', 
                      help='スキャン対象ディレクトリ (デフォルト: src)')
    parser.add_argument('--dry-run', action='store_true',
                      help='実際の修正は行わず、検出のみ実行')
    parser.add_argument('--file', '-f', help='特定のファイルのみ処理')
    
    args = parser.parse_args()

    if args.file:
        files_to_process = [args.file]
    else:
        files_to_process = scan_directory(args.directory)

    total_violations = 0
    fixed_files = 0
    all_failure_locations: List[FailureLocation] = []

    print(f"ローカルインポート修正スクリプト開始")
    print(f"対象: {'ファイル: ' + args.file if args.file else 'ディレクトリ: ' + args.directory}")
    print(f"モード: {'DRY RUN' if args.dry_run else '修正実行'}")
    print("-" * 50)

    for file_path in files_to_process:
        if not os.path.exists(file_path):
            print(f"ファイルが存在しません: {file_path}")
            all_failure_locations.append(FailureLocation(file_path=file_path, line_number=0))
            continue

        fixer = LocalImportFixer(file_path)
        fixer.read_file()
        local_imports = fixer.detect_local_imports()

        if local_imports:
            total_violations += len(local_imports)
            print(f"\n違反検出: {file_path}")
            for line_num, import_statement, function_name in local_imports:
                print(f"  Line {line_num}: {import_statement} (in {function_name})")

            if not args.dry_run:
                if fixer.fix_local_imports():
                    fixed_files += 1
                else:
                    # 修正失敗した場合、failure_locationsを追加
                    all_failure_locations.extend(fixer.failure_locations)
        
        # 構文エラー等の失敗もfailure_locationsに含める
        all_failure_locations.extend(fixer.failure_locations)

    print("\n" + "=" * 50)
    print(f"処理完了")
    print(f"総違反数: {total_violations}")
    if not args.dry_run:
        print(f"修正ファイル数: {fixed_files}")
        print(f"修正失敗数: {len(all_failure_locations)}")
    else:
        print("DRY RUNモードのため、実際の修正は行われませんでした")

    # CheckResultを返す
    fix_policy = "ローカルインポート（関数内・メソッド内のimport文）をファイル上部に移動"
    fix_example = """# 修正前
def some_function():
    from some_module import some_function  # ローカルインポート
    return some_function()

# 修正後
from some_module import some_function  # ファイル上部に移動

def some_function():
    return some_function()"""

    return CheckResult(
        failure_locations=all_failure_locations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )


if __name__ == "__main__":
    main()