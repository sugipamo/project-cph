import pytest
from pathlib import Path
from execution_env.execution_env import LocalExecutionEnv, DockerExecutionEnv, ExecutionEnvType, ExecutionStatus, ExecutionEnvFactory, BaseExecutionEnv
from execution_env.language_env_base import BaseTestHandler

# ダミーBaseTestHandler
class DummyHandler(BaseTestHandler):
    def run(self):
        pass
    def build(self):
        pass
    language = "cpp"

def test_local_execution_env_properties():
    handler = DummyHandler(
        source_file="main.cpp",
        contest_current_path=Path("contest_current"),
        contest_env_path=Path("contest_env"),
        contest_template_path=Path("contest_template"),
        contest_temp_path=Path(".temp"),
    )
    env = LocalExecutionEnv(handler)
    assert env.contest_current_path == Path("contest_current")
    assert env.source_file_path == Path("contest_current/main.cpp")
    assert env.env_type == ExecutionEnvType.LOCAL
    assert env.contest_env_path == Path("contest_env")
    assert env.contest_template_path == Path("contest_template")
    assert env.contest_temp_path == Path(".temp")
    assert env.test_case_path == Path("contest_current/test")
    assert env.test_case_in_path == Path("contest_current/test/in")
    assert env.test_case_out_path == Path("contest_current/test/out")
    # ステータス
    assert env.get_status() == ExecutionStatus.INIT
    env.set_status(ExecutionStatus.BUILT)
    assert env.get_status() == ExecutionStatus.BUILT

def test_docker_execution_env_properties():
    handler = DummyHandler(
        source_file="main.cpp",
        contest_current_path=Path("contest_current"),
        contest_env_path=Path("contest_env"),
        contest_template_path=Path("contest_template"),
        contest_temp_path=Path(".temp"),
    )
    env = DockerExecutionEnv(handler, container_workspace="/workspace")
    assert str(env.contest_current_path).startswith("/workspace")
    assert str(env.source_file_path).endswith("main.cpp")
    assert env.env_type == ExecutionEnvType.DOCKER
    assert str(env.contest_env_path).startswith("/workspace")
    assert str(env.contest_template_path).startswith("/workspace")
    assert str(env.contest_temp_path).startswith("/workspace")
    assert str(env.test_case_path).endswith("test")
    assert str(env.test_case_in_path).endswith("test/in")
    assert str(env.test_case_out_path).endswith("test/out")
    assert env.image_name == "cpp"

def test_execution_env_factory():
    # predicate: handler.language == "cpp" ならLocalExecutionEnv
    ExecutionEnvFactory._registry.clear()
    ExecutionEnvFactory.register(lambda h: getattr(h, "language", None) == "cpp")(LocalExecutionEnv)
    handler = DummyHandler(
        source_file="main.cpp",
        contest_current_path=Path("contest_current"),
        contest_env_path=Path("contest_env"),
        contest_template_path=Path("contest_template"),
        contest_temp_path=Path(".temp"),
    )
    env = ExecutionEnvFactory.create(handler)
    assert isinstance(env, LocalExecutionEnv)
    # 不一致の場合は例外
    class OtherHandler(BaseTestHandler):
        def run(self): pass
        def build(self): pass
        language = "python"
    other = OtherHandler(
        source_file="main.py",
        contest_current_path=Path("contest_current"),
        contest_env_path=Path("contest_env"),
        contest_template_path=Path("contest_template"),
        contest_temp_path=Path(".temp"),
    )
    with pytest.raises(ValueError):
        ExecutionEnvFactory.create(other) 