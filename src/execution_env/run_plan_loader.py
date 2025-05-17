import os
import json
from typing import List
from dataclasses import dataclass
# 新規追加: language, envtypeからEnvContextを生成
BASE_DIR = "contest_env"
OJ_ENV_PATH = os.path.join("src", "execution_env", "oj", "env.json")

@dataclass
class EnvContext:
    language: str
    env: str
    count: int = 1
    contest_current_path: str = None
    source_file: str = None
    source_file_name: str = None
    contest_env_path: str = None
    contest_template_path: str = None
    contest_temp_path: str = None
    language_id: str = None
    dockerfile_path: str = None
    env_type_conf: dict = None

    @classmethod
    def from_json(cls, language: str, env: str, count: int = 1):
        env_json = load_env_json(language, env)
        lang_conf = env_json.get(language, {})
        env_types = lang_conf.get("env_types", {})
        env_type_conf = env_types.get(env, {})
        return cls(
            language=language,
            env=env,
            count=count,
            contest_current_path=lang_conf.get("contest_current_path") or ".",
            source_file=lang_conf.get("source_file"),
            source_file_name=lang_conf.get("source_file_name"),
            contest_env_path=lang_conf.get("contest_env_path") or "env",
            contest_template_path=lang_conf.get("contest_template_path") or "template",
            contest_temp_path=lang_conf.get("contest_temp_path") or "temp",
            language_id=lang_conf.get("language_id"),
            dockerfile_path=env_type_conf.get("dockerfile_path"),
            env_type_conf=env_type_conf
        )

    def __post_init__(self):
        # デフォルトでは何もしない（from_jsonでのみenv.jsonをロード）
        pass

def load_env_json(language: str, env: str) -> dict:
    # 通常のenv.json
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    with open(json_path, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    return base_data

def list_languages() -> List[str]:
    base_dir = BASE_DIR
    if not os.path.exists(base_dir):
        return []
    langs = []
    for name in os.listdir(base_dir):
        lang_dir = os.path.join(base_dir, name)
        if os.path.isdir(lang_dir) and os.path.exists(os.path.join(lang_dir, "env.json")):
            langs.append(name)
    return langs

def list_language_envs() -> List[tuple]:
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

def load_env_context_from_language_env(language: str, env: str, count: int = 1) -> EnvContext:
    """
    language, envから設定ファイルパスを解決し、EnvContextを生成
    例: contest_env/python/env.json など
    """
    return EnvContext.from_json(language, env, count)
