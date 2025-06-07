"""
Comprehensive tests for utils.path_operations module
This is a critical untested module (533 LOC) that handles all path operations
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.path_operations import DockerPathOperations, PathInfo, PathOperationResult, PathOperations


class TestPathOperations:
    """PathOperationsクラスのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base = Path(self.temp_dir)

    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # resolve_path のテスト
    def test_resolve_path_simple_mode(self):
        """シンプルモードでのパス解決テスト"""
        result = PathOperations.resolve_path("/base", "file.txt")
        assert result == str(Path("/base/file.txt").resolve())

    def test_resolve_path_strict_mode_success(self):
        """詳細モード（成功）でのパス解決テスト"""
        result = PathOperations.resolve_path("/base", "file.txt", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == str(Path("/base/file.txt").resolve())
        assert len(result.errors) == 0
        assert result.metadata["resolution_method"] == "relative"

    def test_resolve_path_strict_mode_failure(self):
        """詳細モード（失敗）でのパス解決テスト"""
        result = PathOperations.resolve_path("/base", "", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert result.result is None
        assert "Path cannot be empty" in result.errors

    def test_resolve_path_absolute_path(self):
        """絶対パスでのテスト"""
        absolute_path = "/absolute/path/file.txt"
        result = PathOperations.resolve_path("/base", absolute_path)
        assert result == str(Path(absolute_path).resolve())

    def test_resolve_path_exception_simple_mode(self):
        """シンプルモードでの例外テスト"""
        with pytest.raises(ValueError, match="Path cannot be empty"):
            PathOperations.resolve_path("/base", "")

    # normalize_path のテスト
    def test_normalize_path_simple_mode(self):
        """パス正規化（シンプルモード）"""
        result = PathOperations.normalize_path("./test/../file.txt")
        assert Path(result).name == "file.txt"

    def test_normalize_path_strict_mode(self):
        """パス正規化（詳細モード）"""
        original = "./test/../file.txt"
        result = PathOperations.normalize_path(original, strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert Path(result.result).name == "file.txt"
        assert result.metadata["original"] == original

    # safe_path_join のテスト
    def test_safe_path_join_simple(self):
        """安全なパス結合（基本）"""
        result = PathOperations.safe_path_join("base", "sub", "file.txt")
        expected = str(Path("base") / "sub" / "file.txt")
        assert result == expected

    def test_safe_path_join_with_warnings(self):
        """安全なパス結合（警告付き）"""
        result = PathOperations.safe_path_join("base", "..", "file.txt", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert len(result.warnings) > 0
        assert "Potentially unsafe" in result.warnings[0]

    def test_safe_path_join_empty_paths(self):
        """空のパス結合エラー"""
        with pytest.raises(ValueError, match="At least one path must be provided"):
            PathOperations.safe_path_join()

    def test_safe_path_join_empty_paths_strict(self):
        """空のパス結合エラー（詳細モード）"""
        result = PathOperations.safe_path_join(strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert "At least one path must be provided" in result.errors

    # get_relative_path のテスト
    def test_get_relative_path_success(self):
        """相対パス取得（成功）"""
        base_path = self.test_base
        sub_path = base_path / "sub" / "file.txt"

        result = PathOperations.get_relative_path(str(sub_path), str(base_path))
        assert result == str(Path("sub") / "file.txt")

    def test_get_relative_path_strict_success(self):
        """相対パス取得（詳細モード・成功）"""
        base_path = self.test_base
        sub_path = base_path / "sub" / "file.txt"

        result = PathOperations.get_relative_path(str(sub_path), str(base_path), strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == str(Path("sub") / "file.txt")

    def test_get_relative_path_failure(self):
        """相対パス取得（失敗）"""
        with pytest.raises(ValueError):
            PathOperations.get_relative_path("/completely/different/path", str(self.test_base))

    def test_get_relative_path_strict_failure(self):
        """相対パス取得（詳細モード・失敗）"""
        result = PathOperations.get_relative_path(
            "/completely/different/path",
            str(self.test_base),
            strict=True
        )

        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert "Cannot compute relative path" in result.errors[0]

    # is_subdirectory のテスト
    def test_is_subdirectory_true(self):
        """サブディレクトリ判定（True）"""
        parent = self.test_base
        child = parent / "sub" / "file.txt"

        result = PathOperations.is_subdirectory(str(child), str(parent))
        assert result is True

    def test_is_subdirectory_false(self):
        """サブディレクトリ判定（False）"""
        result = PathOperations.is_subdirectory("/different/path", str(self.test_base))
        assert result is False

    def test_is_subdirectory_strict_true(self):
        """サブディレクトリ判定（詳細モード・True）"""
        parent = self.test_base
        child = parent / "sub" / "file.txt"

        is_sub, result = PathOperations.is_subdirectory(str(child), str(parent), strict=True)

        assert is_sub is True
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.metadata["is_subdirectory"] is True

    def test_is_subdirectory_strict_false(self):
        """サブディレクトリ判定（詳細モード・False）"""
        is_sub, result = PathOperations.is_subdirectory("/different/path", str(self.test_base), strict=True)

        assert is_sub is False
        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.metadata["is_subdirectory"] is False

    # ensure_parent_dir のテスト
    def test_ensure_parent_dir(self):
        """親ディレクトリ作成テスト"""
        target_file = self.test_base / "new" / "sub" / "file.txt"

        PathOperations.ensure_parent_dir(str(target_file))

        assert target_file.parent.exists()
        assert target_file.parent.is_dir()

    def test_ensure_parent_dir_existing(self):
        """既存の親ディレクトリテスト"""
        existing_dir = self.test_base / "existing"
        existing_dir.mkdir()
        target_file = existing_dir / "file.txt"

        # エラーが発生しないことを確認
        PathOperations.ensure_parent_dir(str(target_file))
        assert existing_dir.exists()

    # get_file_extension のテスト
    def test_get_file_extension_simple(self):
        """ファイル拡張子取得（シンプル）"""
        result = PathOperations.get_file_extension("file.txt")
        assert result == ".txt"

    def test_get_file_extension_no_extension(self):
        """拡張子なしファイル"""
        result = PathOperations.get_file_extension("file")
        assert result == ""

    def test_get_file_extension_strict(self):
        """ファイル拡張子取得（詳細モード）"""
        result = PathOperations.get_file_extension("file.txt", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == ".txt"
        assert result.metadata["stem"] == "file"

    # change_extension のテスト
    def test_change_extension_simple(self):
        """拡張子変更（シンプル）"""
        result = PathOperations.change_extension("file.txt", ".py")
        assert result == "file.py"

    def test_change_extension_no_dot(self):
        """拡張子変更（ドットなし）"""
        result = PathOperations.change_extension("file.txt", "py")
        assert result == "file.py"

    def test_change_extension_strict(self):
        """拡張子変更（詳細モード）"""
        result = PathOperations.change_extension("file.txt", ".py", strict=True)

        assert isinstance(result, PathOperationResult)
        assert result.success is True
        assert result.result == "file.py"
        assert result.metadata["original_extension"] == ".txt"
        assert result.metadata["new_extension"] == ".py"

    def test_change_extension_remove(self):
        """拡張子削除"""
        result = PathOperations.change_extension("file.txt", "")
        assert result == "file"


class TestDockerPathOperations:
    """DockerPathOperationsクラスのテスト"""

    def test_convert_path_exact_workspace(self):
        """ワークスペースパス完全一致"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "./workspace",
            "/host/workspace",
            "/docker/workspace"
        )
        assert result == "/docker/workspace"

    def test_convert_path_exact_workspace_path(self):
        """ワークスペースパス（絶対パス）完全一致"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/host/workspace",
            "/host/workspace",
            "/docker/workspace"
        )
        assert result == "/docker/workspace"

    def test_convert_path_subpath(self):
        """ワークスペースサブパス"""
        result = DockerPathOperations.convert_path_to_docker_mount(
            "/host/workspace/src/file.py",
            "/host/workspace",
            "/docker/workspace"
        )
        assert result == "/docker/workspace/src/file.py"

    def test_convert_path_no_match(self):
        """ワークスペース外のパス"""
        original_path = "/different/path/file.py"
        result = DockerPathOperations.convert_path_to_docker_mount(
            original_path,
            "/host/workspace",
            "/docker/workspace"
        )
        assert result == original_path

    def test_get_docker_mount_path_language_specific(self):
        """言語固有のマウントパス"""
        env_json = {
            "python": {
                "mount_path": "/python/workspace"
            }
        }

        result = DockerPathOperations.get_docker_mount_path_from_config(
            env_json,
            "python"
        )
        assert result == "/python/workspace"

    def test_get_docker_mount_path_global(self):
        """グローバルマウントパス"""
        env_json = {
            "mount_path": "/global/workspace"
        }

        result = DockerPathOperations.get_docker_mount_path_from_config(
            env_json,
            "unknown_language"
        )
        assert result == "/global/workspace"

    def test_get_docker_mount_path_default(self):
        """デフォルトマウントパス"""
        result = DockerPathOperations.get_docker_mount_path_from_config(
            {},
            "unknown_language"
        )
        assert result == "/workspace"

    def test_get_docker_mount_path_custom_default(self):
        """カスタムデフォルトマウントパス"""
        result = DockerPathOperations.get_docker_mount_path_from_config(
            {},
            "unknown_language",
            "/custom/default"
        )
        assert result == "/custom/default"

    def test_get_docker_mount_path_none_env(self):
        """None環境設定"""
        result = DockerPathOperations.get_docker_mount_path_from_config(
            None,
            "python"
        )
        assert result == "/workspace"


class TestPathInfo:
    """PathInfoクラスのテスト"""

    def test_path_info_creation(self):
        """PathInfo作成テスト"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            path_info = PathInfo.from_path(temp_path)

            assert path_info.path == temp_path
            assert path_info.is_absolute is True
            assert path_info.is_file is True
            assert path_info.is_directory is False
            assert path_info.suffix == ".txt"
            assert len(path_info.parts) > 0
        finally:
            os.unlink(temp_path)

    def test_path_info_directory(self):
        """ディレクトリのPathInfo"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path_info = PathInfo.from_path(temp_dir)

            assert path_info.is_directory is True
            assert path_info.is_file is False

    def test_path_info_nonexistent(self):
        """存在しないパスのPathInfo"""
        nonexistent = "/nonexistent/path/file.txt"
        path_info = PathInfo.from_path(nonexistent)

        assert path_info.is_directory is False
        assert path_info.is_file is False
        assert path_info.suffix == ".txt"
        assert path_info.stem == "file"


class TestPathOperationResult:
    """PathOperationResultクラスのテスト"""

    def test_result_creation_success(self):
        """成功結果の作成"""
        result = PathOperationResult(
            success=True,
            result="/path/to/file",
            errors=[],
            warnings=[],
            metadata={"test": "value"}
        )

        assert result.success is True
        assert result.result == "/path/to/file"
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.metadata["test"] == "value"

    def test_result_creation_failure(self):
        """失敗結果の作成"""
        result = PathOperationResult(
            success=False,
            result=None,
            errors=["Error message"],
            warnings=["Warning message"],
            metadata={}
        )

        assert result.success is False
        assert result.result is None
        assert "Error message" in result.errors
        assert "Warning message" in result.warnings

    def test_result_immutable(self):
        """結果の不変性テスト"""
        result = PathOperationResult(
            success=True,
            result="/path",
            errors=[],
            warnings=[],
            metadata={}
        )

        # frozen=Trueなので、属性変更はエラーになる
        with pytest.raises((AttributeError, TypeError)):  # AttributeError for frozen dataclass
            result.success = False


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_strings(self):
        """空文字列の処理"""
        # resolve_path
        with pytest.raises(ValueError):
            PathOperations.resolve_path("", "file.txt")

        with pytest.raises(ValueError):
            PathOperations.resolve_path("/base", "")

    def test_none_values(self):
        """None値の処理"""
        with pytest.raises(ValueError, match="Base directory cannot be None"):
            PathOperations.resolve_path(None, "file.txt")

    def test_unicode_paths(self):
        """Unicode文字を含むパス"""
        unicode_path = "テスト/ファイル.txt"
        result = PathOperations.normalize_path(unicode_path)
        assert isinstance(result, str)

    def test_very_long_paths(self):
        """非常に長いパス"""
        long_component = "a" * 100
        long_path = "/".join([long_component] * 10)

        result = PathOperations.normalize_path(long_path)
        assert isinstance(result, str)
        assert len(result) > 1000


if __name__ == "__main__":
    pytest.main([__file__])
