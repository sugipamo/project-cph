"""
Tests for src/operations/utils/path_utils.py PathUtil class to improve coverage
"""
import pytest
from pathlib import Path
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# Import only PathUtil to avoid circular import issues
import sys
sys.path.insert(0, '/home/cphelper/project-cph/src')

# Import directly without going through context imports
import importlib.util
spec = importlib.util.spec_from_file_location("path_utils", "/home/cphelper/project-cph/src/operations/utils/path_utils.py")
path_utils_module = importlib.util.module_from_spec(spec)

# Mock the problematic imports
sys.modules['src.context.resolver.config_resolver'] = Mock()
sys.modules['src.context.resolver.config_node'] = Mock()

spec.loader.exec_module(path_utils_module)

PathUtil = path_utils_module.PathUtil


class TestPathUtil:
    """Tests for PathUtil class methods"""
    
    def test_resolve_path_absolute(self):
        """Test resolve_path with absolute path"""
        base_dir = "/home/user"
        absolute_path = "/tmp/test.txt"
        
        result = PathUtil.resolve_path(base_dir, absolute_path)
        
        assert result == Path(absolute_path)
        assert result.is_absolute()
    
    def test_resolve_path_relative(self):
        """Test resolve_path with relative path"""
        base_dir = "/home/user"
        relative_path = "documents/file.txt"
        
        result = PathUtil.resolve_path(base_dir, relative_path)
        
        expected = Path("/home/user/documents/file.txt")
        assert result == expected
    
    def test_resolve_path_current_directory(self):
        """Test resolve_path with current directory references"""
        base_dir = "/home/user"
        current_path = "./file.txt"
        
        result = PathUtil.resolve_path(base_dir, current_path)
        
        expected = Path("/home/user/./file.txt")
        assert result == expected
    
    def test_resolve_path_parent_directory(self):
        """Test resolve_path with parent directory references"""
        base_dir = "/home/user/documents"
        parent_path = "../config.txt"
        
        result = PathUtil.resolve_path(base_dir, parent_path)
        
        expected = Path("/home/user/documents/../config.txt")
        assert result == expected

    def test_ensure_parent_dir_creates_directories(self):
        """Test ensure_parent_dir creates parent directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "subdir" / "nested" / "file.txt"
            
            # Parent directories should not exist initially
            assert not test_file.parent.exists()
            
            PathUtil.ensure_parent_dir(test_file)
            
            # Parent directories should now exist
            assert test_file.parent.exists()
            assert test_file.parent.is_dir()
    
    def test_ensure_parent_dir_existing_directories(self):
        """Test ensure_parent_dir with existing directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "file.txt"
            
            # Parent directory already exists
            assert test_file.parent.exists()
            
            # Should not raise error
            PathUtil.ensure_parent_dir(test_file)
            
            assert test_file.parent.exists()
    
    def test_normalize_path_resolves_path(self):
        """Test normalize_path resolves the path"""
        test_path = "some/relative/path/../file.txt"
        
        result = PathUtil.normalize_path(test_path)
        
        # Should resolve and be absolute
        assert result.is_absolute()
        assert str(result).endswith("some/relative/file.txt")
    
    def test_normalize_path_absolute_path(self):
        """Test normalize_path with absolute path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test.txt"
            
            result = PathUtil.normalize_path(test_path)
            
            assert result.is_absolute()
            assert result == test_path.resolve()
    
    def test_get_relative_path_success(self):
        """Test get_relative_path when relative path can be calculated"""
        base_dir = "/home/user"
        target_path = "/home/user/documents/file.txt"
        
        result = PathUtil.get_relative_path(base_dir, target_path)
        
        expected = Path("documents/file.txt")
        assert result == expected
    
    def test_get_relative_path_not_relative(self):
        """Test get_relative_path when paths are not relative"""
        base_dir = "/home/user"
        target_path = "/tmp/file.txt"
        
        result = PathUtil.get_relative_path(base_dir, target_path)
        
        # Should return absolute path when relative_to fails
        assert result.is_absolute()
        assert result == Path(target_path).resolve()
    
    def test_get_relative_path_same_directory(self):
        """Test get_relative_path with same directory"""
        base_dir = "/home/user"
        target_path = "/home/user"
        
        result = PathUtil.get_relative_path(base_dir, target_path)
        
        assert result == Path(".")
    
    def test_is_subdirectory_true(self):
        """Test is_subdirectory returns True for subdirectory"""
        parent_dir = "/home/user"
        child_path = "/home/user/documents/file.txt"
        
        result = PathUtil.is_subdirectory(parent_dir, child_path)
        
        assert result is True
    
    def test_is_subdirectory_false(self):
        """Test is_subdirectory returns False for non-subdirectory"""
        parent_dir = "/home/user"
        child_path = "/tmp/file.txt"
        
        result = PathUtil.is_subdirectory(parent_dir, child_path)
        
        assert result is False
    
    def test_is_subdirectory_same_path(self):
        """Test is_subdirectory with same path"""
        same_path = "/home/user"
        
        result = PathUtil.is_subdirectory(same_path, same_path)
        
        # Same path should be considered a subdirectory (or equal)
        assert result is True
    
    def test_safe_path_join_valid_paths(self):
        """Test safe_path_join with valid relative paths"""
        result = PathUtil.safe_path_join("base", "sub", "file.txt")
        
        expected = Path("base/sub/file.txt")
        assert result == expected
    
    def test_safe_path_join_single_path(self):
        """Test safe_path_join with single path"""
        result = PathUtil.safe_path_join("single_path")
        
        expected = Path("single_path")
        assert result == expected
    
    def test_safe_path_join_absolute_path_raises_error(self):
        """Test safe_path_join raises error for absolute path"""
        with pytest.raises(ValueError, match="Unsafe path component"):
            PathUtil.safe_path_join("base", "/absolute/path")
    
    def test_safe_path_join_parent_reference_raises_error(self):
        """Test safe_path_join raises error for parent directory reference"""
        with pytest.raises(ValueError, match="Unsafe path component"):
            PathUtil.safe_path_join("base", "../parent")
        
        with pytest.raises(ValueError, match="Unsafe path component"):
            PathUtil.safe_path_join("base", "sub/../../../escape")
    
    def test_safe_path_join_dot_in_filename_allowed(self):
        """Test safe_path_join allows dots in filenames"""
        result = PathUtil.safe_path_join("base", "file.name.txt")
        
        expected = Path("base/file.name.txt")
        assert result == expected
    
    def test_get_file_extension_with_extension(self):
        """Test get_file_extension with file that has extension"""
        test_path = "document.pdf"
        
        result = PathUtil.get_file_extension(test_path)
        
        assert result == ".pdf"
    
    def test_get_file_extension_multiple_dots(self):
        """Test get_file_extension with multiple dots"""
        test_path = "archive.tar.gz"
        
        result = PathUtil.get_file_extension(test_path)
        
        assert result == ".gz"  # Only the last extension
    
    def test_get_file_extension_no_extension(self):
        """Test get_file_extension with file that has no extension"""
        test_path = "README"
        
        result = PathUtil.get_file_extension(test_path)
        
        assert result == ""
    
    def test_get_file_extension_hidden_file(self):
        """Test get_file_extension with hidden file"""
        test_path = ".hidden"
        
        result = PathUtil.get_file_extension(test_path)
        
        assert result == ""
    
    def test_change_extension_with_dot(self):
        """Test change_extension with extension that includes dot"""
        test_path = "document.txt"
        new_extension = ".pdf"
        
        result = PathUtil.change_extension(test_path, new_extension)
        
        expected = Path("document.pdf")
        assert result == expected
    
    def test_change_extension_without_dot(self):
        """Test change_extension with extension without dot"""
        test_path = "document.txt"
        new_extension = "pdf"
        
        result = PathUtil.change_extension(test_path, new_extension)
        
        expected = Path("document.pdf")
        assert result == expected
    
    def test_change_extension_no_original_extension(self):
        """Test change_extension with file that has no extension"""
        test_path = "README"
        new_extension = ".md"
        
        result = PathUtil.change_extension(test_path, new_extension)
        
        expected = Path("README.md")
        assert result == expected
    
    def test_change_extension_complex_path(self):
        """Test change_extension with complex path"""
        test_path = "/home/user/documents/report.docx"
        new_extension = "pdf"
        
        result = PathUtil.change_extension(test_path, new_extension)
        
        expected = Path("/home/user/documents/report.pdf")
        assert result == expected
    
    def test_pathutil_with_pathlib_objects(self):
        """Test PathUtil methods work with pathlib.Path objects"""
        base_dir = Path("/home/user")
        target_path = Path("documents/file.txt")
        
        result = PathUtil.resolve_path(base_dir, target_path)
        
        assert isinstance(result, Path)
        assert str(result) == "/home/user/documents/file.txt"
    
    def test_pathutil_with_string_paths(self):
        """Test PathUtil methods work with string paths"""
        base_dir = "/home/user"
        target_path = "documents/file.txt"
        
        result = PathUtil.resolve_path(base_dir, target_path)
        
        assert isinstance(result, Path)
        assert str(result) == "/home/user/documents/file.txt"
    
    def test_safe_path_join_with_mixed_types(self):
        """Test safe_path_join with mixed Path and string types"""
        result = PathUtil.safe_path_join(Path("base"), "sub", Path("file.txt"))
        
        expected = Path("base/sub/file.txt")
        assert result == expected
    
    def test_path_functions_with_empty_strings(self):
        """Test path functions handle empty strings appropriately"""
        result = PathUtil.get_file_extension("")
        assert result == ""
        
        # Empty string creates invalid path for with_suffix
        with pytest.raises(ValueError):
            PathUtil.change_extension("", ".txt")


class TestConfigurationBasedFunctionsDirect:
    """Test configuration-based functions through direct module access"""
    
    def test_get_test_case_path(self):
        """Test get_test_case_path returns correct path"""
        contest_current_path = Path("/contest/current")
        
        result = path_utils_module.get_test_case_path(contest_current_path)
        
        expected = Path("/contest/current/test")
        assert result == expected
    
    def test_get_test_case_in_path(self):
        """Test get_test_case_in_path returns correct path"""
        contest_current_path = Path("/contest/current")
        
        result = path_utils_module.get_test_case_in_path(contest_current_path)
        
        expected = Path("/contest/current/test/in")
        assert result == expected
    
    def test_get_test_case_out_path(self):
        """Test get_test_case_out_path returns correct path"""
        contest_current_path = Path("/contest/current")
        
        result = path_utils_module.get_test_case_out_path(contest_current_path)
        
        expected = Path("/contest/current/test/out")
        assert result == expected
    
    def test_test_case_paths_with_relative_path(self):
        """Test test case path functions with relative paths"""
        contest_current_path = Path("contest/current")
        
        test_path = path_utils_module.get_test_case_path(contest_current_path)
        in_path = path_utils_module.get_test_case_in_path(contest_current_path)
        out_path = path_utils_module.get_test_case_out_path(contest_current_path)
        
        assert test_path == Path("contest/current/test")
        assert in_path == Path("contest/current/test/in")
        assert out_path == Path("contest/current/test/out")
    
    def test_test_case_paths_chaining(self):
        """Test that test case path functions work correctly when chained"""
        contest_current_path = Path("/base")
        
        # Verify that in_path and out_path use get_test_case_path
        base_test_path = path_utils_module.get_test_case_path(contest_current_path)
        in_path = path_utils_module.get_test_case_in_path(contest_current_path)
        out_path = path_utils_module.get_test_case_out_path(contest_current_path)
        
        assert in_path == base_test_path / "in"
        assert out_path == base_test_path / "out"
    
    def test_get_contest_env_path_found_in_current_dir(self):
        """Test get_contest_env_path when contest_env is in current directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create contest_env directory
            contest_env_path = os.path.join(temp_dir, "contest_env")
            os.makedirs(contest_env_path)
            
            with patch('os.getcwd', return_value=temp_dir):
                result = path_utils_module.get_contest_env_path()
            
            assert result == Path(contest_env_path)
    
    def test_get_contest_env_path_found_in_parent_dir(self):
        """Test get_contest_env_path when contest_env is in parent directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create contest_env in temp_dir
            contest_env_path = os.path.join(temp_dir, "contest_env")
            os.makedirs(contest_env_path)
            
            # Create subdirectory
            sub_dir = os.path.join(temp_dir, "subdir", "nested")
            os.makedirs(sub_dir)
            
            with patch('os.getcwd', return_value=sub_dir):
                result = path_utils_module.get_contest_env_path()
            
            assert result == Path(contest_env_path)
    
    def test_get_contest_env_path_not_found(self):
        """Test get_contest_env_path when contest_env is not found"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('os.getcwd', return_value=temp_dir):
                with pytest.raises(ValueError, match="contest_env_pathが自動検出できませんでした"):
                    path_utils_module.get_contest_env_path()
    
    def test_get_contest_env_path_reaches_root(self):
        """Test get_contest_env_path when search reaches filesystem root"""
        # Mock os functions to simulate reaching root without finding contest_env
        with patch('os.getcwd', return_value='/some/deep/path'):
            with patch('os.path.isdir', return_value=False):
                with patch('os.path.dirname', side_effect=lambda x: '/' if x != '/' else '/'):
                    with pytest.raises(ValueError, match="contest_env_pathが自動検出できませんでした"):
                        path_utils_module.get_contest_env_path()


class TestConfigurationFunctionsMocked:
    """Test configuration functions with mocked dependencies"""
    
    def test_configuration_functions_with_mocked_resolver(self):
        """Test configuration functions with mocked resolve_best"""
        
        def mock_resolve_best(resolver, path):
            mock_node = Mock()
            if path[-1] == "workspace_path":
                mock_node.value = "/workspace"
                mock_node.key = "workspace_path"
            elif path[-1] == "contest_current_path":
                mock_node.value = "/contest/current"
                mock_node.key = "contest_current_path"
            elif path[-1] == "contest_template_path":
                mock_node.value = "/contest/template"
                mock_node.key = "contest_template_path"
            elif path[-1] == "contest_temp_path":
                mock_node.value = "/contest/temp"
                mock_node.key = "contest_temp_path"
            elif path[-1] == "source_file_name":
                mock_node.value = "main.py"
                mock_node.key = "source_file_name"
            else:
                return None
            return mock_node
        
        # Patch the resolve_best function in the module
        with patch.object(path_utils_module, 'resolve_best', side_effect=mock_resolve_best):
            # Test workspace path
            result = path_utils_module.get_workspace_path(Mock(), "python")
            assert result == Path("/workspace")
            
            # Test contest current path
            result = path_utils_module.get_contest_current_path(Mock(), "python")
            assert result == Path("/contest/current")
            
            # Test contest template path
            result = path_utils_module.get_contest_template_path(Mock(), "python")
            assert result == Path("/contest/template")
            
            # Test contest temp path
            result = path_utils_module.get_contest_temp_path(Mock(), "python")
            assert result == Path("/contest/temp")
            
            # Test source file name
            result = path_utils_module.get_source_file_name(Mock(), "python")
            assert result == "main.py"
    
    def test_configuration_functions_error_cases(self):
        """Test configuration functions error handling"""
        
        # Test with None resolver response
        with patch.object(path_utils_module, 'resolve_best', return_value=None):
            with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
                path_utils_module.get_workspace_path(Mock(), "python")
            
            with pytest.raises(TypeError, match="contest_current_pathが設定されていません"):
                path_utils_module.get_contest_current_path(Mock(), "python")
            
            with pytest.raises(TypeError, match="contest_template_pathが設定されていません"):
                path_utils_module.get_contest_template_path(Mock(), "python")
            
            with pytest.raises(TypeError, match="contest_temp_pathが設定されていません"):
                path_utils_module.get_contest_temp_path(Mock(), "python")
            
            with pytest.raises(ValueError, match="source_file_nameが設定されていません"):
                path_utils_module.get_source_file_name(Mock(), "python")
        
        # Test with wrong key
        mock_node_wrong_key = Mock()
        mock_node_wrong_key.value = "some_value"
        mock_node_wrong_key.key = "wrong_key"
        
        with patch.object(path_utils_module, 'resolve_best', return_value=mock_node_wrong_key):
            with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
                path_utils_module.get_workspace_path(Mock(), "python")
        
        # Test with None value
        mock_node_none_value = Mock()
        mock_node_none_value.value = None
        mock_node_none_value.key = "workspace_path"
        
        with patch.object(path_utils_module, 'resolve_best', return_value=mock_node_none_value):
            with pytest.raises(TypeError, match="workspace_pathが設定されていません"):
                path_utils_module.get_workspace_path(Mock(), "python")