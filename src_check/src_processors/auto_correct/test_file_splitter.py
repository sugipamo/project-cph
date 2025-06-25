import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_splitter import FileSplitter

def test_file_splitter():
    logger('=' * 60)
    logger('ファイル分割テスト')
    logger('=' * 60)
    test_dir = '/home/cphelper/project-cph/src/configuration/config_node'
    logger(f'\n対象ディレクトリ: {test_dir}')
    logger('-' * 60)
    splitter = FileSplitter(test_dir, single_function_per_file=True, single_class_per_file=True)
    test_file = os.path.join(test_dir, 'config_node_logic.py')
    if os.path.exists(test_file):
        logger(f'\n解析対象: {test_file}')
        analysis = splitter.analyze_file(test_file)
        logger(f'\n発見された要素:')
        logger(f'  - 関数数: {len(analysis.functions)}')
        for func in analysis.functions:
            logger(f'    * {func.name} (行 {func.line_start + 1}-{func.line_end})')
        logger(f'  - クラス数: {len(analysis.classes)}')
        for cls in analysis.classes:
            logger(f'    * {cls.name} (行 {cls.line_start + 1}-{cls.line_end})')
        if splitter.should_split_file(analysis):
            logger(f'\n✅ このファイルは分割対象です')
            plan = splitter.generate_split_plan(analysis)
            logger(f'\n分割計画:')
            for name, obj_type, target in plan.splits:
                logger(f'  - {name} ({obj_type}) → {plan.target_dir}/{target}')
        else:
            logger(f'\n❌ このファイルは分割対象ではありません')
    logger(f'\n\n=== プロジェクト全体の解析 ===')
    results = splitter.analyze_and_split_project(dry_run=True)
    logger(f'\n📊 解析結果サマリー:')
    logger(f'  - 解析したファイル数: {results['files_analyzed']}')
    logger(f'  - 分割対象ファイル数: {results['files_to_split']}')
    logger(f'  - 総関数数: {results['total_functions']}')
    logger(f'  - 総クラス数: {results['total_classes']}')
if __name__ == '__main__':
    test_file_splitter()