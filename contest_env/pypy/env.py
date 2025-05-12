from contest_env.base import BaseLanguageEnv

class PypyEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"] 