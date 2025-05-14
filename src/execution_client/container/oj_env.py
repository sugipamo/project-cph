from src.execution_env.language_env_base import DockerTestHandler, LocalTestHandler
from dataclasses import dataclass

@dataclass
class OjDockerHandler(DockerTestHandler):
    language_name = "oj"
    env_type = "docker"
    run_cmd = ["oj"]

    def get_language_name(self):
        return self.language_name

@dataclass
class OjLocalHandler(LocalTestHandler):
    language_name = "oj"
    env_type = "local"
    run_cmd = ["oj"]

    def get_language_name(self):
        return self.language_name

    @property
    def dockerfile_path(self):
        return self.contest_env_path / ".." / "src" / "execution_client" / "container" / "oj.Dockerfile"