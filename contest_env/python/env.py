from contest_env.base import DockerTestHandler, LocalTestHandler, register_handler
from dataclasses import dataclass

@dataclass
class PythonConfig():
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2)
    source_file = "main.py"
    exclude_patterns = [r"^.*\\.log$", r"^debug.*"]  # moveignore相当

@dataclass
@register_handler
class PythonDockerHandler(DockerTestHandler, PythonConfig):
    language_name = "python"
    env_type = "docker"
    run_cmd = ["python3", "{source}"]

    def get_language_name(self):
        return self.language_name

@dataclass
@register_handler
class PythonLocalHandler(LocalTestHandler, PythonConfig):
    language_name = "python"
    env_type = "local"
    run_cmd = ["python3", "{source}"]

    def get_language_name(self):
        return self.language_name
