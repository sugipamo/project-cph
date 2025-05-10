import os
from src.language_env.language_config import LANGUAGE_CONFIGS

class RunLanguageHandler:
    def build(self, manager, name, temp_source_path, language_name):
        config = LANGUAGE_CONFIGS[language_name]
        if config.build_cmd:
            # Rustなどビルドが必要な場合
            cmd = [c.format(bin_path=config.bin_path or "", source=temp_source_path) for c in config.build_cmd]
            result = manager.run_and_measure(name, cmd, timeout=None, cwd=os.path.abspath(temp_source_path))
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr
        else:
            # Python, Pypyなどビルド不要
            return True, "", ""

    def run(self, manager, name, in_file, temp_source_path, language_name, host_in_file=None):
        config = LANGUAGE_CONFIGS[language_name]
        run_cmd = [c.format(bin_path=config.bin_path or "", source=temp_source_path) for c in config.run_cmd]
        if hasattr(manager, 'exec_in_container'):
            if host_in_file is None:
                raise ValueError("host_in_file must be provided for container execution")
            with open(host_in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            result = manager.exec_in_container(name, run_cmd, stdin=input_data)
            ok = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            return ok, stdout, stderr
        else:
            with open(in_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            result = manager.run_and_measure(name, run_cmd, timeout=None, input=input_data)
            ok = result.returncode == 0
            return ok, result.stdout, result.stderr

RUN_HANDLERS = {k: RunLanguageHandler() for k in LANGUAGE_CONFIGS.keys()} 