import pytest
from src.command_executor import CommandExecutor

def test_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.login()

def test_open():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.open("abc300", "a", "python")

def test_submit():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.submit("abc300", "a", "python")

def test_test():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.test("abc300", "a", "python")

def test_execute_login():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.execute("login")

def test_execute_open():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.execute("open", "abc300", "a", "python")

def test_execute_submit():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.execute("submit", "abc300", "a", "python")

def test_execute_test():
    executor = CommandExecutor()
    with pytest.raises(NotImplementedError):
        executor.execute("test", "abc300", "a", "python")

def test_execute_invalid():
    executor = CommandExecutor()
    with pytest.raises(ValueError):
        executor.execute("invalid_command") 