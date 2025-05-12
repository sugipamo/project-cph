import importlib
import os
import glob
import re

# contest_env配下の *_config.py を動的にロード
LANGUAGE_CONFIGS = {}
config_files = glob.glob(os.path.join(os.path.dirname(__file__), '../../contest_env/*_config.py'))
for config_path in config_files:
    module_name = os.path.splitext(os.path.basename(config_path))[0]
    # 例: pypy_7_3_config → lang: pypy, ver: 7.3
    m = re.match(r'([a-zA-Z0-9]+)_([0-9_]+)_config', module_name)
    if not m:
        continue
    lang = m.group(1)
    ver = m.group(2).replace('_', '.')
    mod = importlib.import_module(f'contest_env.{module_name}')
    conf = getattr(mod, 'CONFIG', None)
    if conf:
        LANGUAGE_CONFIGS[(lang, ver)] = conf

class LanguageEnvProfile:
    def __init__(self, language: str, version: str):
        self.language = language
        self.version = version
        self.config = LANGUAGE_CONFIGS[(language, version)]
        self.dockerfile_path = self.config["dockerfile_path"] 