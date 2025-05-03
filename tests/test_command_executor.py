import pytest
from src.command_executor import CommandExecutor
from src.podman_operator import MockPodmanOperator
from src.contest_file_manager import ContestFileManager

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
    with pytest.raises(NotImplementedError):
        await executor.submit("abc300", "a", "python")

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
    with pytest.raises(NotImplementedError):
        await executor.execute("submit", "abc300", "a", "python")

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