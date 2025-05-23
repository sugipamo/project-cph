from pathlib import Path
from src.operations.file.file_driver import FileDriver

class DummyFileDriver(FileDriver):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.ensure_parent_dir(dst_path)
        self.operations.append(("move", src_path, dst_path))
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def copy(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.ensure_parent_dir(dst_path)
        self.operations.append(("copy", src_path, dst_path))
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents[src_path] if src_path in self.contents else ""

    def exists(self):
        path = self.resolve_path()
        return path in self.files

    def create(self, content: str = ""):
        path = self.resolve_path()
        self.ensure_parent_dir(path)
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

    def copytree(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.ensure_parent_dir(dst_path)
        self.operations.append(("copytree", src_path, dst_path))

    def rmtree(self):
        path = self.resolve_path()
        self.operations.append(("rmtree", path))
        if path in self.files:
            self.files.remove(path)
            self.contents.pop(path, None)

    def isdir(self):
        path = self.resolve_path()
        return str(path).endswith("/")

    def open(self, mode="r", encoding=None):
        class Dummy:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def read(self): return ""
            def write(self, content): pass
        return Dummy()

    def ensure_parent_dir(self, path):
        parent = Path(path).parent
        self.files.add(parent)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        pass

    def hash_file(self, path, algo='sha256'):
        return 'dummyhash' 