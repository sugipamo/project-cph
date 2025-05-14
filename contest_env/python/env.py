from contest_env.base import BaseLanguageConfig, DockerTestHandler, LocalTestHandler, register_handler

class PythonConfig(BaseLanguageConfig):
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2)
    source_file = "main.py"
    exclude_patterns = [r"^.*\\.log$", r"^debug.*"]  # moveignore相当

@register_handler
class PythonDockerHandler(DockerTestHandler, PythonConfig):
    language_name = "python"
    env_type = "docker"
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"]

@register_handler
class PythonLocalHandler(LocalTestHandler, PythonConfig):
    language_name = "python"
    env_type = "local"
    run_cmd = ["python3", "{source}"]