from contest_env.base import BaseLanguageEnv

class Python38Env(BaseLanguageEnv):
    dockerfile_path = "contest_env/python_3_8.Dockerfile"
    run_cmd = ["python3", "{source}"]
    # build_cmd, source_file, copy_modeはbaseのデフォルトを利用 