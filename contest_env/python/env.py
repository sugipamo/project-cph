from contest_env.base import BaseLanguageEnv, ContainerTestHandler, LocalTestHandler

class PythonEnv(BaseLanguageEnv):
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"]
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2) 

class PythonContainerHandler(ContainerTestHandler, PythonEnv):
    language_name = "python"
    env_type = "container"
    
class PythonLocalHandler(LocalTestHandler, PythonEnv):
    language_name = "python"
    env_type = "local" 