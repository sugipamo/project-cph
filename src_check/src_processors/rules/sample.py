"""
品質チェックルールのサンプル実装

このファイルは新しい品質チェックルールを作成する際のテンプレートとして使用してください。

## ルール作成の手順

1. このファイルをコピーして新しいルール名でファイルを作成
2. チェック内容に応じて実装を修正
3. main()関数が必ずCheckResultを返すようにする
4. test.pyを実行してルールが正しく動作することを確認

## 命名規則

- ファイル名: xxx_checker.py （例: import_checker.py, naming_checker.py）
- クラス名: XxxChecker （例: ImportChecker, NamingChecker）

## 実装のポイント

- astモジュールを使用してPythonコードを解析
- 違反箇所はFailureLocationで正確な位置を記録
- 修正方針と修正例は具体的かつ実践的に記述
- エラーが発生しても他のファイルのチェックを継続
"""
import ast
from pathlib import Path
from typing import List
import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, FailureLocation

class SampleChecker(ast.NodeVisitor):
    """
    ASTノードを訪問してチェックを実行するクラス
    
    継承して以下のvisit_Xxxメソッドをオーバーライドします：
    - visit_FunctionDef: 関数定義をチェック
    - visit_ClassDef: クラス定義をチェック
    - visit_Import: import文をチェック
    - visit_Call: 関数呼び出しをチェック
    - その他: https://docs.python.org/3/library/ast.html 参照
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_Pass(self, node):
        """
        例: pass文を検出する（実際のルールでは適切なノードタイプを使用）
        """
        self.violations.append(FailureLocation(file_path=self.file_path, line_number=node.lineno))
        self.generic_visit(node)

def check_file(file_path: Path) -> List[FailureLocation]:
    """
    単一ファイルをチェックする
    
    Args:
        file_path: チェック対象のファイルパス
    
    Returns:
        違反箇所のリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content, filename=str(file_path))
        checker = SampleChecker(str(file_path))
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception as e:
        return []

def main(di_container) -> CheckResult:
    """
    メインエントリーポイント
    
    このルールのメイン処理を実装します。
    必ずCheckResultインスタンスを返してください。
    
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
    fix_policy = 'pass文を実際の処理に置き換えてください。TODOコメントを追加して後で実装する場合は、具体的な実装内容を記載してください。'
    fix_example = '# Before\ndef process_data(data):\n    pass\n\n# After - 実装予定の場合\ndef process_data(data):\n    # TODO: データの検証とクリーニング処理を実装\n    raise NotImplementedError("process_data is not implemented yet")\n\n# After - 空の処理が意図的な場合\ndef process_data(data):\n    # 特定の条件下では処理不要\n    return'
    return CheckResult(failure_locations=all_violations, fix_policy=fix_policy, fix_example_code=fix_example)
if __name__ == '__main__':
    result = main()
    print(f'サンプルチェッカー: {len(result.failure_locations)}件の違反を検出')
    if result.failure_locations:
        print('\n違反箇所:')
        for location in result.failure_locations[:5]:
            print(f'  - {location.file_path}:{location.line_number}')
        if len(result.failure_locations) > 5:
            print(f'  ... 他 {len(result.failure_locations) - 5} 件')