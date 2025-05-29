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
        self.operations = []
        self.files = set()
        self.contents = dict()

    def resolve_path(self):
        return self.path.resolve()

    def makedirs(self, exist_ok=True):
        self.path.mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self):
        return self.path.is_dir()

    def glob(self, pattern):
        return list(self.base_dir.glob(pattern))

    def move(self):
        src_path = self.resolve_path()
        dst_path = self.dst_path.resolve()
        self.ensure_parent_dir(dst_path)
        self._move_impl(src_path, dst_path)

    def _move_impl(self, src_path, dst_path):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def copy(self):
        src_path = self.resolve_path()
        dst_path = self.dst_path.resolve()
        self.ensure_parent_dir(dst_path)
        self._copy_impl(src_path, dst_path)

    def _copy_impl(self, src_path, dst_path):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def exists(self):
        path = self.resolve_path()
        return self._exists_impl(path)

    def _exists_impl(self, path):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def create(self, content: str = ""):
        path = self.resolve_path()
        self.ensure_parent_dir(path)
        self._create_impl(path, content)

    def _create_impl(self, path, content):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def copytree(self):
        src_path = self.path.resolve()
        dst_path = self.dst_path.resolve()
        if src_path == dst_path:
            return
        self.ensure_parent_dir(dst_path)
        self._copytree_impl(src_path, dst_path)

    def _copytree_impl(self, src_path, dst_path):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def rmtree(self):
        p = self.resolve_path()
        self._rmtree_impl(p)

    def _rmtree_impl(self, p):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    def remove(self):
        p = self.resolve_path()
        self._remove_impl(p)

    def _remove_impl(self, p):
        # Local/Mock/Dummyでoverride
        raise NotImplementedError

    @abstractmethod
    def open(self, path, mode="r", encoding=None):
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

    @abstractmethod
    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        pass

    def mkdir(self):
        path = self.resolve_path()
        path.mkdir(parents=True, exist_ok=True)

    def touch(self):
        path = self.resolve_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def list_files(self, base_dir):
        """
        指定ディレクトリ以下の全ファイルパスをリストで返す（サブクラスで実装）
        """
        raise NotImplementedError

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