"""壊れたインポートと循環インポートをチェックするルール"""
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict

# src_checkのモデルをインポート
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation


def get_imports_from_file(file_path: Path) -> List[Tuple[str, int]]:
    """ファイルからインポート文を抽出"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module, node.lineno))
    except:
        pass
    
    return imports


def check_import_exists(module_name: str, file_path: Path) -> bool:
    """インポートが存在するかチェック（簡易版）"""
    # 標準ライブラリまたはインストール済みパッケージ
    try:
        __import__(module_name.split('.')[0])
        return True
    except ImportError:
        pass
    
    # プロジェクト内のモジュールをチェック
    project_root = Path(__file__).parent.parent.parent
    
    # src.xxx 形式のインポートをチェック
    if module_name.startswith('src.'):
        # src.application.xxx -> src/application/xxx.py または src/application/xxx/__init__.py
        parts = module_name.split('.')[1:]  # 'src.'を除去
        
        # ファイルパスを構築
        file_path1 = project_root / 'src'
        for part in parts[:-1]:
            file_path1 = file_path1 / part
        
        # モジュールファイルか__init__.pyをチェック
        module_file = file_path1 / f"{parts[-1]}.py"
        init_file = file_path1 / parts[-1] / "__init__.py"
        
        return module_file.exists() or init_file.exists()
    
    return False


def detect_circular_imports(project_root: Path) -> List[List[Path]]:
    """簡易的な循環インポート検出"""
    import_graph = defaultdict(set)
    
    # Pythonファイルを収集
    py_files = []
    for pattern in ['src/**/*.py']:
        py_files.extend(project_root.glob(pattern))
    
    # インポートグラフを構築
    for file_path in py_files:
        if '__pycache__' in str(file_path) or 'src_check' in str(file_path):
            continue
            
        imports = get_imports_from_file(file_path)
        for module_name, _ in imports:
            # srcから始まるインポートのみを対象とする
            if module_name.startswith('src'):
                import_graph[str(file_path)].add(module_name)
    
    # 簡易的な循環検出（2ファイル間の相互参照のみ）
    cycles = []
    checked = set()
    
    for file1, imports1 in import_graph.items():
        for file2, imports2 in import_graph.items():
            if file1 >= file2:
                continue
            
            # file1がfile2をインポートし、file2がfile1をインポートしているかチェック
            file1_module = Path(file1).stem
            file2_module = Path(file2).stem
            
            if any(file2_module in imp for imp in imports1) and any(file1_module in imp for imp in imports2):
                cycles.append([Path(file1), Path(file2)])
    
    return cycles


def main() -> CheckResult:
    """壊れたインポートと循環インポートをチェック"""
    
    project_root = Path(__file__).parent.parent.parent
    failure_locations = []
    
    # src配下のPythonファイルをチェック
    src_dir = project_root / 'src'
    if not src_dir.exists():
        return CheckResult(
            failure_locations=[],
            fix_policy="srcディレクトリが見つかりません",
            fix_example_code=None
        )
    
    broken_imports_count = 0
    files_checked = 0
    
    # 壊れたインポートをチェック
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        files_checked += 1
        imports = get_imports_from_file(py_file)
        
        for module_name, line_number in imports:
            # src内部のインポートのみチェック
            if not module_name.startswith('src'):
                continue
                
            if not check_import_exists(module_name, py_file):
                failure_locations.append(
                    FailureLocation(
                        file_path=str(py_file),
                        line_number=line_number
                    )
                )
                broken_imports_count += 1
    
    # 循環インポートを検出
    cycles = detect_circular_imports(project_root)
    circular_imports_count = len(cycles)
    
    # 循環インポートをfailure_locationsに追加
    for cycle in cycles:
        if cycle:
            failure_locations.append(
                FailureLocation(
                    file_path=str(cycle[0]),
                    line_number=1
                )
            )
    
    # 修正方針を作成
    fix_policy_parts = []
    
    if broken_imports_count > 0:
        fix_policy_parts.append(
            f"{broken_imports_count}個の壊れたインポートが見つかりました。\n"
            "インポートパスを確認し、正しいモジュール名に修正してください。"
        )
    
    if circular_imports_count > 0:
        fix_policy_parts.append(
            f"{circular_imports_count}個の循環インポートが見つかりました。\n"
            "循環インポートを解消するには:\n"
            "  1. 共通の依存関係を別モジュールに抽出\n"
            "  2. インポートを関数内に移動（遅延インポート）\n"
            "  3. 型ヒントのみの場合はTYPE_CHECKINGを使用"
        )
    
    fix_policy = "\n\n".join(fix_policy_parts) if fix_policy_parts else "問題は見つかりませんでした。"
    
    # デバッグ情報
    print(f"チェックしたファイル数: {files_checked}")
    print(f"壊れたインポート: {broken_imports_count}件")
    print(f"循環インポート: {circular_imports_count}件")
    
    return CheckResult(
        failure_locations=failure_locations,
        fix_policy=fix_policy,
        fix_example_code=None
    )


if __name__ == "__main__":
    result = main()
    print(f"\n結果: {len(result.failure_locations)}件の問題が見つかりました")
    if result.fix_policy:
        print(f"\n修正方針:\n{result.fix_policy}")