from contest_env.base import BaseLanguageEnv

class Pypy73Env(BaseLanguageEnv):
    dockerfile_path = "contest_env/pypy_7_3.Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    # build_cmd, source_file, copy_modeはbaseのデフォルトを利用 