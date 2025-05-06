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
        cmd = ["sh", "-c", f"python3 .temp/main.py < {in_file}"]
        return ctl.exec_in_container(container, cmd)

class PypyTestHandler(TestLanguageHandler):
    def build(self, ctl, container, temp_source_path):
        return True, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        cmd = ["sh", "-c", f"pypy3 .temp/main.py < {in_file}"]
        return ctl.exec_in_container(container, cmd)

class RustTestHandler(TestLanguageHandler):
    def build(self, ctl, container, temp_source_path):
        cmd = ["rustc", "/workspace/.temp/main.rs", "-o", "/workspace/.temp/a.out"]
        result = ctl.exec_in_container(container, cmd)
        # ctl.exec_in_containerの返り値がタプルでなければタプル化
        if isinstance(result, tuple) and len(result) == 3:
            return result
        else:
            return result, "", ""
    def run(self, ctl, container, in_file, temp_source_path):
        cmd = ["sh", "-c", f"/workspace/.temp/a.out < {in_file}"]
        return ctl.exec_in_container(container, cmd)

HANDLERS = {
    "python": PythonTestHandler(),
    "pypy": PypyTestHandler(),
    "rust": RustTestHandler(),
} 