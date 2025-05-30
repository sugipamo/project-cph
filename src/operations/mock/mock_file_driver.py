from pathlib import Path
from src.operations.file.file_driver import FileDriver
import os

class MockFileDriver(FileDriver):
    """
    振る舞い検証用のモックドライバー
    - 操作履歴の詳細記録
    - 期待される戻り値の返却
    - 内部状態のシミュレーション
    """
    def __init__(self, base_dir=Path(".")):
        super().__init__(base_dir)
        # 操作履歴（振る舞い検証用）
        self.operations = []
        self.call_count = {}
        
        # 内部状態のシミュレーション
        self.files = set()
        self.contents = dict()
        
        # 期待値設定
        self.expected_results = {}
        self.file_exists_map = {}

    def _record_operation(self, operation, *args):
        """操作を記録し、呼び出し回数をカウント"""
        self.operations.append((operation, *args))
        self.call_count[operation] = self.call_count.get(operation, 0) + 1

    def assert_operation_called(self, operation, times=None):
        """指定された操作が呼ばれたことを検証"""
        count = self.call_count.get(operation, 0)
        if times is None:
            assert count > 0, f"Operation '{operation}' was not called"
        else:
            assert count == times, f"Operation '{operation}' was called {count} times, expected {times}"

    def assert_operation_called_with(self, operation, *expected_args):
        """指定された操作が特定の引数で呼ばれたことを検証"""
        matching_calls = [op for op in self.operations if op[0] == operation and op[1:] == expected_args]
        assert len(matching_calls) > 0, f"Operation '{operation}' with args {expected_args} was not found in {self.operations}"

    def set_file_exists(self, path, exists=True):
        """ファイルの存在状態を設定"""
        abs_path = self.base_dir / Path(path)
        self.file_exists_map[abs_path] = exists
        if exists:
            self.files.add(abs_path)
        elif abs_path in self.files:
            self.files.remove(abs_path)

    def _move_impl(self, src_path, dst_path):
        # src_pathとdst_pathは既に解決済みの絶対パスである
        self.ensure_parent_dir(dst_path)
        self._record_operation("move", src_path, dst_path)
        if src_path in self.files:
            self.files.remove(src_path)
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents.pop(src_path, "")

    def _copy_impl(self, src_path, dst_path):
        # src_pathとdst_pathは既に解決済みの絶対パスである
        self.ensure_parent_dir(dst_path)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} が存在しません")
        self._record_operation("copy", src_path, dst_path)
        if src_path in self.files:
            self.files.add(dst_path)
            self.contents[dst_path] = self.contents[src_path] if src_path in self.contents else ""

    def _exists_impl(self, path):
        # すでに絶対パスならbase_dirを重ねない
        if isinstance(path, Path) and path.is_absolute():
            abs_path = path
        else:
            abs_path = self.base_dir / Path(path)
        self._record_operation("exists", abs_path)
        return abs_path in self.files

    def _create_impl(self, path, content):
        # pathが既に絶対パスならbase_dirを重ねない
        if isinstance(path, Path) and path.is_absolute():
            abs_path = path
        else:
            abs_path = self.base_dir / Path(path)
        self.ensure_parent_dir(abs_path)
        self._record_operation("create", abs_path, content)
        self.files.add(abs_path)
        self.contents[abs_path] = content

    def _copytree_impl(self, src_path, dst_path):
        src_path = self.base_dir / Path(src_path)
        dst_path = self.base_dir / Path(dst_path)
        self.ensure_parent_dir(dst_path)
        self.operations.append(("copytree", src_path, dst_path))
        # モックなので、ディレクトリ構造の再現は省略

    def _rmtree_impl(self, p):
        p = self.base_dir / Path(p)
        self.operations.append(("rmtree", p))
        # ディレクトリ配下も含めて全て削除（モックなので単純化）
        to_remove = [x for x in self.files if str(x).startswith(str(p))]
        for x in to_remove:
            self.files.remove(x)
            self.contents.pop(x, None)

    def _remove_impl(self, p):
        p = self.base_dir / Path(p)
        self.operations.append(("remove", p))
        if p in self.files:
            self.files.remove(p)
            self.contents.pop(p, None)

    def open(self, path, mode="r", encoding=None):
        abs_path = self.base_dir / Path(path)
        print(f"[DEBUG] MockFileDriver.open: path={abs_path} type={type(abs_path)}")
        print(f"[DEBUG] MockFileDriver.open: self.contents.keys()={list(self.contents.keys())}")
        if mode.startswith("w"):
            class Writer:
                def __init__(self, driver, path):
                    self.driver = driver
                    self.path = path
                    self._written = False
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def write(self, content):
                    self.driver.contents[self.path] = content
                    self.driver.files.add(self.path)
                    self._written = True
            return Writer(self, abs_path)
        elif mode.startswith("r"):
            class Reader:
                def __init__(self, content):
                    self._content = content
                    self._read = False
                def __enter__(self): return self
                def __exit__(self, exc_type, exc_val, exc_tb): pass
                def read(self):
                    if not self._read:
                        self._read = True
                        return self._content
                    return ""
            return Reader(self.contents.get(abs_path, ""))
        else:
            raise NotImplementedError(f"MockFileDriver: mode {mode} 未対応")

    def ensure_parent_dir(self, path):
        parent = Path(path).parent
        self.files.add(parent)

    def docker_cp(self, src: str, dst: str, container: str, to_container: bool = True, docker_driver=None):
        src_path = self.base_dir / Path(src)
        if src_path not in self.files:
            raise FileNotFoundError(f"MockFileDriver: {src_path} が存在しません (docker_cp)")
        self.operations.append(("docker_cp", src, dst, container, to_container))
        return f"mock_docker_cp_{src}_{dst}_{container}_{to_container}"

    def hash_file(self, path, algo='sha256'):
        import hashlib
        path = self.base_dir / Path(path)
        h = hashlib.new(algo)
        content = self.contents[path] if path in self.contents else ""
        content = content.encode()
        h.update(content)
        return h.hexdigest()

    def list_files(self, base_dir):
        base = self.base_dir / Path(base_dir)
        print(f"[DEBUG] list_files: base={base} str(base)={str(base)}")
        result = []
        for p in self.files:
            print(f"[DEBUG] list_files: p={p} str(p)={str(p)}")
            try:
                if p.is_relative_to(base):
                    print(f"[DEBUG] list_files: {p} is_relative_to {base} -> True")
                    result.append(p)
            except AttributeError:
                if str(p).startswith(str(base)):
                    print(f"[DEBUG] list_files: {str(p)} startswith {str(base)} -> True")
                    result.append(p)
        print(f"[DEBUG] list_files: result={result}")
        return result

    def add(self, path, content=""):
        """テスト用: ファイルの内容と存在を同時にセット"""
        abs_path = self.base_dir / Path(path)
        self.contents[abs_path] = content
        self.files.add(abs_path)

    def create(self, content=""):
        """後方互換性: driver.path が設定されている場合の古いAPIパターンをサポート"""
        if self.path is not None:
            # 古いAPIパターン: driver.path = path; driver.create(content)
            self._create_impl(self.path, content)
        else:
            # 新しいAPIパターンでは、引数でパスを指定する必要がある
            raise ValueError("Path must be provided either as argument or via self.path") 