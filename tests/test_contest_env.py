import pytest
from contest_env.python.env import PythonContainerHandler, PythonLocalHandler

@pytest.mark.parametrize("HandlerCls, expected_env_type", [
    (PythonContainerHandler, "container"),
    (PythonLocalHandler, "local"),
])
def test_python_handler_properties(HandlerCls, expected_env_type):
    handler = HandlerCls("python", expected_env_type)
    # クラス属性
    assert handler.language == "python"
    assert handler.env_type == expected_env_type
    # dockerfile_path, run_cmd
    assert hasattr(handler, "dockerfile_path")
    if expected_env_type == "container":
        assert handler.dockerfile_path == "contest_env/python/Dockerfile"
    else:
        assert handler.dockerfile_path is None
    assert hasattr(handler, "run_cmd")
    assert handler.run_cmd == ["python3", "{source}"]


def test_python_handler_cwd_methods():
    handler = PythonContainerHandler("python", "container")
    source_path = "/tmp/main.py"
    assert handler.get_build_cwd(source_path) == "/tmp"
    assert handler.get_run_cwd(source_path) == "/tmp" 