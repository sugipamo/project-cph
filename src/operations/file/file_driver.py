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
    """
    ファイル操作の抽象基底クラス
    
    テンプレートメソッドパターンを使用:
    - 共通の処理（パス解決、親ディレクトリ作成等）は基底クラスで実装
    - 実際のファイル操作は具象クラスで実装（_*_implメソッド）
    """
    
    def __init__(self, base_dir=Path(".")):
        self.base_dir = Path(base_dir)
        # path と dst_path は操作時に動的に設定される
        self.path = None
        self.dst_path = None

    def resolve_path(self, path=None):
        """パスを解決する（絶対パスに変換）"""
        target_path = path if path is not None else self.path
        if target_path is None:
            raise ValueError("Path is not set")
        return self.base_dir / Path(target_path)

    def makedirs(self, path=None, exist_ok=True):
        """ディレクトリを作成する"""
        target_path = self.resolve_path(path)
        target_path.mkdir(parents=True, exist_ok=exist_ok)

    def isdir(self, path=None):
        """ディレクトリかどうかを判定する"""
        target_path = self.resolve_path(path)
        return target_path.is_dir()

    def glob(self, pattern):
        """パターンにマッチするファイルを検索する"""
        return list(self.base_dir.glob(pattern))

    def move(self, src_path=None, dst_path=None):
        """ファイルを移動する（テンプレートメソッド）"""
        # 後方互換性: 引数なしの場合は self.path と self.dst_path を使用
        if src_path is None:
            src_path = self.path
        if dst_path is None:
            dst_path = self.dst_path
            
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        self._move_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _move_impl(self, src_path, dst_path):
        """ファイル移動の実装（具象クラスで実装）"""
        pass

    def copy(self, src_path=None, dst_path=None):
        """ファイルをコピーする（テンプレートメソッド）"""
        # 後方互換性: 引数なしの場合は self.path と self.dst_path を使用
        if src_path is None:
            src_path = self.path
        if dst_path is None:
            dst_path = self.dst_path
            
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        self.ensure_parent_dir(resolved_dst)
        self._copy_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _copy_impl(self, src_path, dst_path):
        """ファイルコピーの実装（具象クラスで実装）"""
        pass

    def exists(self, path=None):
        """ファイルの存在確認（テンプレートメソッド）"""
        # 後方互換性: 引数なしの場合は self.path を使用
        if path is None:
            path = self.path
        resolved_path = self.resolve_path(path)
        return self._exists_impl(resolved_path)

    @abstractmethod
    def _exists_impl(self, path):
        """ファイル存在確認の実装（具象クラスで実装）"""
        pass

    def create(self, path, content: str = ""):
        """ファイルを作成する（テンプレートメソッド）"""
        resolved_path = self.resolve_path(path)
        self.ensure_parent_dir(resolved_path)
        self._create_impl(resolved_path, content)

    @abstractmethod
    def _create_impl(self, path, content):
        """ファイル作成の実装（具象クラスで実装）"""
        pass

    def copytree(self, src_path, dst_path):
        """ディレクトリツリーをコピーする（テンプレートメソッド）"""
        resolved_src = self.resolve_path(src_path)
        resolved_dst = self.resolve_path(dst_path)
        if resolved_src == resolved_dst:
            return
        self.ensure_parent_dir(resolved_dst)
        self._copytree_impl(resolved_src, resolved_dst)

    @abstractmethod
    def _copytree_impl(self, src_path, dst_path):
        """ディレクトリツリーコピーの実装（具象クラスで実装）"""
        pass

    def rmtree(self, path):
        """ディレクトリツリーを削除する（テンプレートメソッド）"""
        resolved_path = self.resolve_path(path)
        self._rmtree_impl(resolved_path)

    @abstractmethod
    def _rmtree_impl(self, path):
        """ディレクトリツリー削除の実装（具象クラスで実装）"""
        pass

    def remove(self, path):
        """ファイルを削除する（テンプレートメソッド）"""
        resolved_path = self.resolve_path(path)
        self._remove_impl(resolved_path)

    @abstractmethod
    def _remove_impl(self, path):
        """ファイル削除の実装（具象クラスで実装）"""
        pass

    @abstractmethod
    def open(self, path, mode="r", encoding=None):
        """ファイルを開く（具象クラスで実装）"""
        pass

    def ensure_parent_dir(self, path):
        """親ディレクトリを作成する"""
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def hash_file(self, path, algo='sha256'):
        """ファイルのハッシュ値を計算する"""
        import hashlib
        h = hashlib.new(algo)
        resolved_path = self.resolve_path(path)
        with open(resolved_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @abstractmethod
    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        """Dockerコンテナとのファイルコピー（具象クラスで実装）"""
        pass

    def mkdir(self, path):
        """ディレクトリを作成する"""
        resolved_path = self.resolve_path(path)
        resolved_path.mkdir(parents=True, exist_ok=True)

    def touch(self, path):
        """ファイルをタッチする（作成または更新時刻を変更）"""
        resolved_path = self.resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.touch(exist_ok=True)

    @abstractmethod
    def list_files(self, base_dir):
        """
        指定ディレクトリ以下の全ファイルパスをリストで返す（具象クラスで実装）
        """
        pass 