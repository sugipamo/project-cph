import importlib
import os
import inspect
from contest_env.base import BaseLanguageEnv

LANGUAGE_ENVS = {}
contest_env_dir = os.path.join(os.path.dirname(__file__), '../../contest_env')
for lang in os.listdir(contest_env_dir):
    lang_dir = os.path.join(contest_env_dir, lang)
    env_path = os.path.join(lang_dir, 'env.py')
    if os.path.isdir(lang_dir) and os.path.exists(env_path):
        mod = importlib.import_module(f'contest_env.{lang}.env')
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, BaseLanguageEnv) and obj is not BaseLanguageEnv:
                LANGUAGE_ENVS[lang] = obj

class LanguageEnvProfile:
    def __init__(self, language: str):
        self.language = language
        self.env_class = LANGUAGE_ENVS[language]
        self.env = self.env_class()  # インスタンス化
        self.dockerfile_path = self.env.dockerfile_path
        # 必要に応じて他のプロパティも参照可能 