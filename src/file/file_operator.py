from pathlib import Path
from abc import ABC, abstractmethod
from shutil import copy2
import shutil

class FileOperator(ABC):
    def __init__(self, base_dir=Path(".")):
        self.base_dir = Path(base_dir)

    def resolve_path(self):
        return self.path.resolve()

    def makedirs(self, exist_ok=True):
        self.path.mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self):
        return self.path.is_dir()

    def glob(self, pattern):
        # patternはbase_dirからの相対パターン
        return list(self.base_dir.glob(pattern))

    def remove(self):
        self.path.unlink()

    def rmtree(self):
        shutil.rmtree(self.path)

    def open(self, mode="r", encoding=None):
        return self.path.open(mode=mode, encoding=encoding)

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

class MockFileOperator(FileOperator):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("move", src_path, dst_path))
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def copy(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("copy", src_path, dst_path))
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.get(src_path, "")

    def exists(self):
        path = self.resolve_path()
        return path in self.files

    def create(self, content: str = ""):
        path = self.resolve_path()
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

    def copytree(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("copytree", src_path, dst_path))
        # モックなので、ディレクトリ構造の再現は省略

class LocalFileOperator(FileOperator):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)

    def copy(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src_path, dst_path)

    def exists(self):
        path = self.resolve_path()
        return path.exists()

    def create(self, content: str = ""):
        path = self.resolve_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

    def copytree(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        # srcとdstが同じ場合は何もしない
        if src_path.resolve() == dst_path.resolve():
            return
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

    def rmtree(self):
        p = self.resolve_path()
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

class DummyFileOperator(FileOperator):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("move", src_path, dst_path))
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def copy(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("copy", src_path, dst_path))
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.get(src_path, "")

    def exists(self):
        path = self.resolve_path()
        return path in self.files

    def create(self, content: str = ""):
        path = self.resolve_path()
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

    def copytree(self):
        src_path = self.resolve_path()
        dst_path = self.resolve_path()
        self.operations.append(("copytree", src_path, dst_path))

    def rmtree(self):
        path = self.resolve_path()
        self.operations.append(("rmtree", path))
        if path in self.files:
            self.files.remove(path)
            self.contents.pop(path, None)

    def isdir(self):
        path = self.resolve_path()
        # テスト用: ディレクトリは"/"で終わるパスと仮定
        return str(path).endswith("/") 