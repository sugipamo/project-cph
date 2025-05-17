from src.execution_env.resource_handler.file_handler import DockerFileHandler, LocalFileHandler
from src.execution_env.resource_handler.run_handler import LocalRunHandler, DockerRunHandler
from src.execution_env.resource_handler.const_handler import DockerConstHandler, LocalConstHandler
from typing import List
import os
import json
from enum import Enum
from src.operations.di_container import DIContainer

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
    base_dir = BASE_DIR
    if not os.path.exists(base_dir):
        return []
    langs = []
    for name in os.listdir(base_dir):
        lang_dir = os.path.join(base_dir, name)
        if os.path.isdir(lang_dir) and os.path.exists(os.path.join(lang_dir, "env.json")):
            langs.append(name)
    return langs

def list_language_envs():
    base_dir = BASE_DIR
    if not os.path.exists(base_dir):
        return []
    result = []
    for name in os.listdir(base_dir):
        lang_dir = os.path.join(base_dir, name)
        env_json_path = os.path.join(lang_dir, "env.json")
        if os.path.isdir(lang_dir) and os.path.exists(env_json_path):
            try:
                with open(env_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # env.jsonのトップレベルキーが言語名
                lang_data = data.get(name)
                if not lang_data:
                    continue
                handlers = lang_data.get("handlers", {})
                for env_type in ("local", "docker"):
                    if env_type in handlers:
                        result.append((name, env_type))
            except Exception:
                continue
    return result

class EnvResourceController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        # テスト用: 依存注入があればそれを使う
        if file_handler is not None:
            self.language_name = language_name
            self.env_type = env_type
            self.const_handler = const_handler
            self.run_handler = run_handler
            self.file_handler = file_handler
            return
        self.language_name = language_name
        self.env_type = env_type
        env_config = load_env_json(language_name, env_type)
        # DIコンテナのセットアップ
        container = DIContainer()
        # provider登録
        container.register("LocalConstHandler", lambda: LocalConstHandler(env_config))
        container.register("DockerConstHandler", lambda: DockerConstHandler(env_config))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_config, container.resolve("LocalConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_config, container.resolve("DockerConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_config, container.resolve("LocalConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_config, container.resolve("DockerConstHandler")))
        # HandlerのDI取得
        if env_config.env_type == EnvType.DOCKER:
            self.const_handler = container.resolve("DockerConstHandler")
            self.run_handler = container.resolve("DockerRunHandler")
            self.file_handler = container.resolve("DockerFileHandler")
        else:
            self.const_handler = container.resolve("LocalConstHandler")
            self.run_handler = container.resolve("LocalRunHandler")
            self.file_handler = container.resolve("LocalFileHandler")

    def create_process_options(self, cmd: List[str]):
        return self.run_handler.create_process_options(cmd)

    def read_file(self, relative_path: str) -> str:
        return self.file_handler.read(relative_path)

    def write_file(self, relative_path: str, content: str):
        self.file_handler.write(relative_path, content)

    def file_exists(self, relative_path: str) -> bool:
        return self.file_handler.exists(relative_path)

    def remove_file(self, relative_path: str):
        return self.file_handler.remove(relative_path)

    def move_file(self, src_path: str, dst_path: str):
        return self.file_handler.move(src_path, dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return self.file_handler.copytree(src_path, dst_path)

    def rmtree(self, dir_path: str):
        return self.file_handler.rmtree(dir_path)

    def copy_file(self, src_path: str, dst_path: str):
        return self.file_handler.copy(src_path, dst_path)

def get_resource_handler(language: str, env: str):
    return EnvResourceController(language, env)

