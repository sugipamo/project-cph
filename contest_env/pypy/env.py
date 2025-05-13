from contest_env.base import BaseLanguageConfig, ContainerTestHandler, LocalTestHandler, register_handler

class PypyConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5079"  # 例: AtCoder PyPy3 (7.3.0)
    source_file = "main.py"
    exclude_patterns = [r"^.*\\.log$", r"^debug.*"]  # moveignore相当

@register_handler("pypy", "container")
class PypyContainerHandler(ContainerTestHandler, PypyConfig):
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@register_handler("pypy", "local")
class PypyLocalHandler(LocalTestHandler, PypyConfig):
    dockerfile_path = None
    run_cmd = ["pypy3", "{source}"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 