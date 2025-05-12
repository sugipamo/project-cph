import importlib
import pkgutil
import os
from .execution_env_config import ExecutionEnvConfig
from .language_env_profile import LanguageEnvProfile

LANGUAGE_CONFIGS = {}
PROFILES = {}

# language_env配下の全ファイルを自動importし、*_CONFIGを集約
language_env_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../language_env')
for _, module_name, _ in pkgutil.iter_modules([language_env_dir]):
    if module_name.startswith("__"): continue
    mod = importlib.import_module(f"src.language_env.{module_name}")
    config = getattr(mod, f"{module_name.upper()}_CONFIG", None)
    if config:
        LANGUAGE_CONFIGS[module_name] = config
        # local/dockerのProfileを自動生成
        PROFILES[(module_name, "local")] = LanguageEnvProfile(config, ExecutionEnvConfig(type="local"))
        PROFILES[(module_name, "docker")] = LanguageEnvProfile(config, ExecutionEnvConfig(type="docker"))

# テストケース用（言語非依存、共通temp_dir）は手動で追加
TESTCASE_PROFILE_LOCAL = LanguageEnvProfile(
    None,  # 言語設定不要
    ExecutionEnvConfig(type="local", temp_dir=".temp")
)
TESTCASE_PROFILE_DOCKER = LanguageEnvProfile(
    None,
    ExecutionEnvConfig(type="docker", temp_dir=".temp")
)
PROFILES[("testcase", "local")] = TESTCASE_PROFILE_LOCAL
PROFILES[("testcase", "docker")] = TESTCASE_PROFILE_DOCKER

def get_profile(language, env_type):
    """
    言語名（例: 'python'）と環境タイプ（例: 'docker' or 'local'）からLanguageEnvProfileを取得する。
    存在しない場合はKeyErrorを投げる。
    """
    key = (language, env_type)
    if key not in PROFILES:
        raise KeyError(f"Profile not found for language={language}, env_type={env_type}")
    return PROFILES[key] 