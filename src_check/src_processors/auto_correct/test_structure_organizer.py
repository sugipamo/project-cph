import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from structure_organizer import StructureOrganizer


def test_current_project():
    print("=" * 60)
    print("プロジェクト構造解析テスト")
    print("=" * 60)
    
    src_dir = "/home/cphelper/project-cph/src"
    report_path = "/home/cphelper/project-cph/structure_analysis_report.json"
    
    print(f"\n対象ディレクトリ: {src_dir}")
    print("-" * 60)
    
    organizer = StructureOrganizer(src_dir)
    organizer.analyze_project()
    
    print("\n=== 解析結果 ===")
    print(f"解析したファイル数: {len(organizer.file_analyses)}")
    
    print("\n=== インポートグラフ ===")
    for module, imports in organizer.import_graph.items():
        if imports:
            print(f"{module}:")
            for imp in imports:
                print(f"  → {imp}")
    
    print("\n=== 問題の検出 ===")
    has_issues = organizer.check_issues()
    
    if has_issues:
        print("\n⚠️  プロジェクトに問題が検出されました。")
        print("構造の再編成は実行されません。")
    else:
        print("\n✅ 問題は検出されませんでした。")
        
        ideal_structure = organizer.determine_ideal_structure()
        
        if ideal_structure:
            print("\n=== 推奨される構造変更 ===")
            for source, dest in ideal_structure.items():
                print(f"  {source}")
                print(f"  → {dest}")
                print()
            
            move_steps = organizer.generate_move_plan(ideal_structure)
            
            print("\n=== 移動計画 ===")
            for step in move_steps:
                print(f"移動: {step.source}")
                print(f"  → {step.destination}")
                print(f"  理由: {step.reason}")
                print()
        else:
            print("\n現在の構造は適切です。変更の必要はありません。")
    
    report = organizer.generate_report()
    
    import json
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 詳細レポートを保存しました: {report_path}")
    
    print("\n=== レポートサマリー ===")
    print(f"総ファイル数: {report['total_files']}")
    print(f"循環参照: {report['circular_references']}")
    print(f"遅延インポート: {report['delayed_imports']}")


if __name__ == "__main__":
    test_current_project()