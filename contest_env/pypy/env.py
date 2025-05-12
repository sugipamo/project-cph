from contest_env.base import BaseLanguageEnv

class PypyEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    LANGUAGE_ID = "5079"  # 例: AtCoder PyPy3 (7.3.0) 