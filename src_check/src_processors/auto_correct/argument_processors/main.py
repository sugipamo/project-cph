"""
引数処理自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルの
引数・キーワード引数のデフォルト値を自動削除します。
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src_check.models.check_result import CheckResult, FailureLocation

# 同じディレクトリのモジュールをインポート
from .args_remover import ArgsRemover
from .kwargs_remover import KwargsRemover


def main(di_container) -> CheckResult:
    """
    引数処理のメインエントリーポイント
    
    Args:
        di_container: DIコンテナ
        logger: ロガー関数
        
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    # 設定を取得
    config = {
        'mode': 'both',  # 'args', 'kwargs', 'both'
        'dry_run': True
    }
    
    logger(f"🔍 引数処理解析を開始: {src_dir}")
    logger(f"モード: {config['mode']}")
    
    failure_locations = []
    fix_policies = []
    
    try:
        if config['mode'] in ['args', 'both']:
            # 引数のデフォルト値を削除
            args_result = _process_args(src_dir, config, logger)
            failure_locations.extend(args_result.failure_locations)
            if args_result.fix_policy:
                fix_policies.append(args_result.fix_policy)
        
        if config['mode'] in ['kwargs', 'both']:
            # キーワード引数のデフォルト値を削除
            kwargs_result = _process_kwargs(src_dir, config, logger)
            failure_locations.extend(kwargs_result.failure_locations)
            if kwargs_result.fix_policy:
                fix_policies.append(kwargs_result.fix_policy)
        
        # 結果を統合
        if failure_locations:
            fix_policy = "\n".join(fix_policies)
            fix_example = (
                "# 修正前:\n"
                "def func(arg1='default', arg2=None):\n"
                "    pass\n\n"
                "# 修正後:\n"
                "def func(arg1, arg2):\n"
                "    pass"
            )
        else:
            fix_policy = "引数のデフォルト値は検出されませんでした。"
            fix_example = None
        
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=fix_example
        )
        
    except Exception as e:
        logger(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            failure_locations=[],
            fix_policy=f"引数処理中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


def _process_args(src_dir: Path, config: dict, logger) -> CheckResult:
    """引数のデフォルト値を処理"""
    remover = ArgsRemover(dry_run=config['dry_run'])
    failures = []
    
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified, locations = remover.remove_defaults(content, str(py_file))
            
            if locations:
                failures.extend(locations)
                
                if not config['dry_run'] and modified != content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(modified)
                    logger(f"✏️  修正: {py_file}")
                    
        except Exception as e:
            logger(f"⚠️  {py_file}の処理中にエラー: {e}")
    
    if failures:
        return CheckResult(
            failure_locations=failures,
            fix_policy=f"{len(failures)}個の引数デフォルト値が検出されました。",
            fix_example_code=None
        )
    else:
        return CheckResult(
            failure_locations=[],
            fix_policy="",
            fix_example_code=None
        )


def _process_kwargs(src_dir: Path, config: dict, logger) -> CheckResult:
    """キーワード引数のデフォルト値を処理"""
    remover = KwargsRemover(dry_run=config['dry_run'])
    failures = []
    
    for py_file in src_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified, locations = remover.remove_defaults(content, str(py_file))
            
            if locations:
                failures.extend(locations)
                
                if not config['dry_run'] and modified != content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(modified)
                    logger(f"✏️  修正: {py_file}")
                    
        except Exception as e:
            logger(f"⚠️  {py_file}の処理中にエラー: {e}")
    
    if failures:
        return CheckResult(
            failure_locations=failures,
            fix_policy=f"{len(failures)}個のキーワード引数デフォルト値が検出されました。",
            fix_example_code=None
        )
    else:
        return CheckResult(
            failure_locations=[],
            fix_policy="",
            fix_example_code=None
        )




if __name__ == "__main__":
    # テスト実行
    result = main(None)
    print(f"\nCheckResult: {len(result.failure_locations)} default values found")