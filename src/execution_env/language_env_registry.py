"""
このファイルは言語環境拡張用の基底クラスと、言語環境レジストリ機能を兼ねます。
"""
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import json
import os
import subprocess

# === コマンド展開用関数 ===
def expand_cmd(cmd_list: List[str], handler: 'BaseTestHandler') -> List[str]:
    # handlerの属性をdict化
    context = {
        "contest_current": str(handler.contest_current_path),
        "contest_env": str(handler.contest_env_path),
        "contest_template": str(handler.contest_template_path),
        "contest_temp": str(handler.contest_temp_path),
        "source_file": handler.source_file,
        "time_limit": handler.time_limit,
        "run_cmd": handler.run_cmd,
        "build_cmd": getattr(handler, "build_cmd", None),
    }
    return [s.format(**context) for s in cmd_list]

# === 基底クラス ===
@dataclass
class BaseTestHandler(ABC):
    contest_current_path: Path = Path("./contest_current")
    contest_env_path: Path = Path("./contest_env")
    contest_template_path: Path = Path("./contest_template")
    contest_temp_path: Path = Path("./.temp")
    source_file: Optional[str] = None
    time_limit: Optional[int] = None
    language_name: Optional[str] = None
    env_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    @abstractmethod
    def run(self, cmd: List[str]) -> str:
        """
        任意のコマンドを実行する
        """
        pass

@dataclass
class LocalTestHandler(BaseTestHandler):
    def run(self, cmd: List[str]) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.contest_current_path)
        return result.stdout

@dataclass
class DockerTestHandler(BaseTestHandler):
    container_workspace: str = "/workspace"
    memory_limit: Optional[int] = None
    def run(self, cmd: List[str]) -> str:
        # 実際のdocker exec等はここで実装（例示）
        docker_cmd = [
            "docker", "exec", self.config.get("container_name", "cph_default"),
        ] + cmd
        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        return result.stdout

# === jsonベースのレジストリ ===
BASE_DIR = "contest_env"

# 言語ごとのenv.jsonをロード
def _load_env_json(language: str) -> dict:
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    with open(json_path, "r") as f:
        return json.load(f)

def list_languages():
    # contest_env配下のディレクトリを列挙し、env.jsonがあるものを言語とみなす
    langs = []
    for name in os.listdir(BASE_DIR):
        lang_dir = os.path.join(BASE_DIR, name)
        if os.path.isdir(lang_dir) and os.path.exists(os.path.join(lang_dir, "env.json")):
            langs.append(name)
    return sorted(langs)

def list_language_envs():
    # 各env.jsonのhandlersキーから(env, type)のペアを列挙
    envs = []
    for lang in list_languages():
        data = _load_env_json(lang)
        handlers = data.get("handlers", {})
        for env_type in handlers.keys():
            envs.append((lang, env_type))
    return sorted(envs)

def get_test_handler(language: str, env: str, config: Optional[Dict[str, Any]] = None):
    data = _load_env_json(language)
    handlers = data.get("handlers", {})
    if env not in handlers:
        raise ValueError(f"Handler not found for language={language}, env={env}")
    handler_cls = DockerTestHandler if env == "docker" else LocalTestHandler
    return handler_cls(
        language_name=language,
        env_type=env,
        source_file=data.get("source_file"),
        config=config,
    )

class EnvController:
    def __init__(self, language_name, env_type, config=None):
        self.language_name = language_name
        self.env_type = env_type
        self.handler = get_test_handler(language=language_name, env=env_type, config=config)
    def run(self, cmd: List[str]) -> str:
        return self.handler.run(cmd)