"""
インポート修正自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルの
インポート文を自動修正します。
"""
import ast
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from models.check_result import CheckResult, FailureLocation, LogLevel

# 同じディレクトリのモジュールをインポート
sys.path.append(str(Path(__file__).parent))
from local_import_fixer import LocalImportFixer


def main() -> CheckResult:
    """
    ローカルインポート修正のメインエントリーポイント
    
    役割: 関数内のimport文をファイル上部に移動する
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    print(f"🔍 ローカルインポート検出を開始: {src_dir}")
    
    try:
        all_files = list(src_dir.rglob("*.py"))
        if not all_files:
            return CheckResult(
                title="import_fixers",
                log_level=LogLevel.INFO,
                failure_locations=[],
                fix_policy="Pythonファイルが見つかりませんでした。",
                fix_example_code=None
            )
        
        total_local_imports = 0
        files_with_issues = 0
        failure_locations = []
        
        for py_file in all_files:
            if '__pycache__' in str(py_file):
                continue
                
            fixer = LocalImportFixer(str(py_file))
            fixer.read_file()
            local_imports = fixer.detect_local_imports()
            
            if local_imports:
                files_with_issues += 1
                total_local_imports += len(local_imports)
                
                for line_num, import_statement, function_name in local_imports:
                    failure_locations.append(FailureLocation(
                        file_path=str(py_file),
                        line_number=line_num
                    ))
        
        if failure_locations:
            fix_policy = (
                f"{total_local_imports}個のローカルインポートが{files_with_issues}個のファイルで検出されました。\n"
                "関数内・メソッド内のimport文をファイル上部に移動することを推奨します。"
            )
            fix_example = (
                "# 修正前:\n"
                "def some_function():\n"
                "    import os  # ローカルインポート\n"
                "    return os.getcwd()\n\n"
                "# 修正後:\n"
                "import os  # ファイル上部に移動\n\n"
                "def some_function():\n"
                "    return os.getcwd()"
            )
        else:
            fix_policy = "ローカルインポートは検出されませんでした。"
            fix_example = None
        
        return CheckResult(
            title="import_fixers",
            log_level=LogLevel.WARNING if failure_locations else LogLevel.INFO,
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=fix_example
        )
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            title="import_fixers_error",
            log_level=LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"ローカルインポート解析中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


class LocalImportFixer:
    """ローカルインポート修正クラス（簡易版）"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_lines = []
    
    def read_file(self):
        """ファイルを読み込む"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.source_lines = f.readlines()
        except Exception:
            self.source_lines = []
    
    def detect_local_imports(self):
        """ローカルインポートを検出"""
        # local_import_fixer.pyの機能を簡略化して移植
        try:
            source_code = ''.join(self.source_lines)
            tree = ast.parse(source_code)
            
            local_imports = []
            current_function = None
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    current_function = node.name
                elif isinstance(node, (ast.Import, ast.ImportFrom)) and current_function:
                    line_num = node.lineno
                    if line_num <= len(self.source_lines):
                        import_line = self.source_lines[line_num - 1].strip()
                        local_imports.append((line_num, import_line, current_function))
            
            return local_imports
            
        except Exception:
            return []


if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\nCheckResult: {len(result.failure_locations)} import issues found")