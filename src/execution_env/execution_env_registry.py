from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from src.shell_process import ShellProcess
from typing import List
import os
import json
from enum import Enum

BASE_DIR = "contest_env"

class EnvType(Enum):
    LOCAL = "local"
    DOCKER = "docker"

class EnvConfig:
    def __init__(self, data: dict):
        # 必須項目チェック
        if "env_type" not in data:
            raise ValueError("env_type is required in env.json")
        env_type_str = data["env_type"].lower()
        if env_type_str not in ("local", "docker"):
            raise ValueError(f"Unknown env_type: {env_type_str}")
        self.env_type = EnvType(env_type_str)
        # 他の項目も同様に
        self.contest_current_path = data.get("contest_current_path")
        self.source_file = data.get("source_file")
        self.contest_env_path = data.get("contest_env_path")
        self.contest_template_path = data.get("contest_template_path")
        self.contest_temp_path = data.get("contest_temp_path")
        # 必須項目のバリデーション例
        if not self.contest_current_path:
            raise ValueError("contest_current_path is required in env.json")
        if not self.source_file:
            raise ValueError("source_file is required in env.json")

    @classmethod
    def from_json(cls, path: str):
        with open(path, "r") as f:
            data = json.load(f)
        return cls(data)

def load_env_json(language: str, env: str) -> EnvConfig:
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    return EnvConfig.from_json(json_path)


def list_languages():
    pass

def list_language_envs():
    pass

class EnvResourceController:
    def __init__(self, language_name, env_type):
        self.language_name = language_name
        self.env_type = env_type
        env_config = load_env_json(language_name, env_type)
        if env_config.env_type == EnvType.DOCKER:
            self.const_handler = DockerConstHandler(env_config)
            self.run_handler = DockerRunHandler(env_config)
            self.file_handler = DockerFileHandler(env_config)
        else:
            self.const_handler = LocalConstHandler(env_config)
            self.run_handler = LocalRunHandler(env_config)
            self.file_handler = LocalFileHandler(env_config)

    def create_process_options(self, cmd: List[str]):
        return self.run_handler.create_process_options(cmd)

    def read_file(self, relative_path: str) -> str:
        return self.file_handler.read(relative_path)

    def write_file(self, relative_path: str, content: str):
        self.file_handler.write(relative_path, content)

    def file_exists(self, relative_path: str) -> bool:
        return self.file_handler.exists(relative_path) 

def get_resource_handler(language: str, env: str):
    return EnvResourceController(language, env)

