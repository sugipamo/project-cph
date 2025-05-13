import time
from unittest.mock import patch
from src.timer import Timer

def test_timer_elapsed():
    with patch('src.logger.Logger.info') as mock_info:
        with Timer('test') as t:
            time.sleep(0.01)
        assert t.elapsed >= 0.01
        assert t.label == 'test'
        assert mock_info.call_count == 1
        assert 'test took' in mock_info.call_args[0][0]

def test_timer_no_label():
    with patch('src.logger.Logger.info') as mock_info:
        with Timer() as t:
            time.sleep(0.005)
        assert t.elapsed >= 0.005
        assert t.label is None
        assert mock_info.call_count == 1
        assert 'Elapsed time:' in mock_info.call_args[0][0] 