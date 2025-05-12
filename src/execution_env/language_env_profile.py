import importlib
import os
import glob
import re
import inspect
from contest_env.base import BaseLanguageEnv

# contest_env配下の *_env.py を動的にロード
LANGUAGE_ENVS = {}
env_files = glob.glob(os.path.join(os.path.dirname(__file__), '../../contest_env/*_env.py'))
for env_path in env_files:
    module_name = os.path.splitext(os.path.basename(env_path))[0]
    # 例: pypy_7_3_env → lang: pypy, ver: 7.3
    m = re.match(r'([a-zA-Z0-9]+)_([0-9_]+)_env', module_name)
    if not m:
        continue
    lang = m.group(1)
    ver = m.group(2).replace('_', '.')
    mod = importlib.import_module(f'contest_env.{module_name}')
    # BaseLanguageEnvのサブクラスを探す
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, BaseLanguageEnv) and obj is not BaseLanguageEnv:
            LANGUAGE_ENVS[(lang, ver)] = obj

class LanguageEnvProfile:
    def __init__(self, language: str, version: str):
        self.language = language
        self.version = version
        self.env_class = LANGUAGE_ENVS[(language, version)]
        self.env = self.env_class()  # インスタンス化
        self.dockerfile_path = self.env.dockerfile_path
        # 必要に応じて他のプロパティも参照可能 