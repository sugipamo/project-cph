"""
パス操作互換性レイヤーのテスト

既存コードとの後方互換性を確保するためのテスト
deprecation warningが適切に発生することも確認
"""
import pytest
import warnings
import tempfile
import os
from pathlib import Path

from src.utils.path_operations_legacy import (
    PathUtil,
    resolve_path_pure,
    normalize_path_pure,
    get_relative_path_pure,
    is_subdirectory_pure,
    safe_path_join_pure,
    convert_path_to_docker_mount,
    get_docker_mount_path_from_config,
    get_workspace_path,
    get_contest_current_path,
    get_test_case_path
)
from src.utils.path_operations import PathOperationResult


class TestPathUtilCompatibility:
    """PathUtilクラスの互換性テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base = Path(self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_resolve_path_compatibility(self):
        """resolve_pathの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = PathUtil.resolve_path("/base", "file.txt")
            
            # 結果の正当性確認
            assert result == str(Path("/base/file.txt").resolve())
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "PathUtil.resolve_path()" in str(w[0].message)
            assert "PathOperations.resolve_path()" in str(w[0].message)
    
    def test_normalize_path_compatibility(self):
        """normalize_pathの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = PathUtil.normalize_path("./test/../file.txt")
            
            # 結果の正当性確認
            assert Path(result).name == "file.txt"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_ensure_parent_dir_compatibility(self):
        """ensure_parent_dirの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            target_file = self.test_base / "new" / "sub" / "file.txt"
            PathUtil.ensure_parent_dir(str(target_file))
            
            # 機能の正当性確認
            assert target_file.parent.exists()
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_get_relative_path_compatibility(self):
        """get_relative_pathの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            base_path = self.test_base
            sub_path = base_path / "sub" / "file.txt"
            
            result = PathUtil.get_relative_path(str(sub_path), str(base_path))
            
            # 結果の正当性確認
            assert result == str(Path("sub") / "file.txt")
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_is_subdirectory_compatibility(self):
        """is_subdirectoryの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            parent = self.test_base
            child = parent / "sub" / "file.txt"
            
            result = PathUtil.is_subdirectory(str(child), str(parent))
            
            # 結果の正当性確認
            assert result is True
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_safe_path_join_compatibility(self):
        """safe_path_joinの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = PathUtil.safe_path_join("base", "sub", "file.txt")
            
            # 結果の正当性確認
            expected = str(Path("base") / "sub" / "file.txt")
            assert result == expected
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_get_file_extension_compatibility(self):
        """get_file_extensionの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = PathUtil.get_file_extension("file.txt")
            
            # 結果の正当性確認
            assert result == ".txt"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_change_extension_compatibility(self):
        """change_extensionの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = PathUtil.change_extension("file.txt", ".py")
            
            # 結果の正当性確認
            assert result == "file.py"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestPureFunctionCompatibility:
    """純粋関数の互換性テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base = Path(self.temp_dir)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_resolve_path_pure_compatibility(self):
        """resolve_path_pureの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = resolve_path_pure("/base", "file.txt")
            
            # 結果の正当性確認
            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert result.result == str(Path("/base/file.txt").resolve())
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "resolve_path_pure()" in str(w[0].message)
    
    def test_normalize_path_pure_compatibility(self):
        """normalize_path_pureの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = normalize_path_pure("./test/../file.txt")
            
            # 結果の正当性確認
            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert Path(result.result).name == "file.txt"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_get_relative_path_pure_compatibility(self):
        """get_relative_path_pureの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            base_path = self.test_base
            sub_path = base_path / "sub" / "file.txt"
            
            result = get_relative_path_pure(str(sub_path), str(base_path))
            
            # 結果の正当性確認
            assert isinstance(result, PathOperationResult)
            assert result.success is True
            assert result.result == str(Path("sub") / "file.txt")
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_is_subdirectory_pure_compatibility(self):
        """is_subdirectory_pureの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            parent = self.test_base
            child = parent / "sub" / "file.txt"
            
            is_sub, result = is_subdirectory_pure(str(child), str(parent))
            
            # 結果の正当性確認
            assert is_sub is True
            assert isinstance(result, PathOperationResult)
            assert result.success is True
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_safe_path_join_pure_compatibility(self):
        """safe_path_join_pureの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = safe_path_join_pure("base", "sub", "file.txt")
            
            # 結果の正当性確認
            assert isinstance(result, PathOperationResult)
            assert result.success is True
            expected = str(Path("base") / "sub" / "file.txt")
            assert result.result == expected
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestDockerFunctionCompatibility:
    """Docker関数の互換性テスト"""
    
    def test_convert_path_to_docker_mount_compatibility(self):
        """convert_path_to_docker_mountの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = convert_path_to_docker_mount(
                "./workspace",
                "/host/workspace",
                "/docker/workspace"
            )
            
            # 結果の正当性確認
            assert result == "/docker/workspace"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "convert_path_to_docker_mount()" in str(w[0].message)
    
    def test_get_docker_mount_path_from_config_compatibility(self):
        """get_docker_mount_path_from_configの互換性テスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            env_json = {"mount_path": "/custom/workspace"}
            result = get_docker_mount_path_from_config(env_json, "python")
            
            # 結果の正当性確認
            assert result == "/custom/workspace"
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestConfigBasedFunctions:
    """設定ベース関数のテスト"""
    
    def test_get_workspace_path(self):
        """get_workspace_pathのテスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = get_workspace_path()
            
            # 結果の正当性確認（何らかのパスが返される）
            assert isinstance(result, str)
            assert len(result) > 0
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_get_contest_current_path(self):
        """get_contest_current_pathのテスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = get_contest_current_path()
            
            # 結果の正当性確認
            assert isinstance(result, str)
            # フォールバック値または設定値が返される
            assert len(result) > 0
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
    
    def test_get_test_case_path(self):
        """get_test_case_pathのテスト"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = get_test_case_path()
            
            # 結果の正当性確認
            assert isinstance(result, str)
            assert len(result) > 0
            
            # 非推奨警告の確認
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)


class TestWarningBehavior:
    """警告動作の詳細テスト"""
    
    def test_warning_stacklevel(self):
        """警告のスタックレベルテスト"""
        def call_legacy_function():
            return PathUtil.resolve_path("/base", "file.txt")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            call_legacy_function()
            
            # 警告が発生することを確認
            assert len(w) == 1
            
            # スタックレベルが適切に設定されていることを確認
            # （警告の場所が呼び出し元を指している）
            warning = w[0]
            assert warning.filename.endswith("test_path_operations_legacy.py")
    
    def test_multiple_warnings(self):
        """複数の非推奨関数呼び出しでの警告"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            PathUtil.resolve_path("/base", "file1.txt")
            PathUtil.normalize_path("./file2.txt")
            PathUtil.safe_path_join("base", "file3.txt")
            
            # 3つの警告が発生することを確認
            assert len(w) == 3
            
            # 全て非推奨警告であることを確認
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
    
    def test_warning_filtering(self):
        """警告フィルタリングのテスト"""
        # 非推奨警告を無視する設定
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            
            # 警告が発生しないことを確認（機能は正常動作）
            result = PathUtil.resolve_path("/base", "file.txt")
            assert result == str(Path("/base/file.txt").resolve())


class TestErrorHandling:
    """エラーハンドリングの互換性テスト"""
    
    def test_legacy_error_behavior(self):
        """従来のエラー動作の互換性"""
        # 従来版と同じように例外が発生することを確認
        with pytest.raises(ValueError):
            PathUtil.resolve_path("/base", "")
        
        with pytest.raises(ValueError):
            PathUtil.get_relative_path("/different/path", "/base")
    
    def test_pure_function_error_behavior(self):
        """純粋関数版のエラー動作の互換性"""
        # 純粋関数版では結果型でエラーが返されることを確認
        result = resolve_path_pure("/base", "")
        
        assert isinstance(result, PathOperationResult)
        assert result.success is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__])