import pytest
from unittest.mock import MagicMock, patch
from src.commands.command_open import CommandOpen

class DummyFileManager:
    def __init__(self):
        self.file_operator = MagicMock()
    def prepare_problem_files(self, contest, problem, lang):
        self.called = True
    def get_problem_files(self, contest, problem, lang):
        return 'problem_dir', 'test_dir'

class DummyOpener:
    def __init__(self):
        self.browser_opened = False
        self.editor_opened = False
        self.last_editor_path = None
    def open_browser(self, url):
        self.browser_opened = True
        self.last_url = url
    def open_editor(self, path, lang):
        self.editor_opened = True
        self.last_editor_path = path

class DummyTestEnv:
    def __init__(self):
        self.adjusted = False
        self.downloaded = False
    def adjust_containers(self, req, contest, problem, lang):
        self.adjusted = True
        self.last_req = req
        return ['c1', 'c2']
    def download_testcases(self, url, test_dir):
        self.downloaded = True
        self.last_url = url
        self.last_test_dir = test_dir

@patch('src.commands.command_open.ConfigJsonManager')
@patch('src.commands.command_open.InfoJsonManager')
@patch('src.commands.command_open.UnifiedPathManager')
@pytest.mark.asyncio
async def test_open_entry_file_and_editor(mock_upm, mock_info, mock_config):
    file_manager = DummyFileManager()
    opener = DummyOpener()
    test_env = DummyTestEnv()
    # entry_fileが存在する場合
    mock_config.return_value.get_entry_file.return_value = 'main.py'
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = '/path/to/main.py'
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_info.return_value = MagicMock()
    file_manager.file_operator.glob.return_value = ['a.in', 'b.in']
    cmd = CommandOpen(file_manager, opener, test_env)
    await cmd.open('abc', 'pqr', 'python')
    assert opener.browser_opened
    assert opener.editor_opened
    assert 'main.py' in opener.last_editor_path
    assert test_env.adjusted
    assert test_env.downloaded

@patch('src.commands.command_open.ConfigJsonManager')
@patch('src.commands.command_open.InfoJsonManager')
@patch('src.commands.command_open.UnifiedPathManager')
@pytest.mark.asyncio
async def test_open_no_entry_file_opens_dir(mock_upm, mock_info, mock_config):
    file_manager = DummyFileManager()
    opener = DummyOpener()
    test_env = DummyTestEnv()
    # entry_fileが存在しない場合
    mock_config.return_value.get_entry_file.return_value = None
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = '/path/to/dir'
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_info.return_value = MagicMock()
    file_manager.file_operator.glob.return_value = ['a.in']
    cmd = CommandOpen(file_manager, opener, test_env)
    await cmd.open('abc', 'pqr', 'python')
    assert opener.editor_opened
    assert 'dir' in opener.last_editor_path

@patch('src.commands.command_open.ConfigJsonManager')
@patch('src.commands.command_open.InfoJsonManager')
@patch('src.commands.command_open.UnifiedPathManager')
@pytest.mark.asyncio
async def test_open_no_file_operator(mock_upm, mock_info, mock_config):
    file_manager = MagicMock()
    file_manager.file_operator = None
    file_manager.prepare_problem_files.return_value = None
    file_manager.get_problem_files.return_value = ('problem_dir', 'test_dir')
    opener = DummyOpener()
    test_env = DummyTestEnv()
    mock_config.return_value.get_entry_file.return_value = None
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = '/path/to/dir'
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_info.return_value = MagicMock()
    # os.listdir, os.path.existsをpatch
    with patch('os.listdir', return_value=['a.in', 'b.in']), patch('os.path.exists', return_value=True):
        cmd = CommandOpen(file_manager, opener, test_env)
        await cmd.open('abc', 'pqr', 'python')
        assert opener.editor_opened
        assert test_env.adjusted
        assert test_env.downloaded 