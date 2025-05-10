import pytest
from src.language_env.language_config import LANGUAGE_CONFIGS, LanguageConfig
from src.language_env.execution_env_config import ExecutionEnvConfig
from src.language_env.language_env_profile import LanguageEnvProfile
from src.language_env.dockerfile_map import DOCKERFILE_MAP
from src.language_env.constants import CONTAINER_WORKSPACE, HOST_WORKSPACE


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
    assert DOCKERFILE_MAP["python"].endswith("python.Dockerfile")
    assert DOCKERFILE_MAP["rust"].endswith("rust.Dockerfile")
    assert DOCKERFILE_MAP["ojtools"].endswith("oj.Dockerfile")


def test_constants():
    assert CONTAINER_WORKSPACE == "/workspace"
    assert HOST_WORKSPACE == "./workspace" 