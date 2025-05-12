import pytest
from src.language_env.language_config import LANGUAGE_CONFIGS, LanguageConfig
from src.language_env.execution_env_config import ExecutionEnvConfig
from src.language_env.language_env_profile import LanguageEnvProfile
from src.language_env.dockerfile_map import DOCKERFILE_MAP
from src.language_env.constants import CONTAINER_WORKSPACE, HOST_WORKSPACE
from contest_env.python_config import PYTHON_CONFIGS
from contest_env.rust_config import RUST_CONFIGS
from contest_env.pypy_config import PYPY_CONFIGS
from contest_env.ojtools_config import OJTOOLS_CONFIGS


def test_language_configs():
    assert "python" in LANGUAGE_CONFIGS
    assert isinstance(LANGUAGE_CONFIGS["python"], LanguageConfig)
    assert LANGUAGE_CONFIGS["python"].run_cmd == ["python3", "{source}"]
    assert LANGUAGE_CONFIGS["rust"].build_cmd == ["cargo", "build", "--release"]
    assert LANGUAGE_CONFIGS["rust"].bin_path == "target/release/rust"


def test_execution_env_config():
    config = ExecutionEnvConfig(type="docker", mounts=[("./workspace", "/workspace")], env_vars={"A": "B"})
    assert config.type == "docker"
    assert ("./workspace", "/workspace") in config.mounts
    assert config.env_vars["A"] == "B"


def test_language_env_profile():
    lang_conf = LANGUAGE_CONFIGS["python"]
    env_conf = ExecutionEnvConfig(type="local")
    profile = LanguageEnvProfile(lang_conf, env_conf)
    assert profile.language_config is lang_conf
    assert profile.env_config is env_conf


def test_dockerfile_map():
    assert PYTHON_CONFIGS["3.8"]["dockerfile_path"].endswith("python.Dockerfile")
    assert RUST_CONFIGS["1.70"]["dockerfile_path"].endswith("rust.Dockerfile")
    assert OJTOOLS_CONFIGS["default"]["dockerfile_path"].endswith("oj.Dockerfile")


def test_constants():
    assert CONTAINER_WORKSPACE == "/workspace"
    assert HOST_WORKSPACE == "./workspace" 