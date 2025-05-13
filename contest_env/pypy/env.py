from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class PypyConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5079"  # 例: AtCoder PyPy3 (7.3.0)
    source_file = "main.py"
    exclude_patterns = [r"^.*\\.log$", r"^debug.*"]  # moveignore相当

@register_handler
class PypyContainerHandler(ContainerTestHandler, PypyConfig):
    language_name = "pypy"
    env_type = "docker"
    default_config_class = PypyConfig
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, env_type, config=None, env_config=None, *args, **kwargs):
        super().__init__(env_type, config=config, env_config=env_config, *args, **kwargs)

@register_handler
class PypyLocalHandler(LocalTestHandler, PypyConfig):
    language_name = "pypy"
    env_type = "local"
    default_config_class = PypyConfig
    dockerfile_path = None
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, env_type, config=None, env_config=None, *args, **kwargs):
        super().__init__(env_type, config=config, env_config=env_config, *args, **kwargs) 