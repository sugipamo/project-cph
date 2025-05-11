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

# テストケース用（言語非依存、共通temp_dir）
TESTCASE_PROFILE_LOCAL = LanguageEnvProfile(
    None,  # 言語設定不要
    ExecutionEnvConfig(type="local", temp_dir=".temp")
)
TESTCASE_PROFILE_DOCKER = LanguageEnvProfile(
    None,
    ExecutionEnvConfig(type="docker", temp_dir=".temp")
)

PROFILES = {
    ("python", "docker"): PYTHON_DOCKER_PROFILE,
    ("python", "local"): PYTHON_LOCAL_PROFILE,
    ("pypy", "local"): PYPY_LOCAL_PROFILE,
    ("rust", "docker"): RUST_DOCKER_PROFILE,
    ("rust", "local"): RUST_LOCAL_PROFILE,
    ("testcase", "local"): TESTCASE_PROFILE_LOCAL,
    ("testcase", "docker"): TESTCASE_PROFILE_DOCKER,
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