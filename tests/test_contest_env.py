import pytest
from unittest.mock import patch, MagicMock
from contest_env.python.env import PythonContainerHandler, PythonLocalHandler

@pytest.mark.parametrize("HandlerCls, expected_env_type", [
    (PythonContainerHandler, "container"),
    (PythonLocalHandler, "local"),
])
@patch("contest_env.base.get_profile", return_value=MagicMock(language_config=MagicMock(), env_config=MagicMock()))
def test_python_handler_properties(mock_get_profile, HandlerCls, expected_env_type):
    handler = HandlerCls("python", expected_env_type)
    # クラス属性
    assert handler.language_name == "python"
    assert handler.env_type == expected_env_type
    # dockerfile_path, run_cmd
    assert hasattr(handler, "dockerfile_path")
    assert handler.dockerfile_path == "contest_env/python/Dockerfile"
    assert hasattr(handler, "run_cmd")
    assert handler.run_cmd == ["python3", "{source}"]


@patch("contest_env.base.get_profile", return_value=MagicMock(language_config=MagicMock(), env_config=MagicMock()))
def test_python_handler_build_and_run_command(mock_get_profile):
    handler = PythonContainerHandler("python", "container")
    # build_command, run_command
    temp_source_path = "/tmp/main.py"
    build_cmd = handler.build_command(temp_source_path)
    run_cmd = handler.run_command(temp_source_path)
    # Pythonはbuild不要なのでbuild_cmdはNoneまたは空
    assert build_cmd is None or build_cmd == []
    # run_cmdはrun_cmd属性と一致
    assert run_cmd == ["python3", "{source}"]


@patch("contest_env.base.get_profile", return_value=MagicMock(language_config=MagicMock(), env_config=MagicMock()))
def test_python_handler_cwd_methods(mock_get_profile):
    handler = PythonContainerHandler("python", "container")
    source_path = "/tmp/main.py"
    assert handler.get_build_cwd(source_path) == "/tmp"
    assert handler.get_run_cwd(source_path) == "/tmp" 