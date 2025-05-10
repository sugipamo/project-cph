from .language_config import LANGUAGE_CONFIGS
from .execution_env_config import ExecutionEnvConfig
from .language_env_profile import LanguageEnvProfile

# Python（Docker）
PYTHON_DOCKER_PROFILE = LanguageEnvProfile(
    LANGUAGE_CONFIGS["python"],
    ExecutionEnvConfig(type="docker")
)

# Python（ローカル）
PYTHON_LOCAL_PROFILE = LanguageEnvProfile(
    LANGUAGE_CONFIGS["python"],
    ExecutionEnvConfig(type="local")
)

# Pypy（ローカル）
PYPY_LOCAL_PROFILE = LanguageEnvProfile(
    LANGUAGE_CONFIGS["pypy"],
    ExecutionEnvConfig(type="local")
)

# Rust（Docker）
RUST_DOCKER_PROFILE = LanguageEnvProfile(
    LANGUAGE_CONFIGS["rust"],
    ExecutionEnvConfig(type="docker")
)

# Rust（ローカル）
RUST_LOCAL_PROFILE = LanguageEnvProfile(
    LANGUAGE_CONFIGS["rust"],
    ExecutionEnvConfig(type="local")
)

PROFILES = {
    ("python", "docker"): PYTHON_DOCKER_PROFILE,
    ("python", "local"): PYTHON_LOCAL_PROFILE,
    ("pypy", "local"): PYPY_LOCAL_PROFILE,
    ("rust", "docker"): RUST_DOCKER_PROFILE,
    ("rust", "local"): RUST_LOCAL_PROFILE,
}

def get_profile(language, env_type):
    """
    言語名（例: 'python'）と環境タイプ（例: 'docker' or 'local'）からLanguageEnvProfileを取得する。
    存在しない場合はKeyErrorを投げる。
    """
    key = (language, env_type)
    if key not in PROFILES:
        raise KeyError(f"Profile not found for language={language}, env_type={env_type}")
    return PROFILES[key] 