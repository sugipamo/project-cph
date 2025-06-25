"""
型ヒント自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルに
型ヒントを自動追加します。
"""
import sys
from pathlib import Path
from typing import List
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation
sys.path.append(str(Path(__file__).parent))
from type_hint_adder import TypeHintAdder

def process_directory(directory: Path, adder: TypeHintAdder) -> List[FailureLocation]:
    """
    ディレクトリ内のPythonファイルを処理
    
    Args:
        directory: 処理対象ディレクトリ
        adder: 型ヒント追加器
        
    Returns:
        処理されたファイルの情報
    """
    processed_files = []
    if not directory.exists():
        return processed_files
    for py_file in directory.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        try:
            was_modified = adder.add_type_hints_to_file(py_file)
            if was_modified:
                processed_files.append(FailureLocation(file_path=str(py_file), line_number=1))
        except Exception as e:
            logger(f'警告: {py_file} の処理中にエラー: {e}')
            continue
    return processed_files

def main(di_container) -> CheckResult:
    """
    型ヒント自動修正のメインエントリーポイント
    
    Returns:
        CheckResult: 処理結果
    """
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / 'src'
    adder = TypeHintAdder()
    processed_files = process_directory(src_dir, adder)
    modifications = adder.get_modification_summary()
    fix_policy = '【型ヒント自動追加】\n関数の引数名と使用パターンから型を推論し、型ヒントを自動追加しました。\n推論できなかった型については手動で追加してください。'
    fix_example = ''
    if modifications:
        fix_example = '【修正された関数の例】\n'
        for i, mod in enumerate(modifications[:3]):
            fix_example += f'\n{mod['file']}:{mod['line']} - {mod['function']}()\n'
            if mod['added_types']:
                for param, ptype in mod['added_types'].items():
                    fix_example += f'  引数 {param}: {ptype}\n'
            if mod['return_type']:
                fix_example += f'  戻り値: {mod['return_type']}\n'
        if len(modifications) > 3:
            fix_example += f'\n他 {len(modifications) - 3} 件の関数が修正されました。'
    return CheckResult(failure_locations=processed_files, fix_policy=fix_policy, fix_example_code=fix_example if fix_example else None)
if __name__ == '__main__':
    result = main()
    logger(f'型ヒント自動修正: {len(result.failure_locations)}ファイルを処理しました')