import pytest
from unittest.mock import MagicMock, patch
from src.commands.command_submit import CommandSubmit

class DummyFileOperator:
    def __init__(self, exists=True):
        self._exists = exists
        self.opened = False
    def exists(self, path):
        return self._exists
    def open(self, path, mode, encoding=None):
        self.opened = True
        import io
        return io.StringIO('{"language_id": {"python": "py3"}}')

class DummyFileManager:
    def __init__(self, exists=True):
        self.file_operator = DummyFileOperator(exists)

class DummyTestEnv:
    def submit_via_ojtools(self, args, volumes, workdir):
        return 'ok', 'stdout', 'stderr'
    def to_container_path(self, host_path):
        return host_path

class DummyCommandTest:
    def __init__(self, ac=True):
        self._ac = ac
    async def run_test_return_results(self, *a, **k):
        return [{'result': 'AC'}] if self._ac else [{'result': 'WA'}]
    def print_test_results(self, results):
        self.printed = True
    def is_all_ac(self, results):
        return all(r['result'] == 'AC' for r in results)
    def prepare_test_environment(self, *a, **k):
        return 'src', 'test_dir'
    def collect_test_cases(self, test_dir, file_operator):
        return ['a.in', 'b.in'], []

@patch('src.commands.command_submit.InfoJsonManager')
def test_validate_info_file_warns_contest(mock_info):
    mock_info.return_value.data = {'contest_name': 'abc', 'problem_name': 'pqr'}
    cmd = CommandSubmit(None, None)
    result = cmd.validate_info_file('info.json', 'zzz', 'pqr')
    assert result is None

@patch('src.commands.command_submit.InfoJsonManager')
def test_validate_info_file_warns_problem(mock_info):
    mock_info.return_value.data = {'contest_name': 'abc', 'problem_name': 'pqr'}
    cmd = CommandSubmit(None, None)
    result = cmd.validate_info_file('info.json', 'abc', 'xxx')
    assert result is None

@patch('src.commands.command_submit.InfoJsonManager')
def test_validate_info_file_ok(mock_info):
    mock_info.return_value.data = {'contest_name': 'abc', 'problem_name': 'pqr'}
    cmd = CommandSubmit(None, None)
    result = cmd.validate_info_file('info.json', 'abc', 'pqr')
    assert result == {'contest_name': 'abc', 'problem_name': 'pqr'}

def test_get_language_id_from_config_file_operator():
    cmd = CommandSubmit(DummyFileManager(), None)
    lang_id = cmd.get_language_id_from_config('config.json', 'python', cmd.file_manager.file_operator)
    assert lang_id == 'py3'

def test_get_language_id_from_config_no_file_operator(tmp_path):
    import json
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps({'language_id': {'python': 'py3'}}), encoding='utf-8')
    cmd = CommandSubmit(None, None)
    lang_id = cmd.get_language_id_from_config(str(config_path), 'python', None)
    assert lang_id == 'py3'

def test_build_submit_command():
    cmd = CommandSubmit(None, None)
    args, url = cmd.build_submit_command('abc', 'pqr', 'python', 'main.py', 'py3')
    assert '--language' in args and 'py3' in args
    args2, url2 = cmd.build_submit_command('abc', 'pqr', 'python', 'main.py', None)
    assert '--language' not in args2

def test_get_ojtools_container_from_info():
    with patch('src.commands.command_submit.InfoJsonManager') as mock_info:
        mock_info.return_value.get_containers.return_value = [{'name': 'ojtools1'}]
        cmd = CommandSubmit(None, None)
        assert cmd.get_ojtools_container_from_info() == 'ojtools1'

def test_get_ojtools_container_from_info_raises():
    with patch('src.commands.command_submit.InfoJsonManager') as mock_info:
        mock_info.return_value.get_containers.return_value = []
        cmd = CommandSubmit(None, None)
        with pytest.raises(RuntimeError):
            cmd.get_ojtools_container_from_info()

@patch('src.commands.command_submit.CommandTest')
@patch('src.commands.command_submit.get_project_root_volumes', return_value={})
@patch('src.commands.command_submit.InfoJsonManager')
@patch('src.commands.command_submit.UnifiedPathManager')
@pytest.mark.asyncio
async def test_submit_all_ac(mock_upm, mock_info, mock_vol, mock_cmdtest):
    file_manager = DummyFileManager()
    test_env = DummyTestEnv()
    cmd = CommandSubmit(file_manager, test_env)
    cmd.command_test = DummyCommandTest(ac=True)
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = 'main.py'
    mock_info.return_value.data = {'contest_name': 'abc', 'problem_name': 'pqr'}
    result = await cmd.submit('abc', 'pqr', 'python')
    assert result == ('ok', 'stdout', 'stderr')

@patch('src.commands.command_submit.CommandTest')
@patch('src.commands.command_submit.get_project_root_volumes', return_value={})
@patch('src.commands.command_submit.InfoJsonManager')
@patch('src.commands.command_submit.UnifiedPathManager')
@patch('builtins.input', return_value='y')
@pytest.mark.asyncio
async def test_submit_wa_and_confirm_yes(mock_input, mock_upm, mock_info, mock_vol, mock_cmdtest):
    file_manager = DummyFileManager()
    test_env = DummyTestEnv()
    cmd = CommandSubmit(file_manager, test_env)
    cmd.command_test = DummyCommandTest(ac=False)
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = 'main.py'
    mock_info.return_value.data = {'contest_name': 'abc', 'problem_name': 'pqr'}
    result = await cmd.submit('abc', 'pqr', 'python')
    assert result == ('ok', 'stdout', 'stderr')

@patch('src.commands.command_submit.CommandTest')
@patch('src.commands.command_submit.get_project_root_volumes', return_value={})
@patch('src.commands.command_submit.InfoJsonManager')
@patch('src.commands.command_submit.UnifiedPathManager')
@patch('builtins.input', return_value='n')
@pytest.mark.asyncio
async def test_submit_wa_and_confirm_no(mock_input, mock_upm, mock_info, mock_vol, mock_cmdtest):
    file_manager = DummyFileManager()
    test_env = DummyTestEnv()
    cmd = CommandSubmit(file_manager, test_env)
    cmd.command_test = DummyCommandTest(ac=False)
    mock_upm.return_value.info_json.return_value = 'info.json'
    mock_upm.return_value.config_json.return_value = 'config.json'
    mock_upm.return_value.contest_current.return_value = 'main.py'
    result = await cmd.submit('abc', 'pqr', 'python')
    assert result is None 