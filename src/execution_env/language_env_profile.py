from .language_config import LanguageConfig
from .execution_env_config import ExecutionEnvConfig

class LanguageEnvProfile:
    def __init__(self, language_config: LanguageConfig, env_config: ExecutionEnvConfig):
        self.language_config = language_config
        self.env_config = env_config 