from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class PypyConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5079"  # 例: AtCoder PyPy3 (7.3.0)

@register_handler("pypy", "container")
class PypyContainerHandler(ContainerTestHandler, PypyConfig):
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, language, env_type, config=None, env_config=None):
        config = config or PypyConfig()
        super().__init__(language, env_type, config=config, env_config=env_config)

@register_handler("pypy", "local")
class PypyLocalHandler(LocalTestHandler, PypyConfig):
    dockerfile_path = None
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, language, env_type, config=None, env_config=None):
        config = config or PypyConfig()
        super().__init__(language, env_type, config=config, env_config=env_config) 