import importlib
import os
import glob

# contest_env配下の *_config.py を動的にロード
LANGUAGE_CONFIGS = {}
config_files = glob.glob(os.path.join(os.path.dirname(__file__), '../../contest_env/*_config.py'))
for config_path in config_files:
    module_name = os.path.splitext(os.path.basename(config_path))[0]
    lang = module_name.replace('_config', '')
    mod = importlib.import_module(f'contest_env.{module_name}')
    configs = getattr(mod, f'{lang.upper()}_CONFIGS', None)
    if configs:
        for ver, conf in configs.items():
            LANGUAGE_CONFIGS[(lang, ver)] = conf

class LanguageEnvProfile:
    def __init__(self, language: str, version: str):
        self.language = language
        self.version = version
        self.config = LANGUAGE_CONFIGS[(language, version)]
        self.dockerfile_path = self.config["dockerfile_path"] 