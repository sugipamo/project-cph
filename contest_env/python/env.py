from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class PythonConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2)
    source_file = "main.py"
    exclude_patterns = [r"^.*\\.log$", r"^debug.*"]  # moveignore相当

@register_handler
class PythonContainerHandler(ContainerTestHandler, PythonConfig):
    language_name = "python"
    env_type = "docker"
    default_config_class = PythonConfig
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"]
    def __init__(self, env_type, config=None, env_config=None, *args, **kwargs):
        super().__init__(env_type, config=config, env_config=env_config, *args, **kwargs)

@register_handler
class PythonLocalHandler(LocalTestHandler, PythonConfig):
    language_name = "python"
    env_type = "local"
    default_config_class = PythonConfig
    dockerfile_path = None  # localはdockerfile不要
    run_cmd = ["python3", "{source}"]
    def __init__(self, env_type, config=None, env_config=None, *args, **kwargs):
        super().__init__(env_type, config=config, env_config=env_config, *args, **kwargs) 