import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.command_executor import CommandExecutor, MockOpener

class DummyEnvCls:
    def __init__(self):
        self.dockerfile_path = "dummy/Dockerfile"

@pytest.mark.asyncio
@pytest.mark.parametrize("exec_mode", ["local", "docker"])
async def test_command_executor_execute_all(exec_mode):
    file_manager = MagicMock()
    opener = MagicMock()
    with patch("src.command_executor.CommandLogin") as MockLogin, \
         patch("src.command_executor.CommandOpen") as MockOpen, \
         patch("src.command_executor.CommandTest") as MockTest, \
         patch("src.command_executor.CommandSubmit") as MockSubmit, \
         patch("src.execution_env.info_json_manager.InfoJsonManager") as MockInfoJsonManager, \
         patch("src.path_manager.unified_path_manager.UnifiedPathManager") as MockUPM, \
         patch("src.execution_env.language_env_profile.LANGUAGE_ENVS", { ("python", "3.8"): DummyEnvCls }), \
         patch("src.execution_env.execution_resource_manager.LANGUAGE_ENVS", { ("python", "3.8"): DummyEnvCls }):
        MockLogin.return_value.login = AsyncMock(return_value="login-ok")
        MockOpen.return_value.open = AsyncMock(return_value="open-ok")
        MockTest.return_value.run_test = AsyncMock(return_value="test-ok")
        MockSubmit.return_value.submit = AsyncMock(return_value="submit-ok")
        MockInfoJsonManager.return_value.data = {}
        MockUPM.return_value.info_json.return_value = "dummy.json"
        executor = CommandExecutor(file_manager=file_manager, opener=opener, exec_mode=exec_mode)
        assert await executor.execute("login") == "login-ok"
        assert await executor.execute("open", "abc", "a", "python") == "open-ok"
        assert await executor.execute("test", "abc", "a", "python") == "test-ok"
        assert await executor.execute("submit", "abc", "a", "python") == "submit-ok"
        with pytest.raises(ValueError):
            await executor.execute("unknown")

@pytest.mark.asyncio
async def test_command_executor_shortcuts():
    file_manager = MagicMock()
    opener = MagicMock()
    with patch("src.command_executor.CommandOpen") as MockOpen, \
         patch("src.command_executor.CommandTest") as MockTest, \
         patch("src.command_executor.CommandSubmit") as MockSubmit, \
         patch("src.execution_env.info_json_manager.InfoJsonManager") as MockInfoJsonManager, \
         patch("src.path_manager.unified_path_manager.UnifiedPathManager") as MockUPM, \
         patch("src.execution_env.language_env_profile.LANGUAGE_ENVS", { ("python", "3.8"): DummyEnvCls }), \
         patch("src.execution_env.execution_resource_manager.LANGUAGE_ENVS", { ("python", "3.8"): DummyEnvCls }):
        MockOpen.return_value.open = AsyncMock(return_value="open-ok")
        MockTest.return_value.run_test = AsyncMock(return_value="test-ok")
        MockSubmit.return_value.submit = AsyncMock(return_value="submit-ok")
        MockInfoJsonManager.return_value.data = {}
        MockUPM.return_value.info_json.return_value = "dummy.json"
        executor = CommandExecutor(file_manager=file_manager, opener=opener, exec_mode="docker")
        assert await executor.open("abc", "a", "python") == "open-ok"
        assert await executor.submit("abc", "a", "python") == "submit-ok"
        assert await executor.run_test("abc", "a", "python") == "test-ok"


def test_mock_opener():
    opener = MockOpener()
    opener.open_editor("/tmp", "python")
    opener.open_browser("http://example.com")
    assert "/tmp/main.py" in opener.opened_paths
    assert "http://example.com" in opener.opened_urls 