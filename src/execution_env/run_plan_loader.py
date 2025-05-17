import os
import json
from typing import List
from dataclasses import dataclass
# 新規追加: language, envtypeからRunPlanを生成
BASE_DIR = "contest_env"

@dataclass
class RunPlan:
    language: str
    env: str
    count: int = 1
    # 今後必要なら追加パラメータもここに

def load_run_plans_from_json(path: str) -> List[RunPlan]:
    """
    指定パスのjsonファイルからRunPlanのリストを生成して返す
    例：
    [
        {"language": "python", "env": "docker", "count": 2},
        {"language": "cpp", "env": "local", "count": 1}
    ]
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    run_plans = [RunPlan(**item) for item in data]
    return run_plans


def load_env_json(language: str, env: str) -> dict:
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

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

def load_run_plan_from_language_env(language: str, env: str, count: int = 1) -> RunPlan:
    """
    language, envから設定ファイルパスを解決し、RunPlanを生成
    例: contest_env/python/env.json など
    """
    json_path = os.path.join(BASE_DIR, language, "env.json")
    if not os.path.exists(json_path):
        raise ValueError(f"env.json not found for language={language}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 必要なパラメータをenv.jsonから取得
    # ここでは例としてlanguage, env, countのみをRunPlanに渡す
    return RunPlan(language=language, env=env, count=count) 