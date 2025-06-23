"""ファイル操作の抽象化と実装

Scripts配下で3番目に重要な副作用であるファイル操作を
依存性注入可能な形で抽象化
"""
# json, shutilは依存性注入により削除 - 実装クラスで受け取る
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union


class FileHandler(ABC):
    """ファイル操作インターフェース"""

    @abstractmethod
    def read_text(self, file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """ファイルをテキストとして読み込み

        Args:
            file_path: ファイルパス
            encoding: エンコーディング

        Returns:
            str: ファイルの内容
        """
        pass

    @abstractmethod
    def write_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを書き込み

        Args:
            file_path: ファイルパス
            content: 書き込む内容
            encoding: エンコーディング
        """
        pass

    @abstractmethod
    def append_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを追記

        Args:
            file_path: ファイルパス
            content: 追記する内容
            encoding: エンコーディング
        """
        pass

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """ファイル/ディレクトリの存在確認

        Args:
            path: パス

        Returns:
            bool: 存在するか
        """
        pass

    @abstractmethod
    def is_file(self, path: Union[str, Path]) -> bool:
        """ファイルかどうかの確認

        Args:
            path: パス

        Returns:
            bool: ファイルか
        """
        pass

    @abstractmethod
    def is_dir(self, path: Union[str, Path]) -> bool:
        """ディレクトリかどうかの確認

        Args:
            path: パス

        Returns:
            bool: ディレクトリか
        """
        pass

    @abstractmethod
    def mkdir(self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> None:
        """ディレクトリ作成

        Args:
            path: ディレクトリパス
            parents: 親ディレクトリも作成するか
            exist_ok: 既存でもエラーにしないか
        """
        pass

    @abstractmethod
    def remove_file(self, file_path: Union[str, Path]) -> None:
        """ファイル削除

        Args:
            file_path: ファイルパス
        """
        pass

    @abstractmethod
    def remove_dir(self, dir_path: Union[str, Path], recursive: bool = False) -> None:
        """ディレクトリ削除

        Args:
            dir_path: ディレクトリパス
            recursive: 再帰的に削除するか
        """
        pass

    @abstractmethod
    def glob(self, pattern: str, base_path: Union[str, Path] = ".") -> List[Path]:
        """パターンマッチングでファイル検索

        Args:
            pattern: glob パターン
            base_path: 検索ベースパス

        Returns:
            List[Path]: マッチしたファイルパスのリスト
        """
        pass

    @abstractmethod
    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリコピー

        Args:
            source: コピー元
            destination: コピー先
        """
        pass

    @abstractmethod
    def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリ移動

        Args:
            source: 移動元
            destination: 移動先
        """
        pass

    @abstractmethod
    def read_json(self, file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
        """JSONファイルを読み込み

        Args:
            file_path: JSONファイルパス
            encoding: エンコーディング

        Returns:
            Dict[str, Any]: JSONの内容
        """
        pass


class LocalFileHandler(FileHandler):
    """ローカルファイルシステムを使用した実装

    副作用操作はfile_operationsインターフェースを通じて注入される
    """

    def __init__(self, file_operations):
        """初期化

        Args:
            file_operations: ファイル操作インターフェース
        """
        self._file_operations = file_operations

    def read_text(self, file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """ファイルをテキストとして読み込み"""
        path = Path(file_path)
        with open(path, encoding=encoding) as f:
            return f.read()

    def write_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを書き込み"""
        path = Path(file_path)
        # 親ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

    def append_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを追記"""
        path = Path(file_path)
        # 親ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding=encoding) as f:
            f.write(content)

    def exists(self, path: Union[str, Path]) -> bool:
        """ファイル/ディレクトリの存在確認"""
        return Path(path).exists()

    def is_file(self, path: Union[str, Path]) -> bool:
        """ファイルかどうかの確認"""
        return Path(path).is_file()

    def is_dir(self, path: Union[str, Path]) -> bool:
        """ディレクトリかどうかの確認"""
        return Path(path).is_dir()

    def mkdir(self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> None:
        """ディレクトリ作成"""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def remove_file(self, file_path: Union[str, Path]) -> None:
        """ファイル削除"""
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()

    def remove_dir(self, dir_path: Union[str, Path], recursive: bool = False) -> None:
        """ディレクトリ削除"""
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            if recursive:
                self._file_operations.remove_tree(path)
            else:
                path.rmdir()

    def glob(self, pattern: str, base_path: Union[str, Path] = ".") -> List[Path]:
        """パターンマッチングでファイル検索"""
        base = Path(base_path)
        return list(base.glob(pattern))

    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリコピー"""
        src = Path(source)
        dst = Path(destination)

        if src.is_file():
            # ファイルコピー
            dst.parent.mkdir(parents=True, exist_ok=True)
            self._file_operations.copy_file(src, dst)
        elif src.is_dir():
            # ディレクトリコピー
            self._file_operations.copy_tree(src, dst, True)
        else:
            raise FileNotFoundError(f"Source not found: {src}")

    def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリ移動"""
        src = Path(source)
        dst = Path(destination)

        # 移動先の親ディレクトリを作成
        dst.parent.mkdir(parents=True, exist_ok=True)
        self._file_operations.move(src, dst)

    def read_json(self, file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        return self._file_operations.load_json(file_path)


class MockFileHandler(FileHandler):
    """テスト用のモック実装"""

    def __init__(self):
        self.files: Dict[str, str] = {}  # ファイルパス -> 内容
        self.directories: set = set()
        self.operations: List[Dict[str, Any]] = []  # 操作履歴

    def _normalize_path(self, path: Union[str, Path]) -> str:
        """パスを正規化"""
        return str(Path(path))

    def _record_operation(self, operation: str, **kwargs) -> None:
        """操作を記録"""
        self.operations.append({
            'operation': operation,
            'timestamp': None,  # 必要に応じて追加
            **kwargs
        })

    def read_text(self, file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """ファイルをテキストとして読み込み"""
        path = self._normalize_path(file_path)
        self._record_operation('read_text', file_path=path, encoding=encoding)

        # 実際のファイルが存在する場合は読み込み
        real_path = Path(file_path)
        if real_path.exists():
            with open(real_path, encoding=encoding) as f:
                return f.read()

        if path not in self.files:
            raise FileNotFoundError(f"No such file: {path}")
        return self.files[path]

    def write_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを書き込み"""
        path = self._normalize_path(file_path)
        self._record_operation('write_text', file_path=path, content=content, encoding=encoding)
        self.files[path] = content

    def append_text(self, file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """ファイルにテキストを追記"""
        path = self._normalize_path(file_path)
        self._record_operation('append_text', file_path=path, content=content, encoding=encoding)

        if path in self.files:
            self.files[path] += content
        else:
            self.files[path] = content

    def exists(self, path: Union[str, Path]) -> bool:
        """ファイル/ディレクトリの存在確認"""
        normalized = self._normalize_path(path)
        return normalized in self.files or normalized in self.directories

    def is_file(self, path: Union[str, Path]) -> bool:
        """ファイルかどうかの確認"""
        normalized = self._normalize_path(path)
        return normalized in self.files

    def is_dir(self, path: Union[str, Path]) -> bool:
        """ディレクトリかどうかの確認"""
        normalized = self._normalize_path(path)
        return normalized in self.directories

    def mkdir(self, path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> None:
        """ディレクトリ作成"""
        normalized = self._normalize_path(path)
        self._record_operation('mkdir', path=normalized, parents=parents, exist_ok=exist_ok)
        self.directories.add(normalized)

    def remove_file(self, file_path: Union[str, Path]) -> None:
        """ファイル削除"""
        path = self._normalize_path(file_path)
        self._record_operation('remove_file', file_path=path)

        if path in self.files:
            del self.files[path]

    def remove_dir(self, dir_path: Union[str, Path], recursive: bool = False) -> None:
        """ディレクトリ削除"""
        path = self._normalize_path(dir_path)
        self._record_operation('remove_dir', dir_path=path, recursive=recursive)

        if path in self.directories:
            self.directories.remove(path)

        if recursive:
            # 配下のファイルとディレクトリも削除
            to_remove_files = [f for f in self.files if f.startswith(path + "/")]
            to_remove_dirs = [d for d in self.directories if d.startswith(path + "/")]

            for f in to_remove_files:
                del self.files[f]
            for d in to_remove_dirs:
                self.directories.remove(d)

    def glob(self, pattern: str, base_path: Union[str, Path] = ".") -> List[Path]:
        """パターンマッチングでファイル検索"""
        self._record_operation('glob', pattern=pattern, base_path=str(base_path))
        # 簡易実装：実際のglobは複雑なのでモックでは最小限
        return []

    def copy(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリコピー"""
        src = self._normalize_path(source)
        dst = self._normalize_path(destination)
        self._record_operation('copy', source=src, destination=dst)

        if src in self.files:
            self.files[dst] = self.files[src]

    def move(self, source: Union[str, Path], destination: Union[str, Path]) -> None:
        """ファイル/ディレクトリ移動"""
        src = self._normalize_path(source)
        dst = self._normalize_path(destination)
        self._record_operation('move', source=src, destination=dst)

        if src in self.files:
            self.files[dst] = self.files[src]
            del self.files[src]

    def read_json(self, file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        path = self._normalize_path(file_path)
        self._record_operation('read_json', file_path=path, encoding=encoding)

        # 実際のファイルが存在する場合は読み込み
        real_path = Path(file_path)
        if real_path.exists():
            try:
                import json
                with open(real_path, encoding=encoding) as f:
                    return json.load(f)
            except (ImportError, json.JSONDecodeError):
                pass

        if path not in self.files:
            # デフォルト設定を返す
            return {}

        content = self.files[path]
        try:
            import json
            return json.loads(content)
        except ImportError:
            # モックではJSONの解析を簡略化
            return {}

    def get_operations(self) -> List[Dict[str, Any]]:
        """操作履歴を取得"""
        return self.operations.copy()

    def set_file_content(self, file_path: Union[str, Path], content: str) -> None:
        """テスト用：ファイル内容を設定"""
        path = self._normalize_path(file_path)
        self.files[path] = content

    def set_directory(self, dir_path: Union[str, Path]) -> None:
        """テスト用：ディレクトリを設定"""
        path = self._normalize_path(dir_path)
        self.directories.add(path)


def create_file_handler(mock: bool, file_operations) -> FileHandler:
    """FileHandlerのファクトリ関数

    Args:
        mock: モック実装を使用するか
        file_operations: ファイル操作インターフェース（実装時に注入）

    Returns:
        FileHandler: ファイルハンドラーインスタンス
    """
    if mock:
        return MockFileHandler()

    # file_operationsは必須パラメータです

    return LocalFileHandler(file_operations)
