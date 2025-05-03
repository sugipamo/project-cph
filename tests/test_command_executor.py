import pytest
from src.command_executor import CommandExecutor
from src.podman_operator import MockPodmanOperator
from src.contest_file_manager import ContestFileManager
import asyncio
from command_executor import MockEditorOpener
from podman_operator import LocalPodmanOperator
import io

class MockFileOperator:
    def __init__(self):
        self.prepare_called = False
    def move(self, *a, **kw): pass
    def copy(self, *a, **kw): pass
    def exists(self, *a, **kw): return False

class MockContestFileManager(ContestFileManager):
    def __init__(self):
        super().__init__(MockFileOperator())
        self.prepare_called = False
    def prepare_problem_files(self, *a, **kw):
        self.prepare_called = True

class DummyPodmanOperator(LocalPodmanOperator):
    def __init__(self):
        self.called = False
    async def run_oj(self, *a, **kw):
        self.called = True
        return 0, "dummy", ""

class DummyFileManager(ContestFileManager):
    def __init__(self):
        super().__init__(None)
    def prepare_problem_files(self, contest_name, problem_name, language_name):
        self.called = (contest_name, problem_name, language_name)

@pytest.mark.skip(reason="対話が必要なため自動テストから除外")
@pytest.mark.asyncio
async def test_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.login()

@pytest.mark.asyncio
async def test_open():
    mock_podman = MockPodmanOperator()
    mock_file_manager = MockContestFileManager()
    executor = CommandExecutor(podman_operator=mock_podman, file_manager=mock_file_manager)
    await executor.open("abc300", "a", "python")
    assert mock_file_manager.prepare_called
    assert mock_podman.calls[0][0] == "run_oj"

@pytest.mark.asyncio
async def test_submit():
    executor = CommandExecutor()
    # 警告return仕様に合わせて、戻り値がNoneであることを確認
    result = await executor.submit("abc300", "a", "python")
    assert result is None

@pytest.mark.asyncio
async def test_test():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.test("abc300", "a", "python")

@pytest.mark.skip(reason="対話が必要なため自動テストから除外")
@pytest.mark.asyncio
async def test_execute_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.execute("login")

@pytest.mark.asyncio
async def test_execute_open():
    mock_podman = MockPodmanOperator()
    mock_file_manager = MockContestFileManager()
    executor = CommandExecutor(podman_operator=mock_podman, file_manager=mock_file_manager)
    await executor.execute("open", "abc300", "a", "python")
    assert mock_file_manager.prepare_called
    assert mock_podman.calls[0][0] == "run_oj"

@pytest.mark.asyncio
async def test_execute_submit():
    executor = CommandExecutor()
    # 警告return仕様に合わせて、戻り値がNoneであることを確認
    result = await executor.execute("submit", "abc300", "a", "python")
    assert result is None

@pytest.mark.asyncio
async def test_execute_test():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.execute("test", "abc300", "a", "python")

@pytest.mark.asyncio
async def test_execute_invalid():
    executor = CommandExecutor()
    with pytest.raises(ValueError):
        await executor.execute("invalid_command")

def test_open_calls_editor_and_file_manager():
    mock_editor = MockEditorOpener()
    dummy_file_manager = DummyFileManager()
    dummy_podman = DummyPodmanOperator()
    executor = CommandExecutor(
        podman_operator=dummy_podman,
        file_manager=dummy_file_manager,
        editor_opener=mock_editor
    )
    asyncio.run(executor.open("abc300", "a", "python"))
    assert dummy_file_manager.called == ("abc300", "a", "python")
    assert mock_editor.opened_paths == ["contest_current/python/main.py"]
    assert dummy_podman.called

@pytest.mark.asyncio
async def test_open_with_none_dependencies():
    # file_manager=None, editor_opener=None でも例外が発生しないか
    executor = CommandExecutor(podman_operator=MockPodmanOperator(), file_manager=None, editor_opener=None)
    # 問題ディレクトリが存在しない場合でも例外が発生しないことを確認
    await executor.open("abc999", "z", "python")
    # editor_openerがNoneでもエラーにならない（デフォルトが使われる）
    executor2 = CommandExecutor(podman_operator=MockPodmanOperator(), file_manager=MockContestFileManager(), editor_opener=None)
    await executor2.open("abc300", "a", "python")
    # file_managerがNoneでもエラーにならない（何も起きない）
    executor3 = CommandExecutor(podman_operator=MockPodmanOperator(), file_manager=None, editor_opener=MockEditorOpener())
    await executor3.open("abc300", "a", "python") 