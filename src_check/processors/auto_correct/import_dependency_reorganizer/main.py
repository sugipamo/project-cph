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
from import_updater_v3 import ImportUpdaterV3
from file_mover import FileMover
from syntax_validator import SyntaxValidator

def main() -> CheckResult:
    """
    インポート依存関係ベースフォルダ構造整理
    src_check/main.pyから呼び出されるエントリーポイント
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
                title="import_dependency_reorganizer",
                failure_locations=[FailureLocation(file_path="system", line_number=0)],
                fix_policy="src/ディレクトリが見つかりません",
                fix_example_code=None
            )
        
        # ファイル数チェック
        python_files = list(src_root.rglob("*.py"))
        file_count = len(python_files)
        
        print(f"発見されたPythonファイル数: {file_count}")
        
        # 制限: 250ファイル以下（実用版）
        if file_count > 250:
            return CheckResult(
                title="import_dependency_reorganizer",
                failure_locations=[FailureLocation(file_path="system", line_number=0)],
                fix_policy=f"ファイル数が多すぎます ({file_count}ファイル)。250ファイル以下で実行してください",
                fix_example_code=None
            )
        
        if file_count == 0:
            return CheckResult(
                title="import_dependency_reorganizer",
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
                title="import_dependency_reorganizer",
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
        move_plan = _create_enhanced_move_plan(depth_map, src_root, analyzer)
        
        total_time = time.time() - start_time
        print(f"\n総実行時間: {total_time:.2f}秒")
        
        # 循環依存チェック
        circular_deps = calculator.detect_circular_dependencies()
        
        # デバッグ：format_info関連の依存関係を確認
        print("\nformat_info関連の依存関係:")
        for file_path, imports in analyzer.file_imports.items():
            if "format_info" in str(file_path):
                print(f"  {file_path.name}: {imports}")
        
        if circular_deps:
            failures = []
            for cycle in circular_deps:
                failures.append(FailureLocation(
                    file_path=str(cycle[0]) if cycle else "unknown",
                    line_number=0
                ))
            
            return CheckResult(
                title="import_dependency_reorganizer",
                failure_locations=failures,
                fix_policy=f"循環依存が検出されました: {len(circular_deps)}個のサイクル",
                fix_example_code=None
            )
        
        # ファイル移動が必要な場合はFailureLocationとして報告
        if move_plan:
            failures = []
            for old_path, new_path in move_plan.items():
                rel_path = old_path.relative_to(src_root)
                failures.append(FailureLocation(
                    file_path=str(rel_path),
                    line_number=0
                ))
            
            fix_policy = f"{len(move_plan)}個のファイルを依存関係の深度に基づいて再配置します。\n\n"
            fix_policy += "深度別の移動計画:\n"
            
            # 深度別に集計
            depth_moves = {}
            for file_path, new_path in move_plan.items():
                depth = depth_map.get(file_path, 0)
                if depth not in depth_moves:
                    depth_moves[depth] = 0
                depth_moves[depth] += 1
            
            for depth in sorted(depth_moves.keys()):
                fix_policy += f"  深度{depth}: {depth_moves[depth]}ファイル\n"
            
            fix_example = (
                "# 実際に移動を実行するには:\n"
                "python3 -m src_check.processors.auto_correct.import_dependency_reorganizer.main_v2 --execute\n\n"
                "# 設定ファイルを作成して詳細なオプションを指定:\n"
                "python3 -m src_check.processors.auto_correct.import_dependency_reorganizer.main_v2 --generate-config"
            )
            
            return CheckResult(
                title="import_dependency_reorganizer",
                failure_locations=failures,
                fix_policy=fix_policy,
                fix_example_code=fix_example
            )
        
        # 移動不要の場合
        return CheckResult(
            title="import_dependency_reorganizer",
            failure_locations=[],
            fix_policy="現在のフォルダ構造は依存関係に基づいて適切に配置されています。",
            fix_example_code=None
        )
        
    except Exception as e:
        return CheckResult(
            title="import_dependency_reorganizer",
            failure_locations=[FailureLocation(file_path="system", line_number=0)],
            fix_policy=f"プロトタイプ実行エラー: {str(e)}",
            fix_example_code=None
        )

def _create_enhanced_move_plan(depth_map: dict, src_root: Path, analyzer) -> dict:
    """詳細な移動計画作成（依存関係情報付き）"""
    move_plan = {}
    
    print(f"\n📋 ファイル移動計画の詳細:")
    
    # 深度別にグループ化
    depth_groups = {}
    for file_path, depth in depth_map.items():
        if depth not in depth_groups:
            depth_groups[depth] = []
        depth_groups[depth].append(file_path)
    
    for depth in sorted(depth_groups.keys()):
        files = depth_groups[depth]
        print(f"\n  🏗️  深度{depth} ({len(files)}ファイル):")
        
        if depth == 0:
            print(f"    📌 src/直下に配置（移動不要）")
            for file_path in files[:3]:  # 最初の3個だけ表示
                rel_path = file_path.relative_to(src_root)
                deps = analyzer.get_dependencies(file_path)
                print(f"      • {rel_path} (依存: {len(deps)}個)")
            if len(files) > 3:
                print(f"      ... 他{len(files)-3}ファイル")
            continue
        
        # 深度1以上のファイルの移動計画
        for file_path in files:
            # より意味のあるフォルダ名を生成
            folder_name = _generate_meaningful_folder_name(file_path, depth)
            new_path = _calculate_new_path(src_root, folder_name, depth, file_path)
            
            if new_path != file_path:
                move_plan[file_path] = new_path
                rel_old = file_path.relative_to(src_root)
                rel_new = new_path.relative_to(src_root)
                deps = analyzer.get_dependencies(file_path)
                dependents = analyzer.get_dependents(analyzer.path_to_module_name(file_path))
                
                print(f"      📦 {rel_old}")
                print(f"         → {rel_new}")
                print(f"         依存: {len(deps)}個, 被依存: {len(dependents)}個")
                
                # 主要な依存関係を表示
                if deps:
                    main_deps = [dep for dep in deps[:2]]  # 最初の2個
                    print(f"         主要依存: {', '.join(main_deps)}")
    
    return move_plan

def _generate_meaningful_folder_name(file_path: Path, depth: int) -> str:
    """ファイルの特性に基づいて意味のあるフォルダ名を生成"""
    filename = file_path.stem
    
    # 特定パターンのファイル名から意味を抽出
    if filename.endswith('_manager'):
        return filename.replace('_manager', '_mgmt')
    elif filename.endswith('_service'):
        return filename.replace('_service', '_svc')
    elif filename.endswith('_handler'):
        return filename.replace('_handler', '_hdlr')
    elif filename.endswith('_processor'):
        return filename.replace('_processor', '_proc')
    elif 'config' in filename.lower():
        return 'configuration'
    elif 'util' in filename.lower():
        return 'utilities'
    else:
        # デフォルトはファイル名そのまま
        return filename

def _calculate_new_path(src_root: Path, folder_name: str, depth: int, file_path: Path) -> Path:
    """新しいファイルパスを計算"""
    new_path = src_root
    
    # 深度に応じた階層構造を作成
    if depth == 1:
        # 深度1: src/components/filename/
        new_path = new_path / "components" / folder_name
    elif depth == 2:
        # 深度2: src/services/filename/
        new_path = new_path / "services" / folder_name
    elif depth == 3:
        # 深度3: src/infrastructure/filename/
        new_path = new_path / "infrastructure" / folder_name
    else:
        # 深度4以上: src/deep/levelN/filename/
        new_path = new_path / "deep"
        for i in range(depth - 3):
            new_path = new_path / f"level_{i+1}"
        new_path = new_path / folder_name
    
    # __init__.pyファイルを追加
    final_path = new_path / file_path.name
    return final_path

if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\n結果: {result.fix_policy}")
    if result.failure_locations:
        print(f"移動対象ファイル数: {len(result.failure_locations)}件")