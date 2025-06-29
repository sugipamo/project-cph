"""ファイル操作プロバイダー - 副作用を集約"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List


class FileProvider(ABC):
    """ファイル操作の抽象インターフェース"""

    @abstractmethod
    def read_text_file(self, file_path: str, encoding: str) -> str:
        """テキストファイルを読み込み"""
        pass

    @abstractmethod
    def write_text_file(self, file_path: str, content: str, encoding: str) -> None:
        """テキストファイルに書き込み"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """ファイル存在チェック"""
        pass

    @abstractmethod
    def list_directory(self, dir_path: str) -> List[str]:
        """ディレクトリ内容を一覧"""
        pass

    @abstractmethod
    def create_directory(self, dir_path: str, parents: bool, exist_ok: bool) -> None:
        """ディレクトリを作成"""
        pass

    @abstractmethod
    def path_exists(self, path: str) -> bool:
        """パス（ファイルまたはディレクトリ）の存在チェック"""
        pass

    @abstractmethod
    def is_directory(self, path: str) -> bool:
        """パスがディレクトリかチェック"""
        pass

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """パスがファイルかチェック"""
        pass


class SystemFileProvider(FileProvider):
    """システムファイル操作の実装 - 副作用はここに集約"""

    def read_text_file(self, file_path: str, encoding: str) -> str:
        """テキストファイルを読み込み（副作用）"""
        with open(file_path, encoding=encoding) as f:
            return f.read()

    def write_text_file(self, file_path: str, content: str, encoding: str) -> None:
        """テキストファイルに書き込み（副作用）"""
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)

    def file_exists(self, file_path: str) -> bool:
        """ファイル存在チェック（副作用なし）"""
        return Path(file_path).exists()

    def list_directory(self, dir_path: str) -> List[str]:
        """ディレクトリ内容を一覧（副作用なし）"""
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            return []
        try:
            return [item.name for item in path.iterdir()]
        except (OSError, PermissionError) as e:
            # 互換性維持のためのコメント: 権限エラーやOSエラーを明示的に処理
            raise RuntimeError(f"Failed to list directory '{dir_path}': {e}") from e

    def create_directory(self, dir_path: str, parents: bool, exist_ok: bool) -> None:
        """ディレクトリを作成（副作用）"""
        Path(dir_path).mkdir(parents=parents, exist_ok=exist_ok)

    def path_exists(self, path: str) -> bool:
        """パスの存在チェック（副作用）"""
        return Path(path).exists()

    def is_directory(self, path: str) -> bool:
        """ディレクトリチェック（副作用）"""
        return Path(path).is_dir()

    def is_file(self, path: str) -> bool:
        """ファイルチェック（副作用）"""
        return Path(path).is_file()


class MockFileProvider(FileProvider):
    """テスト用モックファイルプロバイダー - 副作用なし"""

    def __init__(self):
        self._files: Dict[str, str] = {}

    def read_text_file(self, file_path: str, encoding: str) -> str:
        """モック読み込み（副作用なし）"""
        if file_path not in self._files:
            raise FileNotFoundError(f"File not found: {file_path}")
        return self._files[file_path]

    def write_text_file(self, file_path: str, content: str, encoding: str) -> None:
        """モック書き込み（副作用なし）"""
        self._files[file_path] = content

    def file_exists(self, file_path: str) -> bool:
        """モック存在チェック（副作用なし）"""
        return file_path in self._files

    def list_directory(self, dir_path: str) -> List[str]:
        """モックディレクトリ一覧（副作用なし）"""
        dir_path = dir_path.rstrip('/') + '/'
        return [
            Path(path).name
            for path in self._files
            if path.startswith(dir_path) and '/' not in path[len(dir_path):]
        ]

    def create_directory(self, dir_path: str, parents: bool, exist_ok: bool) -> None:
        """モックディレクトリ作成（副作用なし）"""
        if not exist_ok and self.is_directory(dir_path):
            raise FileExistsError(f"Directory already exists: {dir_path}")
        # モックでは実際にディレクトリを作成せず、記録のみ
        self._directories = getattr(self, '_directories', set())
        self._directories.add(dir_path)
        if parents:
            # 親ディレクトリも追加
            path = Path(dir_path)
            for parent in path.parents:
                if str(parent) != '.':
                    self._directories.add(str(parent))

    def path_exists(self, path: str) -> bool:
        """モックパス存在チェック（副作用なし）"""
        return path in self._files or path in getattr(self, '_directories', set())

    def is_directory(self, path: str) -> bool:
        """モックディレクトリチェック（副作用なし）"""
        return path in getattr(self, '_directories', set())

    def is_file(self, path: str) -> bool:
        """モックファイルチェック（副作用なし）"""
        return path in self._files

    def add_file(self, file_path: str, content: str) -> None:
        """テスト用ファイル追加"""
        self._files[file_path] = content
