"""
動的インポート管理モジュール
main.pyファイルを動的にインポートし、実行する
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult, LogLevel


class DynamicImporter:
    """動的インポート管理クラス"""
    
    def __init__(self, project_root: Path, min_log_level: LogLevel = LogLevel.ERROR):
        self.project_root = project_root
        self.min_log_level = min_log_level
    
    def import_and_execute(self, module_path: Path, module_name: str) -> CheckResult:
        """
        main.pyを動的にインポートして実行
        失敗時は適切なCheckResultを返す
        """
        # 標準出力を一時的に抑制
        import io
        original_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # モジュール仕様を作成
            spec = importlib.util.spec_from_file_location(
                f"dynamic_{module_name}", 
                module_path
            )
            
            if spec is None or spec.loader is None:
                return self._create_failure_result(
                    module_name,
                    f"モジュール仕様の作成に失敗: {module_path}"
                )
            
            # モジュールをインポート
            module = importlib.util.module_from_spec(spec)
            
            # sys.modulesに追加（一時的）
            module_key = f"dynamic_{module_name}_{id(module)}"
            sys.modules[module_key] = module
            
            try:
                # モジュールを実行
                spec.loader.exec_module(module)
                
                # main関数を探して実行
                result = self._execute_main_function(module, module_name)
                
                return result
                
            finally:
                # sys.modulesから削除（クリーンアップ）
                if module_key in sys.modules:
                    del sys.modules[module_key]
                    
        except ImportError as e:
            # インポートエラーの詳細を標準出力に表示（CRITICALレベル）
            sys.stdout = original_stdout
            captured = captured_output.getvalue()
            if self.min_log_level.value <= LogLevel.CRITICAL.value:
                if captured:
                    print(f"\n⚠️  {module_name} の実行中に出力がありました:")
                    print(captured)
                print(f"\n❌ {module_name} でインポートエラーが発生しました: {str(e)}")
            sys.stdout = captured_output
            
            return self._create_failure_result(
                module_name,
                f"インポートエラー: {str(e)}"
            )
        except Exception as e:
            # その他のエラーも標準出力に表示（ERRORレベル）
            sys.stdout = original_stdout
            captured = captured_output.getvalue()
            if self.min_log_level.value <= LogLevel.ERROR.value:
                if captured:
                    print(f"\n⚠️  {module_name} の実行中に出力がありました:")
                    print(captured)
                print(f"\n❌ {module_name} で実行時エラーが発生しました: {str(e)}")
            sys.stdout = captured_output
            
            return self._create_failure_result(
                module_name,
                f"実行時エラー: {str(e)}"
            )
        finally:
            # 標準出力を復元
            sys.stdout = original_stdout
            captured = captured_output.getvalue()
            if captured and "ERROR" not in module_name and self.min_log_level.value <= LogLevel.DEBUG.value:
                # DEBUGレベル以下の場合のみ正常終了時の出力を表示
                print(f"\n📝 {module_name} の出力:")
                print(captured)
    
    def _execute_main_function(self, module: Any, module_name: str) -> CheckResult:
        """
        モジュールのmain関数を実行
        """
        # main関数を探す
        if hasattr(module, 'main') and callable(module.main):
            try:
                result = module.main()
                
                # CheckResultでない場合は適切な形式に変換
                if not isinstance(result, CheckResult):
                    return self._create_success_result(
                        module_name,
                        f"実行完了（戻り値: {type(result).__name__}）"
                    )
                
                # titleが設定されていない場合は設定
                if not hasattr(result, 'title') or not result.title:
                    # CheckResultを再作成（frozenのため）
                    return CheckResult(
                        title=module_name,
                        log_level=result.log_level if hasattr(result, 'log_level') else LogLevel.WARNING,
                        failure_locations=result.failure_locations,
                        fix_policy=result.fix_policy,
                        fix_example_code=result.fix_example_code
                    )
                
                return result
                
            except Exception as e:
                return self._create_failure_result(
                    module_name,
                    f"main関数実行エラー: {str(e)}"
                )
        else:
            return self._create_failure_result(
                module_name,
                "main関数が見つかりません"
            )
    
    def _create_failure_result(self, module_name: str, error_message: str) -> CheckResult:
        """失敗時のCheckResultを作成"""
        # testsからのインポートエラーなど重大なエラーを判定
        is_critical = 'tests' in error_message or 'No module named' in error_message
        
        return CheckResult(
            title=f"{module_name}_ERROR",
            log_level=LogLevel.CRITICAL if is_critical else LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"実行失敗: {error_message}",
            fix_example_code=None
        )
    
    def _create_success_result(self, module_name: str, message: str) -> CheckResult:
        """成功時のCheckResultを作成"""
        return CheckResult(
            title=module_name,
            log_level=LogLevel.INFO,
            failure_locations=[],
            fix_policy=message,
            fix_example_code=None
        )
    
    def validate_main_function(self, module_path: Path) -> bool:
        """
        main.pyにmain関数が存在するかチェック（実行せずに）
        """
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 簡易的なmain関数の存在チェック
            return 'def main(' in content or 'def main():' in content
            
        except Exception:
            return False