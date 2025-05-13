from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class PythonConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2)

@register_handler("python", "container")
class PythonContainerHandler(ContainerTestHandler, PythonConfig):
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"]
    def __init__(self, language, env_type, config=None, env_config=None):
        config = config or PythonConfig()
        super().__init__(language, env_type, config=config, env_config=env_config)

@register_handler("python", "local")
class PythonLocalHandler(LocalTestHandler, PythonConfig):
    dockerfile_path = None  # localはdockerfile不要
    run_cmd = ["python3", "{source}"]
    def __init__(self, language, env_type, config=None, env_config=None):
        config = config or PythonConfig()
        super().__init__(language, env_type, config=config, env_config=env_config) 