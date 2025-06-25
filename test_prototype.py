"""
テスト用プロトタイプ実行スクリプト
test_src/で実際の依存関係がある場合の移動計画をテスト
"""

import sys
from pathlib import Path

# プロトタイプのパスを追加
sys.path.insert(0, "src_check/src_processors/auto_correct/import_dependency_reorganizer")

from simple_import_analyzer import SimpleImportAnalyzer
from dependency_calculator import DependencyCalculator

def test_with_dependencies():
    """依存関係があるプロジェクトでのテスト"""
    test_src_root = Path("test_src")
    
    if not test_src_root.exists():
        print("test_src/が存在しません。先にtest_dependencies.pyを実行してください")
        return
    
    print("🧪 テスト用プロジェクトでの依存関係解析")
    print("=" * 50)
    
    # インポート解析
    analyzer = SimpleImportAnalyzer(test_src_root)
    analyzer.analyze_all_files()
    
    print(f"解析対象ファイル: {len(analyzer.file_imports)}個")
    
    # 各ファイルの依存関係を表示
    print("\n📊 ファイル別依存関係:")
    for file_path, imports in analyzer.file_imports.items():
        rel_path = file_path.relative_to(test_src_root)
        print(f"  {rel_path}: {imports}")
    
    # 依存関係計算
    calculator = DependencyCalculator(analyzer)
    
    # デバッグ: 依存関係グラフを確認
    print(f"\n🔍 依存関係グラフの詳細:")
    calculator.debug_print_graph(limit=10)
    
    depth_map = calculator.calculate_dependency_depths(max_depth=4)
    
    print(f"\n🏗️ 計算された深度:")
    for file_path, depth in depth_map.items():
        rel_path = file_path.relative_to(test_src_root)
        print(f"  深度{depth}: {rel_path}")
    
    # 移動計画をシミュレート
    print(f"\n📋 移動計画のシミュレーション:")
    
    for file_path, depth in depth_map.items():
        if depth == 0:
            continue
        
        rel_path = file_path.relative_to(test_src_root)
        
        if depth == 1:
            new_path = "test_src/components/" + file_path.stem + "/" + file_path.name
        elif depth == 2:
            new_path = "test_src/services/" + file_path.stem + "/" + file_path.name
        elif depth == 3:
            new_path = "test_src/infrastructure/" + file_path.stem + "/" + file_path.name
        else:
            new_path = f"test_src/deep/level_{depth-3}/" + file_path.stem + "/" + file_path.name
        
        print(f"  📦 {rel_path}")
        print(f"     → {new_path}")
        
        deps = analyzer.get_dependencies(file_path)
        dependents = analyzer.get_dependents(analyzer.path_to_module_name(file_path))
        print(f"     依存: {len(deps)}個, 被依存: {len(dependents)}個")
        if deps:
            print(f"     主要依存: {', '.join(deps[:2])}")

if __name__ == "__main__":
    test_with_dependencies()