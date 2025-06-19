"""OSプロバイダー - 副作用を集約"""
from abc import ABC, abstractmethod
from typing import List, Optional


class OsProvider(ABC):
    """OS操作の抽象インターフェース"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """パス存在チェック"""
        pass

    @abstractmethod
    def listdir(self, path: str) -> List[str]:
        """ディレクトリ内容一覧"""
        pass

    @abstractmethod
    def makedirs(self, path: str, exist_ok: bool = False) -> None:
        """ディレクトリ作成"""
        pass

    @abstractmethod
    def remove(self, path: str) -> None:
        """ファイル削除"""
        pass

    @abstractmethod
    def rmdir(self, path: str) -> None:
        """ディレクトリ削除"""
        pass

    @abstractmethod
    def path_join(self, *paths: str) -> str:
        """パス結合"""
        pass

    @abstractmethod
    def path_dirname(self, path: str) -> str:
        """ディレクトリ名取得"""
        pass

    @abstractmethod
    def path_basename(self, path: str) -> str:
        """ベース名取得"""
        pass

    @abstractmethod
    def isdir(self, path: str) -> bool:
        """ディレクトリ判定"""
        pass

    @abstractmethod
    def isfile(self, path: str) -> bool:
        """ファイル判定"""
        pass

    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """パス存在判定"""
        pass

    @abstractmethod
    def path_isdir(self, path: str) -> bool:
        """ディレクトリ判定（path.isdir用）"""
        pass

    @abstractmethod
    def path_isfile(self, path: str) -> bool:
        """ファイル判定（path.isfile用）"""
        pass

    @abstractmethod
    def getcwd(self) -> str:
        """現在のディレクトリ取得"""
        pass

    @abstractmethod
    def chdir(self, path: str) -> None:
        """ディレクトリ変更"""
        pass


class SystemOsProvider(OsProvider):
    """システムOS操作の実装 - 副作用はここに集約"""

    def exists(self, path: str) -> bool:
        """パス存在チェック（副作用なし）"""
        import os
        return os.path.exists(path)

    def listdir(self, path: str) -> List[str]:
        """ディレクトリ内容一覧（副作用なし）"""
        import os
        return os.listdir(path)

    def makedirs(self, path: str, exist_ok: bool = False) -> None:
        """ディレクトリ作成（副作用）"""
        import os
        os.makedirs(path, exist_ok=exist_ok)

    def remove(self, path: str) -> None:
        """ファイル削除（副作用）"""
        import os
        os.remove(path)

    def rmdir(self, path: str) -> None:
        """ディレクトリ削除（副作用）"""
        import os
        os.rmdir(path)

    def path_join(self, *paths: str) -> str:
        """パス結合（副作用なし）"""
        import os
        return os.path.join(*paths)

    def path_dirname(self, path: str) -> str:
        """ディレクトリ名取得（副作用なし）"""
        import os
        return os.path.dirname(path)

    def path_basename(self, path: str) -> str:
        """ベース名取得（副作用なし）"""
        import os
        return os.path.basename(path)

    def isdir(self, path: str) -> bool:
        """ディレクトリ判定（副作用なし）"""
        import os
        return os.path.isdir(path)

    def isfile(self, path: str) -> bool:
        """ファイル判定（副作用なし）"""
        import os
        return os.path.isfile(path)

    def path_exists(self, path: str) -> bool:
        """パス存在判定（副作用なし）"""
        import os
        return os.path.exists(path)

    def path_isdir(self, path: str) -> bool:
        """ディレクトリ判定（path.isdir用）（副作用なし）"""
        import os
        return os.path.isdir(path)

    def path_isfile(self, path: str) -> bool:
        """ファイル判定（path.isfile用）（副作用なし）"""
        import os
        return os.path.isfile(path)

    def getcwd(self) -> str:
        """現在のディレクトリ取得（副作用なし）"""
        import os
        return os.getcwd()

    def chdir(self, path: str) -> None:
        """ディレクトリ変更（副作用）"""
        import os
        os.chdir(path)


class MockOsProvider(OsProvider):
    """テスト用モックOSプロバイダー - 副作用なし"""

    def __init__(self):
        self._filesystem = {}  # path -> "file" or "dir"
        self._dir_contents = {}  # dir_path -> List[str]
        self._current_dir = "/mock_cwd"

    def exists(self, path: str) -> bool:
        """モック存在チェック（副作用なし）"""
        return path in self._filesystem

    def listdir(self, path: str) -> List[str]:
        """モックディレクトリ一覧（副作用なし）"""
        if path in self._dir_contents:
            return self._dir_contents[path]
        return []

    def makedirs(self, path: str, exist_ok: bool = False) -> None:
        """モックディレクトリ作成（副作用なし）"""
        if path in self._filesystem and not exist_ok:
            raise FileExistsError(f"Directory {path} already exists")
        self._filesystem[path] = "dir"
        if path not in self._dir_contents:
            self._dir_contents[path] = []

    def remove(self, path: str) -> None:
        """モックファイル削除（副作用なし）"""
        if path not in self._filesystem:
            raise FileNotFoundError(f"File {path} not found")
        del self._filesystem[path]

    def rmdir(self, path: str) -> None:
        """モックディレクトリ削除（副作用なし）"""
        if path not in self._filesystem:
            raise FileNotFoundError(f"Directory {path} not found")
        del self._filesystem[path]
        if path in self._dir_contents:
            del self._dir_contents[path]

    def path_join(self, *paths: str) -> str:
        """モックパス結合（副作用なし）"""
        return "/".join(paths)

    def path_dirname(self, path: str) -> str:
        """モックディレクトリ名取得（副作用なし）"""
        return "/".join(path.split("/")[:-1]) if "/" in path else ""

    def path_basename(self, path: str) -> str:
        """モックベース名取得（副作用なし）"""
        return path.split("/")[-1]

    def isdir(self, path: str) -> bool:
        """モックディレクトリ判定（副作用なし）"""
        if path in self._filesystem:
            return self._filesystem[path] == "dir"
        return False

    def isfile(self, path: str) -> bool:
        """モックファイル判定（副作用なし）"""
        if path in self._filesystem:
            return self._filesystem[path] == "file"
        return False

    def add_file(self, path: str) -> None:
        """テスト用ファイル追加"""
        self._filesystem[path] = "file"

    def add_directory(self, path: str, contents: Optional[List[str]] = None) -> None:
        """テスト用ディレクトリ追加"""
        self._filesystem[path] = "dir"
        self._dir_contents[path] = contents or []

    def path_exists(self, path: str) -> bool:
        """モックパス存在判定（副作用なし）"""
        return path in self._filesystem

    def path_isdir(self, path: str) -> bool:
        """モックディレクトリ判定（path.isdir用）（副作用なし）"""
        return self.isdir(path)

    def path_isfile(self, path: str) -> bool:
        """モックファイル判定（path.isfile用）（副作用なし）"""
        return self.isfile(path)

    def getcwd(self) -> str:
        """モック現在のディレクトリ取得（副作用なし）"""
        return self._current_dir

    def chdir(self, path: str) -> None:
        """モックディレクトリ変更（副作用なし）"""
        self._current_dir = path
