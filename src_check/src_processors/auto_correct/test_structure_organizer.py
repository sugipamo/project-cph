import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structure_organizer import StructureOrganizer

def test_current_project():
    logger('=' * 60)
    logger('プロジェクト構造解析テスト')
    logger('=' * 60)
    src_dir = '/home/cphelper/project-cph/src'
    report_path = '/home/cphelper/project-cph/structure_analysis_report.json'
    logger(f'\n対象ディレクトリ: {src_dir}')
    logger('-' * 60)
    organizer = StructureOrganizer(src_dir)
    organizer.analyze_project()
    logger('\n=== 解析結果 ===')
    logger(f'解析したファイル数: {len(organizer.file_analyses)}')
    logger('\n=== インポートグラフ ===')
    for module, imports in organizer.import_graph.items():
        if imports:
            logger(f'{module}:')
            for imp in imports:
                logger(f'  → {imp}')
    logger('\n=== 問題の検出 ===')
    has_issues = organizer.check_issues()
    if has_issues:
        logger('\n⚠️  プロジェクトに問題が検出されました。')
        logger('構造の再編成は実行されません。')
    else:
        logger('\n✅ 問題は検出されませんでした。')
        ideal_structure = organizer.determine_ideal_structure()
        if ideal_structure:
            logger('\n=== 推奨される構造変更 ===')
            for source, dest in ideal_structure.items():
                logger(f'  {source}')
                logger(f'  → {dest}')
                logger()
            move_steps = organizer.generate_move_plan(ideal_structure)
            logger('\n=== 移動計画 ===')
            for step in move_steps:
                logger(f'移動: {step.source}')
                logger(f'  → {step.destination}')
                logger(f'  理由: {step.reason}')
                logger()
        else:
            logger('\n現在の構造は適切です。変更の必要はありません。')
    report = organizer.generate_report()
    import json
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger(f'\n📊 詳細レポートを保存しました: {report_path}')
    logger('\n=== レポートサマリー ===')
    logger(f'総ファイル数: {report['total_files']}')
    logger(f'循環参照: {report['circular_references']}')
    logger(f'遅延インポート: {report['delayed_imports']}')
if __name__ == '__main__':
    test_current_project()