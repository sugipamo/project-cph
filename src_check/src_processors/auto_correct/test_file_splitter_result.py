import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from file_splitter import main
from src_check.models.check_result import CheckResult

def test_file_splitter_with_result():
    logger('=' * 60)
    logger('ファイル分割CheckResult返却テスト')
    logger('=' * 60)
    di_container = None
    result = main(di_container)
    logger(f'\n=== CheckResult ===')
    logger(f'失敗箇所数: {len(result.failure_locations)}')
    logger(f'修正ポリシー: {result.fix_policy}')
    if result.failure_locations:
        logger(f'\n失敗箇所一覧:')
        for loc in result.failure_locations:
            logger(f'  - {loc.file_path} (行: {loc.line_number})')
    if result.fix_example_code:
        logger(f'\n修正例:')
        logger(result.fix_example_code)
    assert isinstance(result, CheckResult), '戻り値がCheckResult型ではありません'
    assert isinstance(result.failure_locations, list), 'failure_locationsがリストではありません'
    logger('\n✅ テスト成功: CheckResultが正しく返されました')
if __name__ == '__main__':
    test_file_splitter_with_result()