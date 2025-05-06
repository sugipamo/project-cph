from src.docker.path_mapper import DockerPathMapper
import os
HOST_PROJECT_ROOT = __import__('os').path.abspath('.')
CONTAINER_WORKSPACE = '/workspace'
path_mapper = DockerPathMapper(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE)

class TestLanguageHandler:
    def build(self, ctl, container, temp_source_path):
        # Python, Pypyはビルド不要なので常に成功扱い
        return True, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        raise NotImplementedError

class PythonTestHandler(TestLanguageHandler):
    def build(self, ctl, container, temp_source_path):
        return True, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        main_py = path_mapper.to_container_path('.temp/main.py')
        cmd = ["sh", "-c", f"python3 {main_py} < {in_file}"]
        return ctl.exec_in_container(container, cmd)

class PypyTestHandler(TestLanguageHandler):
    def build(self, ctl, container, temp_source_path):
        return True, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        main_py = path_mapper.to_container_path('.temp/main.py')
        cmd = ["sh", "-c", f"pypy3 {main_py} < {in_file}"]
        return ctl.exec_in_container(container, cmd)

class RustTestHandler(TestLanguageHandler):
    def build(self, ctl, container, temp_source_path):
        main_rs = path_mapper.to_container_path(os.path.abspath('.temp/main.rs'))
        out_path = path_mapper.to_container_path(os.path.abspath('.temp/a.out'))
        cmd = ["rustc", main_rs, "-o", out_path]
        result = ctl.exec_in_container(container, cmd)
        if isinstance(result, tuple) and len(result) == 3:
            return result
        else:
            return result, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        out_path = path_mapper.to_container_path(os.path.abspath('.temp/a.out'))
        in_file = path_mapper.to_container_path(in_file)
        cmd = ["sh", "-c", f"{out_path} < {in_file}"]
        return ctl.exec_in_container(container, cmd)

HANDLERS = {
    "python": PythonTestHandler(),
    "pypy": PypyTestHandler(),
    "rust": RustTestHandler(),
} 