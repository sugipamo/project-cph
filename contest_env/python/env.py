from contest_env.base import BaseLanguageEnv

class PythonEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"] 