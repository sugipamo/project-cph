from pathlib import Path
from abc import ABC, abstractmethod
from shutil import copy2

class FileOperator(ABC):
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

class MockFileOperator(FileOperator):
    def __init__(self):
        self.operations = []
        self.files = set()
        self.contents = dict()

    def move(self, src: Path, dst: Path):
        self.operations.append(("move", src, dst))
        if src in self.files:
            self.files.remove(src)
            self.files.add(dst)
            self.contents[dst] = self.contents.pop(src, "")

    def copy(self, src: Path, dst: Path):
        self.operations.append(("copy", src, dst))
        if src in self.files:
            self.files.add(dst)
            self.contents[dst] = self.contents.get(src, "")

    def exists(self, path: Path) -> bool:
        return path in self.files

    def create(self, path: Path, content: str = ""):
        self.operations.append(("create", path, content))
        self.files.add(path)
        self.contents[path] = content

class LocalFileOperator(FileOperator):
    def move(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)

    def copy(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy2(src, dst)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def create(self, path: Path, content: str = ""):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content) 