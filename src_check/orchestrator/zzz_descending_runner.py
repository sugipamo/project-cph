"""
降順実行ランナー - 辞書順で最後のファイル（zzzプレフィックスで最後に配置）
"""

from pathlib import Path
import sys

# src_checkをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src_check.orchestrator.check_executor import CheckExecutor
from src_check.core.result_writer import ResultWriter


def run_descending():
    """降順（Z→A）で全チェックを実行"""
    project_root = Path(__file__).parent.parent.parent
    
    print("🔄 降順実行モードで品質チェックを開始します...")
    
    # チェック実行
    executor = CheckExecutor(project_root)
    results = executor.execute_all(ascending=False)
    
    # 結果を保存
    writer = ResultWriter(project_root / "src_check" / "check_result")
    writer.write_all_results(results)
    
    print("✅ 降順実行が完了しました")
    return results


if __name__ == "__main__":
    run_descending()