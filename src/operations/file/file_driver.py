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

class MockFileDriver(FileDriver):
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
            self.contents[dst_path] = self.contents.get(src_path, "")

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
        # モックなので、ディレクトリ構造の再現は省略

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
            return Reader(self.contents.get(path, ""))
        else:
            raise NotImplementedError(f"MockFileDriver.open: mode {mode} not supported")

    def ensure_parent_dir(self, path):
        parent = Path(path).parent
        self.files.add(parent)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        self.operations.append(("docker_cp", src, dst, container, to_container))
        return f"mock_docker_cp_{src}_{dst}_{container}_{to_container}"

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
            self.contents[dst_path] = self.contents.get(src_path, "")

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