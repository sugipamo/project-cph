import sys
import os
from pathlib import Path
import time

# src_checkディレクトリをsys.pathに追加（既存パターンに合わせる）
src_check_dir = Path(__file__).parent.parent.parent.parent  # src_checkディレクトリ
sys.path.insert(0, str(src_check_dir))

from models.check_result import CheckResult, FailureLocation

# 現在のディレクトリをパスに追加してローカルモジュールをインポート
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from simple_import_analyzer import SimpleImportAnalyzer
from dependency_calculator import DependencyCalculator

def main() -> CheckResult:
    """
    インポート依存関係ベースフォルダ構造整理のプロトタイプ
    MVP: 小規模ファイルでの動作確認とパフォーマンス測定
    """
    start_time = time.time()
    
    try:
        # プロジェクトルート設定
        project_root = Path(__file__).parent.parent.parent.parent.parent
        src_root = project_root / "src"
        
        print(f"プロジェクトルート: {project_root}")
        print(f"解析対象: {src_root}")
        
        if not src_root.exists():
            return CheckResult(
                failure_locations=[FailureLocation(file_path="system", line_number=0)],
                fix_policy="src/ディレクトリが見つかりません",
                fix_example_code=None
            )
        
        # ファイル数チェック
        python_files = list(src_root.rglob("*.py"))
        file_count = len(python_files)
        
        print(f"発見されたPythonファイル数: {file_count}")
        
        # MVP制限: 50ファイル以下
        if file_count > 50:
            return CheckResult(
                failure_locations=[FailureLocation(file_path="system", line_number=0)],
                fix_policy=f"ファイル数が多すぎます ({file_count}ファイル)。MVPでは50ファイル以下で実行してください",
                fix_example_code=None
            )
        
        if file_count == 0:
            return CheckResult(
                failure_locations=[],
                fix_policy="Pythonファイルが見つかりませんでした",
                fix_example_code=None
            )
        
        # Git状態確認（簡易版）
        git_dir = project_root / ".git"
        if not git_dir.exists():
            print("警告: Gitリポジトリではありません。バックアップを手動で作成してください")
        
        # インポート解析開始
        print("\nインポート解析を開始...")
        analyzer = SimpleImportAnalyzer(src_root)
        analysis_start = time.time()
        
        analyzer.analyze_all_files()
        
        analysis_time = time.time() - analysis_start
        print(f"解析時間: {analysis_time:.2f}秒")
        
        # 解析結果の表示
        total_imports = sum(len(imports) for imports in analyzer.file_imports.values())
        print(f"総インポート文数: {total_imports}")
        
        # 依存関係計算
        print("\n依存関係を計算中...")
        calc_start = time.time()
        
        calculator = DependencyCalculator(analyzer)
        depth_map = calculator.calculate_dependency_depths(max_depth=4)
        
        calc_time = time.time() - calc_start
        print(f"計算時間: {calc_time:.2f}秒")
        
        # 結果サマリー
        if not depth_map:
            return CheckResult(
                failure_locations=[],
                fix_policy="依存関係が検出されませんでした",
                fix_example_code=None
            )
        
        depth_summary = {}
        for file_path, depth in depth_map.items():
            depth_summary[depth] = depth_summary.get(depth, 0) + 1
        
        print(f"\n深度別ファイル数:")
        for depth in sorted(depth_summary.keys()):
            print(f"  深度{depth}: {depth_summary[depth]}ファイル")
        
        # 移動計画のシミュレーション
        move_plan = _create_simple_move_plan(depth_map, src_root)
        
        total_time = time.time() - start_time
        print(f"\n総実行時間: {total_time:.2f}秒")
        
        # 循環依存チェック
        circular_deps = calculator.detect_circular_dependencies()
        if circular_deps:
            failures = []
            for cycle in circular_deps:
                failures.append(FailureLocation(
                    file_path=str(cycle[0]) if cycle else "unknown",
                    line_number=0
                ))
            
            return CheckResult(
                failure_locations=failures,
                fix_policy=f"循環依存が検出されました: {len(circular_deps)}個のサイクル",
                fix_example_code=None
            )
        
        return CheckResult(
            failure_locations=[],
            fix_policy=f"プロトタイプ解析完了: {len(move_plan)}ファイルの移動を計画 (実行時間: {total_time:.2f}秒)",
            fix_example_code=None
        )
        
    except Exception as e:
        return CheckResult(
            failure_locations=[FailureLocation(file_path="system", line_number=0)],
            fix_policy=f"プロトタイプ実行エラー: {str(e)}",
            fix_example_code=None
        )

def _create_simple_move_plan(depth_map: dict, src_root: Path) -> dict:
    """シンプルな移動計画作成（実際の移動は行わない）"""
    move_plan = {}
    
    for file_path, depth in depth_map.items():
        if depth == 0:
            # 深度0はsrc直下（移動不要）
            continue
        
        # 深度に応じたフォルダ構造
        folder_name = file_path.stem
        new_path = src_root
        
        for i in range(depth):
            new_path = new_path / f"level_{i+1}"
        
        new_path = new_path / folder_name / file_path.name
        
        if new_path != file_path:
            move_plan[file_path] = new_path
            print(f"  計画: {file_path.relative_to(src_root)} -> {new_path.relative_to(src_root)}")
    
    return move_plan

if __name__ == "__main__":
    result = main()
    print(f"\n結果: {result.fix_policy}")
    if result.failure_locations:
        print(f"失敗箇所: {len(result.failure_locations)}件")