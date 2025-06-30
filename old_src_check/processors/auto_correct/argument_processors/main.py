"""
引数処理自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルの
引数・キーワード引数のデフォルト値を自動削除します。
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from models.check_result import CheckResult, FailureLocation, LogLevel

# 同じディレクトリのモジュールをインポート
sys.path.append(str(Path(__file__).parent))
from args_remover import ArgsRemover
from kwargs_remover import KwargsRemover


def main() -> CheckResult:
    """
    引数処理のメインエントリーポイント
        
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    # 設定を取得
    import os
    config = {
        'mode': 'both',  # 'args', 'kwargs', 'both'
        'dry_run': bool(os.environ.get('SRC_CHECK_DRY_RUN', False))
    }
    
    print(f"🔍 引数処理解析を開始: {src_dir}")
    print(f"モード: {config['mode']}")
    
    failure_locations = []
    fix_policies = []
    
    try:
        if config['mode'] in ['args', 'both']:
            # 引数のデフォルト値を削除
            args_result = _process_args(src_dir, config, print)
            failure_locations.extend(args_result.failure_locations)
            if args_result.fix_policy:
                fix_policies.append(args_result.fix_policy)
        
        if config['mode'] in ['kwargs', 'both']:
            # キーワード引数のデフォルト値を削除
            kwargs_result = _process_kwargs(src_dir, config, print)
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
            title="argument_processors",
            log_level=LogLevel.WARNING if failure_locations else LogLevel.INFO,
            failure_locations=failure_locations,
            fix_policy=fix_policy,
            fix_example_code=fix_example
        )
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            title="argument_processors_error",
            log_level=LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"引数処理中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


def _process_args(src_dir: Path, config: dict, print) -> CheckResult:
    """引数のデフォルト値を処理"""
    # args_remover.pyのmain関数を直接呼び出す
    from args_remover import main as args_main
    
    # 現在のディレクトリを保存
    original_cwd = os.getcwd()
    project_root = Path(__file__).parent.parent.parent.parent.parent
    
    try:
        # src_dirに移動
        os.chdir(project_root)
        result = args_main()
        return result
        
    except Exception as e:
        print(f"⚠️  引数処理中にエラー: {e}")
        return CheckResult(
            title="argument_processors_args_error",
            log_level=LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"引数処理中にエラー: {str(e)}",
            fix_example_code=None
        )
    finally:
        # ディレクトリを元に戻す
        os.chdir(original_cwd)


def _process_kwargs(src_dir: Path, config: dict, print) -> CheckResult:
    """キーワード引数のデフォルト値を処理"""
    # kwargs_remover.pyのmain関数を直接呼び出す
    from kwargs_remover import main as kwargs_main
    
    # 現在のディレクトリを保存
    original_cwd = os.getcwd()
    project_root = Path(__file__).parent.parent.parent.parent.parent
    
    try:
        # src_dirに移動
        os.chdir(project_root)
        result = kwargs_main()
        return result
        
    except Exception as e:
        print(f"⚠️  キーワード引数処理中にエラー: {e}")
        return CheckResult(
            title="argument_processors_kwargs_error",
            log_level=LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"キーワード引数処理中にエラー: {str(e)}",
            fix_example_code=None
        )
    finally:
        # ディレクトリを元に戻す
        os.chdir(original_cwd)




if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\nCheckResult: {len(result.failure_locations)} default values found")