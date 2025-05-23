from pathlib import Path
from shutil import copy2
import shutil
from .file_driver import FileDriver

class LocalFileDriver(FileDriver):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self):
        src_path = self.path.resolve()
        dst_path = self.dst_path.resolve()
        self.ensure_parent_dir(dst_path)
        src_path.rename(dst_path)

    def copy(self):
        src_path = self.path.resolve()
        dst_path = self.dst_path.resolve()
        self.ensure_parent_dir(dst_path)
        copy2(src_path, dst_path)

    def exists(self):
        path = self.resolve_path()
        return path.exists()

    def create(self, content: str = ""):
        path = self.resolve_path()
        self.ensure_parent_dir(path)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

    def copytree(self):
        src_path = self.path.resolve()
        dst_path = self.dst_path.resolve()
        if src_path == dst_path:
            return
        self.ensure_parent_dir(dst_path)
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    def rmtree(self):
        p = self.resolve_path()
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def open(self, mode="r", encoding=None):
        return self.path.open(mode=mode, encoding=encoding)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        if docker_driver is None:
            raise ValueError("docker_driverが必要です")
        return docker_driver.cp(src, dst, container, to_container=to_container)

    def hash_file(self, path, algo='sha256'):
        import hashlib
        h = hashlib.new(algo)
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest() 