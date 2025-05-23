"""
file_driver.py
operations層のFileRequest等から利用される、ファイル操作の実体（バックエンド）実装。
ローカル・モック・ダミーなど複数の実装を提供する。
"""
from pathlib import Path
from abc import ABC, abstractmethod
from shutil import copy2
import shutil

class FileDriver(ABC):
    def __init__(self, base_dir=Path(".")):
        self.base_dir = Path(base_dir)

    def resolve_path(self):
        return self.path.resolve()

    def makedirs(self, exist_ok=True):
        self.path.mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self):
        return self.path.is_dir()

    def glob(self, pattern):
        return list(self.base_dir.glob(pattern))

    def remove(self):
        self.path.unlink()

    def rmtree(self):
        shutil.rmtree(self.path)

    @abstractmethod
    def open(self, mode="r", encoding=None):
        pass

    @abstractmethod
    def move(self):
        pass

    @abstractmethod
    def copy(self):
        pass

    @abstractmethod
    def exists(self):
        pass

    @abstractmethod
    def create(self, content: str = ""):
        pass

    @abstractmethod
    def copytree(self):
        pass

    @abstractmethod
    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        pass

    def ensure_parent_dir(self, path):
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

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

class FileUtil:
    @staticmethod
    def hash_file(path, algo='sha256'):
        import hashlib
        h = hashlib.new(algo)
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def ensure_parent_dir(path):
        from pathlib import Path
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def glob(base_dir, pattern):
        return list(base_dir.glob(pattern))

    @staticmethod
    def isdir(path):
        return path.is_dir()

    @staticmethod
    def makedirs(path, exist_ok=True):
        path.mkdir(parents=True, exist_ok=exist_ok) 