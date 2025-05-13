from contest_env.base import BaseLanguageEnv, ContainerTestHandler, LocalTestHandler, register_handler

class PythonConfig(BaseLanguageEnv):
    LANGUAGE_ID = "5078"  # 例: AtCoder Python3 (3.8.2)

@register_handler("python", "container")
class PythonContainerHandler(ContainerTestHandler, PythonConfig):
    dockerfile_path = "contest_env/python/Dockerfile"
    run_cmd = ["python3", "{source}"]

@register_handler("python", "local")
class PythonLocalHandler(LocalTestHandler, PythonConfig):
    dockerfile_path = None  # localはdockerfile不要
    run_cmd = ["python3", "{source}"] 