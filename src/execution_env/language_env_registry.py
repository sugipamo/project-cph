from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.shell_process import ShellProcess
from typing import List
import os
import json

BASE_DIR = "contest_env"

# 言語ごとのenv.jsonをロード
def load_env_json(language: str, env: str) -> dict:
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    with open(json_path, "r") as f:
        return json.load(f)


def list_languages():
    pass

def list_language_envs():
    pass

def get_resource_handler(language: str, env: str):
    pass

class EnvResourceController:
    def __init__(self, language_name, env_type):
        self.language_name = language_name
        self.env_type = env_type
        if env_type == "docker":
            env_config = load_env_json(language_name, env_type)
            self.const_handler = DockerConstHandler(env_config)
            self.run_handler = DockerRunHandler(env_config)
            self.file_handler = DockerFileHandler(env_config)
        else:
            env_config = load_env_json(language_name, env_type)
            self.const_handler = LocalConstHandler(env_config)
            self.run_handler = LocalRunHandler(env_config)
            self.file_handler = LocalFileHandler(env_config)

    def run(self, cmd: List[str]) -> ShellProcess:
        return self.run_handler.run(cmd)

    def read_file(self, relative_path: str) -> str:
        return self.file_handler.read(relative_path)

    def write_file(self, relative_path: str, content: str):
        self.file_handler.write(relative_path, content)

    def file_exists(self, relative_path: str) -> bool:
        return self.file_handler.exists(relative_path) 
    

def get_resource_handler(language: str, env: str):
    return EnvResourceController(language, env)

