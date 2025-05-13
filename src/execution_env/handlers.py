import importlib
import pkgutil
import os
import inspect
import sys
from contest_env.base import BaseTestHandler

# --- 言語ごとのハンドラ ---
HANDLERS = {}

# contest_env配下の全env.pyを動的にimport
contest_env_dir = os.path.join(os.path.dirname(__file__), '../../contest_env')
contest_env_dir = os.path.abspath(contest_env_dir)
if contest_env_dir not in sys.path:
    sys.path.insert(0, contest_env_dir)
for lang in os.listdir(contest_env_dir):
    lang_dir = os.path.join(contest_env_dir, lang)
    env_path = os.path.join(lang_dir, 'env.py')
    if os.path.isdir(lang_dir) and os.path.exists(env_path):
        importlib.import_module(f'contest_env.{lang}.env')

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

def get_handler(language, env_type, *args, **kwargs):
    cls = HANDLERS[(language, env_type)]
    return cls(language, env_type, *args, **kwargs) 