"""
型ヒント自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルに
型ヒントを自動追加します。
"""

import sys
from pathlib import Path
from typing import List

# パスを追加
sys.path.append(str(Path(__file__).parent.parent))

from models.check_result import CheckResult, FailureLocation
# パスを追加してインポート
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
    
    for py_file in directory.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        try:
            # 型ヒントを追加
            was_modified = adder.add_type_hints_to_file(py_file)
            
            if was_modified:
                # 修正されたファイルを記録
                processed_files.append(FailureLocation(
                    file_path=str(py_file),
                    line_number=1  # ファイル全体の修正を示すため1行目
                ))
        
        except Exception as e:
            # エラーが発生したファイルをスキップ
            print(f"警告: {py_file} の処理中にエラー: {e}")
            continue
    
    return processed_files


def main() -> CheckResult:
    """
    型ヒント自動修正のメインエントリーポイント
    
    Returns:
        CheckResult: 処理結果
    """
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"
    
    adder = TypeHintAdder()
    
    # src配下のファイルを処理
    processed_files = process_directory(src_dir, adder)
    
    # 修正サマリを取得
    modifications = adder.get_modification_summary()
    
    # 修正内容の詳細を構築
    fix_policy = """【型ヒント自動追加】
関数の引数名と使用パターンから型を推論し、型ヒントを自動追加しました。
推論できなかった型については手動で追加してください。
CLAUDE.mdルールに従い、デフォルト値やNone、*args、**kwargsは使用していません。"""
    
    # 修正例を構築
    fix_example = ""
    if modifications:
        fix_example = "【修正された関数の例】\n"
        for i, mod in enumerate(modifications[:3]):  # 最大3例まで表示
            fix_example += f"\n{mod['file']}:{mod['line']} - {mod['function']}()\n"
            if mod['added_types']:
                for param, ptype in mod['added_types'].items():
                    fix_example += f"  引数 {param}: {ptype}\n"
            if mod['return_type']:
                fix_example += f"  戻り値: {mod['return_type']}\n"
        
        if len(modifications) > 3:
            fix_example += f"\n他 {len(modifications) - 3} 件の関数が修正されました。"
    
    return CheckResult(
        failure_locations=processed_files,
        fix_policy=fix_policy,
        fix_example_code=fix_example if fix_example else None
    )


if __name__ == "__main__":
    result = main()
    print(f"型ヒント自動修正: {len(result.failure_locations)}ファイルを処理しました")