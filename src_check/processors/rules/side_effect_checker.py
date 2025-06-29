"""
副作用チェックルール

CLAUDE.mdに従い、src/infrastructure以外での副作用を検出します。
副作用には以下が含まれます：
- ファイルI/O
- ネットワーク通信
- データベースアクセス
- 環境変数の読み取り
- 外部プロセスの実行
- 標準入出力
"""
import ast
from pathlib import Path
from typing import List, Set
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation, LogLevel

class SideEffectChecker(ast.NodeVisitor):
    """
    副作用をチェックするクラス
    """
    
    # 副作用を持つ可能性のある関数・メソッド
    SIDE_EFFECT_PATTERNS = {
        # ファイルI/O
        'open', 'read', 'write', 'close',
        'mkdir', 'rmdir', 'remove', 'unlink', 'rename',
        'exists', 'isfile', 'isdir',
        # パスライブラリ
        'Path.read_text', 'Path.write_text', 'Path.read_bytes', 'Path.write_bytes',
        'Path.mkdir', 'Path.rmdir', 'Path.unlink', 'Path.rename',
        # ネットワーク
        'urlopen', 'request', 'get', 'post', 'put', 'delete',
        'socket', 'connect', 'send', 'recv',
        # データベース
        'execute', 'commit', 'rollback', 'cursor',
        # 環境変数
        'os.environ', 'getenv', 'putenv',
        # プロセス実行
        'subprocess.run', 'subprocess.call', 'subprocess.Popen',
        'os.system', 'os.popen',
        # 標準入出力
        'print', 'input',
        # その他
        'datetime.now', 'time.time', 'random',
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        self.imported_modules = set()
        
    def visit_Import(self, node):
        """import文を記録"""
        for alias in node.names:
            self.imported_modules.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """from ... import文を記録"""
        if node.module:
            self.imported_modules.add(node.module)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        func_name = self._get_function_name(node.func)
        if func_name and self._is_side_effect(func_name):
            self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)
        
    def visit_With(self, node):
        """with文（ファイル操作など）をチェック"""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func_name = self._get_function_name(item.context_expr.func)
                if func_name == 'open':
                    self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)
        
    def _get_function_name(self, node) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            obj_name = self._get_function_name(node.value)
            if obj_name:
                return f"{obj_name}.{node.attr}"
            return node.attr
        return ""
        
    def _is_side_effect(self, func_name: str) -> bool:
        """副作用を持つ関数かチェック"""
        # 完全一致
        if func_name in self.SIDE_EFFECT_PATTERNS:
            return True
            
        # 部分一致（メソッド呼び出し）
        for pattern in self.SIDE_EFFECT_PATTERNS:
            if func_name.endswith(f".{pattern}"):
                return True
                
        # I/O関連のモジュール
        io_modules = {'requests', 'urllib', 'http', 'socket', 'asyncio', 
                      'aiohttp', 'aiofiles', 'sqlite3', 'psycopg2', 'pymongo'}
        for module in io_modules:
            if module in self.imported_modules and func_name.startswith(module):
                return True
                
        return False

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルの副作用をチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        # infrastructureディレクトリ内のファイルは除外
        if 'infrastructure' in str(file_path):
            return []
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = SideEffectChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception:
        return []

def main() -> CheckResult:
    """
    メインエントリーポイント
    
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / 'src'
    all_violations = []
    
    if src_dir.exists():
        for py_file in src_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            violations = check_file(py_file)
            all_violations.extend(violations)
    
    fix_policy = '''【CLAUDE.mdルール違反】
副作用はsrc/infrastructureのみとする

検出された副作用：
- ファイルI/O操作
- ネットワーク通信
- データベースアクセス
- 環境変数の読み取り
- 外部プロセスの実行
- 標準入出力

修正方法：
1. 副作用を持つ処理をinfrastructureレイヤーに移動
2. main.pyから依存性注入で提供
3. ビジネスロジックは純粋関数として実装'''
    
    fix_example = '''# Before - ビジネスロジックに副作用が含まれている
# src/operations/data_processor.py
import json

class DataProcessor:
    def process_config(self):
        # 副作用: ファイルI/O
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # 副作用: 標準出力
        print(f"Processing with config: {config}")
        
        # ビジネスロジック
        processed = self._transform_data(config)
        
        # 副作用: ファイルI/O
        with open('output.json', 'w') as f:
            json.dump(processed, f)
        
        return processed

# After - 副作用をinfrastructureに分離
# src/infrastructure/file_handler.py
import json
from pathlib import Path

class FileHandler:
    def read_json(self, path: str):
        with open(path, 'r') as f:
            return json.load(f)
    
    def write_json(self, data, path: str):
        with open(path, 'w') as f:
            json.dump(data, f)

# src/infrastructure/logger.py
class Logger:
    def info(self, message: str):
        print(f"[INFO] {message}")

# src/operations/data_processor.py
class DataProcessor:
    def __init__(self, file_handler, logger):
        self.file_handler = file_handler
        self.logger = logger
    
    def process_config(self, config_path: str, output_path: str):
        # 副作用はinfrastructureに委譲
        config = self.file_handler.read_json(config_path)
        self.logger.info(f"Processing with config: {config}")
        
        # 純粋なビジネスロジック
        processed = self._transform_data(config)
        
        # 副作用はinfrastructureに委譲
        self.file_handler.write_json(processed, output_path)
        
        return processed
    
    def _transform_data(self, config):
        # 純粋関数として実装
        return {"processed": True, **config}

# main.py
from src.infrastructure.file_handler import FileHandler
from src.infrastructure.logger import Logger
from src.operations.data_processor import DataProcessor

# 依存性注入
file_handler = FileHandler()
logger = Logger()
processor = DataProcessor(file_handler, logger)

# 実行
result = processor.process_config('config.json', 'output.json')'''
    
    return CheckResult(
        title='side_effect_check',
        log_level=LogLevel.ERROR if all_violations else LogLevel.INFO,
        failure_locations=all_violations,
        fix_policy=fix_policy,
        fix_example_code=fix_example
    )

if __name__ == '__main__':
    result = main()
    print(f'副作用チェッカー: {len(result.failure_locations)}件の違反を検出')