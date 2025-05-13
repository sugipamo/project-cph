import importlib
import pkgutil
import os
import inspect
from contest_env.base import BaseTestHandler

# --- 言語ごとのハンドラ ---
HANDLERS = {}
contest_env_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../contest_env')
for lang_name in os.listdir(contest_env_dir):
    lang_dir = os.path.join(contest_env_dir, lang_name)
    if not os.path.isdir(lang_dir) or lang_name.startswith("__"):
        continue
    env_path = os.path.join(lang_dir, "env.py")
    if not os.path.exists(env_path):
        continue
    mod = importlib.import_module(f"contest_env.{lang_name}.env")
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, BaseTestHandler) and obj is not BaseTestHandler:
            if getattr(obj, "language_name", None) and getattr(obj, "env_type", None):
                HANDLERS[(obj.language_name, obj.env_type)] = obj

def get_handler(language, env_type):
    return HANDLERS[(language, env_type)] 