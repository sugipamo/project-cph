from pathlib import Path
from src.operations.file.file_driver import FileDriver

class MockFileDriver(FileDriver):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def _move_impl(self, src_path, dst_path):
        self.ensure_parent_dir(dst_path)
        self.operations.append(("move", src_path, dst_path))
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def _copy_impl(self, src_path, dst_path):
        self.ensure_parent_dir(dst_path)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} が存在しません")
        self.operations.append(("copy", src_path, dst_path))
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents[src_path] if src_path in self.contents else ""

    def _exists_impl(self, path):
        return path in self.files

    def _create_impl(self, path, content):
        self.ensure_parent_dir(path)
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

    def _copytree_impl(self, src_path, dst_path):
        self.ensure_parent_dir(dst_path)
        self.operations.append(("copytree", src_path, dst_path))
        # モックなので、ディレクトリ構造の再現は省略

    def _rmtree_impl(self, p):
        self.operations.append(("rmtree", p))
        # ディレクトリ配下も含めて全て削除（モックなので単純化）
        to_remove = [x for x in self.files if str(x).startswith(str(p))]
        for x in to_remove:
            self.files.remove(x)
            self.contents.pop(x, None)

    def _remove_impl(self, p):
        self.operations.append(("remove", p))
        if p in self.files:
            self.files.remove(p)
            self.contents.pop(p, None)

    def open(self, mode="r", encoding=None):
        path = self.resolve_path()
        if mode.startswith("w"):
            def write_func(content):
                self.create(content)
            class Writer:
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def write(self, content): write_func(content)
            return Writer()
        elif mode.startswith("r"):
            class Reader:
                def __init__(self, content):
                    self._content = content
                    self._read = False
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def read(self):
                    if self._read: return ""
                    self._read = True
                    return self._content
            return Reader(self.contents[path] if path in self.contents else "")
        else:
            raise NotImplementedError(f"MockFileDriver.open: mode {mode} not supported")

    def ensure_parent_dir(self, path):
        parent = Path(path).parent
        self.files.add(parent)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        src_path = Path(src)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} が存在しません (docker_cp)")
        self.operations.append(("docker_cp", src, dst, container, to_container))
        return f"mock_docker_cp_{src}_{dst}_{container}_{to_container}"

    def hash_file(self, path, algo='sha256'):
        import hashlib
        h = hashlib.new(algo)
        content = self.contents[Path(path)] if Path(path) in self.contents else ""
        content = content.encode()
        h.update(content)
        return h.hexdigest() 