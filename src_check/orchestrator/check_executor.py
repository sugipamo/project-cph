"""
チェック実行エンジン - 登録されたモジュールを実行
"""

import importlib.util
import sys
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.check_result import CheckResult, FailureLocation
from .module_registry import ModuleRegistry, CheckModule


class CheckExecutor:
    """チェックモジュールの実行を管理"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_check_path = project_root / "src_check"
        self.registry = ModuleRegistry(self.src_check_path)
        self.results: Dict[str, CheckResult] = {}
    
    def execute_all(self, ascending: bool = True) -> Dict[str, CheckResult]:
        """全モジュールを実行"""
        modules = self.registry.get_modules_sorted(reverse=not ascending)
        
        print(f"\n{'='*60}")
        print(f"実行モード: {'昇順' if ascending else '降順'}")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"モジュール数: {len(modules)}")
        print(f"{'='*60}\n")
        
        for i, module in enumerate(modules, 1):
            print(f"[{i}/{len(modules)}] {module.name} を実行中...")
            result = self._execute_module(module)
            self.results[module.name] = result
            
            if result.failure_locations:
                print(f"  → 検出: {len(result.failure_locations)}件")
            else:
                print(f"  → OK")
        
        self._print_summary()
        return self.results
    
    def execute_specific(self, module_names: List[str]) -> Dict[str, CheckResult]:
        """特定のモジュールのみ実行"""
        results = {}
        
        for name in module_names:
            module = self.registry.get_module(name)
            if module:
                print(f"実行中: {name}")
                result = self._execute_module(module)
                results[name] = result
            else:
                print(f"警告: モジュール '{name}' が見つかりません")
        
        return results
    
    def _execute_module(self, module: CheckModule) -> CheckResult:
        """個別モジュールを実行"""
        # 標準出力を抑制
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # モジュールを動的にインポート
            spec = importlib.util.spec_from_file_location(
                f"check_module_{module.name}",
                module.path
            )
            
            if spec is None or spec.loader is None:
                return self._create_error_result(
                    module.name,
                    "モジュール仕様の作成に失敗"
                )
            
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # main関数を実行
            if hasattr(mod, 'main') and callable(mod.main):
                result = mod.main()
                
                # CheckResultでない場合はエラー
                if not isinstance(result, CheckResult):
                    return self._create_error_result(
                        module.name,
                        f"不正な戻り値: {type(result).__name__}"
                    )
                
                return result
            else:
                return self._create_error_result(
                    module.name,
                    "main関数が見つかりません"
                )
                
        except Exception as e:
            return self._create_error_result(
                module.name,
                f"実行エラー: {str(e)}"
            )
        finally:
            # 標準出力を復元
            sys.stdout = original_stdout
    
    def _create_error_result(self, module_name: str, error_msg: str) -> CheckResult:
        """エラー時のCheckResult作成"""
        return CheckResult(
            title=f"{module_name}_ERROR",
            failure_locations=[],
            fix_policy=f"実行失敗: {error_msg}",
            fix_example_code=None
        )
    
    def _print_summary(self):
        """実行結果のサマリーを表示"""
        total_modules = len(self.results)
        failed_modules = sum(1 for r in self.results.values() if r.failure_locations)
        total_failures = sum(len(r.failure_locations) for r in self.results.values())
        
        print(f"\n{'='*60}")
        print("実行結果サマリー")
        print(f"{'='*60}")
        print(f"実行モジュール数: {total_modules}")
        print(f"問題検出モジュール数: {failed_modules}")
        print(f"総検出件数: {total_failures}")
        print(f"{'='*60}\n")