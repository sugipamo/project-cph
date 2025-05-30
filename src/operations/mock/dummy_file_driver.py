from pathlib import Path
from src.operations.file.file_driver import FileDriver

class DummyFileDriver(FileDriver):
    """
    最小実装のスタブドライバー
    - エラーを起こさない
    - None/空値を返す
    - 内部状態や操作記録は持たない
    """
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)

    def _move_impl(self, src_path, dst_path):
        # 何もしない
        pass

    def _copy_impl(self, src_path, dst_path):
        # 何もしない
        pass

    def _exists_impl(self, path):
        # 常にFalseを返す
        return False

    def _create_impl(self, path, content):
        # 何もしない
        pass

    def _copytree_impl(self, src_path, dst_path):
        # 何もしない
        pass

    def _rmtree_impl(self, p):
        # 何もしない
        pass

    def _remove_impl(self, p):
        # 何もしない
        pass

    def open(self, path, mode="r", encoding=None):
        """空のダミーファイルオブジェクトを返す"""
        class DummyFile:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def read(self): return ""
            def write(self, content): pass
            def close(self): pass
        return DummyFile()

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        # 何もしない
        pass

    def list_files(self, base_dir):
        # 空のリストを返す
        return [] 