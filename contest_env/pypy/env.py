from contest_env.base import BaseLanguageEnv, ContainerTestHandler, LocalTestHandler

class PypyEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/pypy/Dockerfile"
    run_cmd = ["pypy3", "{source}"]
    LANGUAGE_ID = "5079"  # 例: AtCoder PyPy3 (7.3.0)

class PypyContainerHandler(ContainerTestHandler, PypyEnv):
    language_name = "pypy"
    env_type = "container"

class PypyLocalHandler(LocalTestHandler, PypyEnv):
    language_name = "pypy"
    env_type = "local" 