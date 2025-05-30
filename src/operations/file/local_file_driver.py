from pathlib import Path
from shutil import copy2
import shutil
from .file_driver import FileDriver
import os

class LocalFileDriver(FileDriver):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)

    def _move_impl(self, src_path, dst_path):
        # Use shutil.move for better handling of directories and cross-filesystem moves
        shutil.move(str(src_path), str(dst_path))

    def _copy_impl(self, src_path, dst_path):
        copy2(src_path, dst_path)

    def _exists_impl(self, path):
        return path.exists()

    def _create_impl(self, path, content):
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

    def _copytree_impl(self, src_path, dst_path):
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    def _rmtree_impl(self, p):
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    def _remove_impl(self, p):
        if p.exists():
            p.unlink()

    def open(self, path, mode="r", encoding=None):
        return Path(path).open(mode=mode, encoding=encoding)

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

    def list_files(self, base_dir):
        import os
        from pathlib import Path
        base = self.base_dir / base_dir
        result = []
        for root, dirs, files in os.walk(base):
            for file in files:
                result.append(str(Path(root) / file))
        return result 