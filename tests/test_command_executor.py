import pytest
from src.command_executor import CommandExecutor

@pytest.mark.skip(reason="対話が必要なため自動テストから除外")
@pytest.mark.asyncio
async def test_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.login()

@pytest.mark.asyncio
async def test_open():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.open("abc300", "a", "python")

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
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        await executor.execute("open", "abc300", "a", "python")

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