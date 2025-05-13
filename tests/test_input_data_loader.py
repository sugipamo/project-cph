import io
import os
from unittest.mock import MagicMock, patch
from src.input_data_loader import InputDataLoader

def test_load_with_file_operator_and_host_in_file():
    file_operator = MagicMock()
    file_operator.exists.side_effect = lambda path: path == 'in.txt'
    file_operator.open.return_value.__enter__.return_value.read.return_value = 'data1'
    result = InputDataLoader.load(file_operator, 'in.txt', 'backup.txt')
    assert result == 'data1'

def test_load_with_file_operator_and_host_in_file_path():
    file_operator = MagicMock()
    file_operator.exists.side_effect = lambda path: path == 'backup.txt'
    file_operator.open.return_value.__enter__.return_value.read.return_value = 'data2'
    result = InputDataLoader.load(file_operator, None, 'backup.txt')
    assert result == 'data2'

def test_load_with_file_operator_not_found():
    file_operator = MagicMock()
    file_operator.exists.return_value = False
    result = InputDataLoader.load(file_operator, 'notfound.txt', 'notfound2.txt')
    assert result == ''

def test_load_without_file_operator_and_host_in_file(tmp_path):
    in_file = tmp_path / 'in.txt'
    in_file.write_text('data3', encoding='utf-8')
    with patch('os.path.exists', side_effect=lambda path: path == str(in_file)):
        result = InputDataLoader.load(None, str(in_file), 'backup.txt')
        assert result == 'data3'

def test_load_without_file_operator_and_host_in_file_path(tmp_path):
    backup_file = tmp_path / 'backup.txt'
    backup_file.write_text('data4', encoding='utf-8')
    with patch('os.path.exists', side_effect=lambda path: path == str(backup_file)):
        result = InputDataLoader.load(None, None, str(backup_file))
        assert result == 'data4'

def test_load_without_file_operator_not_found():
    with patch('os.path.exists', return_value=False):
        result = InputDataLoader.load(None, 'notfound.txt', 'notfound2.txt')
        assert result == '' 