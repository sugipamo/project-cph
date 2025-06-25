import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_splitter import FileSplitter


def test_file_splitter():
    print("=" * 60)
    print("ファイル分割テスト")
    print("=" * 60)
    
    # config_node_logic.pyを分割対象にテスト
    test_dir = "/home/cphelper/project-cph/src/configuration/config_node"
    
    print(f"\n対象ディレクトリ: {test_dir}")
    print("-" * 60)
    
    splitter = FileSplitter(test_dir, single_function_per_file=True, single_class_per_file=True)
    
    # config_node_logic.pyの解析
    test_file = os.path.join(test_dir, "config_node_logic.py")
    if os.path.exists(test_file):
        print(f"\n解析対象: {test_file}")
        analysis = splitter.analyze_file(test_file)
        
        print(f"\n発見された要素:")
        print(f"  - 関数数: {len(analysis.functions)}")
        for func in analysis.functions:
            print(f"    * {func.name} (行 {func.line_start + 1}-{func.line_end})")
        
        print(f"  - クラス数: {len(analysis.classes)}")
        for cls in analysis.classes:
            print(f"    * {cls.name} (行 {cls.line_start + 1}-{cls.line_end})")
        
        if splitter.should_split_file(analysis):
            print(f"\n✅ このファイルは分割対象です")
            plan = splitter.generate_split_plan(analysis)
            
            print(f"\n分割計画:")
            for name, obj_type, target in plan.splits:
                print(f"  - {name} ({obj_type}) → {plan.target_dir}/{target}")
        else:
            print(f"\n❌ このファイルは分割対象ではありません")
    
    # プロジェクト全体の解析（Dry Run）
    print(f"\n\n=== プロジェクト全体の解析 ===")
    results = splitter.analyze_and_split_project(dry_run=True)
    
    print(f"\n📊 解析結果サマリー:")
    print(f"  - 解析したファイル数: {results['files_analyzed']}")
    print(f"  - 分割対象ファイル数: {results['files_to_split']}")
    print(f"  - 総関数数: {results['total_functions']}")
    print(f"  - 総クラス数: {results['total_classes']}")


if __name__ == "__main__":
    test_file_splitter()