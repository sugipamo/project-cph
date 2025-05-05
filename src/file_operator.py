from pathlib import Path
from abc import ABC, abstractmethod
from shutil import copy2
import glob as pyglob
import shutil

class FileOperator(ABC):
    def __init__(self, base_dir=Path(".")):
        self.base_dir = Path(base_dir)

    def resolve_path(self, path):
        if isinstance(path, Path):
            return self.base_dir / path
        return self.base_dir / Path(path)

    def makedirs(self, path, exist_ok=True):
        self.resolve_path(path).mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self, path):
        return self.resolve_path(path).is_dir()

    def glob(self, pattern):
        # patternはbase_dirからの相対パターン
        return list(self.base_dir.glob(pattern))

    def remove(self, path):
        self.resolve_path(path).unlink()

    def rmtree(self, path):
        shutil.rmtree(self.resolve_path(path))

    def open(self, path, mode="r", encoding=None):
        return open(self.resolve_path(path), mode, encoding=encoding)

    @abstractmethod
    def move(self, src: Path, dst: Path):
        pass

    @abstractmethod
    def copy(self, src: Path, dst: Path):
        pass

    @abstractmethod
    def exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    def create(self, path: Path, content: str = ""):
        pass

    @abstractmethod
    def copytree(self, src: Path, dst: Path):
        pass

class MockFileOperator(FileOperator):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self, src: Path, dst: Path):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        self.operations.append(("move", src_path, dst_path))
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def copy(self, src: Path, dst: Path):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        self.operations.append(("copy", src_path, dst_path))
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.get(src_path, "")

    def exists(self, path: Path) -> bool:
        path = self.resolve_path(path)
        return path in self.files

    def create(self, path: Path, content: str = ""):
        path = self.resolve_path(path)
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

    def copytree(self, src: Path, dst: Path):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        self.operations.append(("copytree", src_path, dst_path))
        # モックなので、ディレクトリ構造の再現は省略

class LocalFileOperator(FileOperator):
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)

    def move(self, src, dst):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)

    def copy(self, src, dst):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src_path, dst_path)

    def exists(self, path) -> bool:
        path = self.resolve_path(path)
        return path.exists()

    def create(self, path, content: str = ""):
        path = self.resolve_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def copytree(self, src, dst):
        src_path = self.resolve_path(src)
        dst_path = self.resolve_path(dst)
        # srcとdstが同じ場合は何もしない
        if src_path.resolve() == dst_path.resolve():
            return
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True) 