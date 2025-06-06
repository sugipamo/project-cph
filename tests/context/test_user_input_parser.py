"""
Comprehensive tests for user_input_parser module
"""
import pytest
import json
import os
from unittest.mock import Mock, MagicMock, patch
from tests.base.base_test import BaseTest

from src.context.user_input_parser import (
    parse_user_input,
    _load_system_info_direct,
    _save_system_info_direct,
    _parse_command_line_direct,
    _apply_language_direct,
    _apply_env_type_direct,
    _apply_command_direct,
    _apply_problem_name_direct,
    _apply_contest_name_direct,
    _load_shared_config,
    _load_all_env_jsons,
    _merge_with_shared_config,
    _apply_env_json,
    make_dockerfile_loader,
    CONTEST_ENV_DIR
)
from src.context.execution_context import ExecutionContext


class TestSystemInfoOperations(BaseTest):
    """Test system info loading and saving operations"""
    
    def test_load_system_info_direct_file_not_exists(self):
        """Test loading system info when file doesn't exist"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        mock_file_driver.setup_file_not_exists("system_info.json")
        
        result = _load_system_info_direct(operations, "system_info.json")
        
        expected = {
            "command": None,
            "language": None,
            "env_type": None,
            "contest_name": None,
            "problem_name": None,
            "env_json": None,
        }
        assert result == expected
    
    def test_load_system_info_direct_success(self):
        """Test successful loading of system info"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_json": {"python": {"test": "data"}}
        }
        
        mock_file_driver.setup_file_content("system_info.json", json.dumps(system_info))
        
        result = _load_system_info_direct(operations, "system_info.json")
        
        assert result == system_info
    
    def test_load_system_info_direct_missing_env_json_field(self):
        """Test loading system info when env_json field is missing"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a"
        }
        
        mock_file_driver.setup_file_content("system_info.json", json.dumps(system_info))
        
        result = _load_system_info_direct(operations, "system_info.json")
        
        assert result["env_json"] is None
    
    def test_save_system_info_direct(self):
        """Test saving system info"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a",
            "env_json": {"python": {"test": "data"}}
        }
        
        _save_system_info_direct(operations, system_info, "system_info.json")
        
        # Verify the file was written with correct content
        saved_content = mock_file_driver.get_file_content("system_info.json")
        saved_data = json.loads(saved_content)
        assert saved_data == system_info


class TestCommandLineArgumentParsing(BaseTest):
    """Test command line argument parsing functions"""
    
    def setup_test(self):
        """Setup test data"""
        self.mock_context = Mock()
        self.mock_context.language = None
        self.mock_context.env_type = None
        self.mock_context.command_type = None
        self.mock_context.contest_name = None
        self.mock_context.problem_name = None
        
        # Create mock config root
        self.mock_root = Mock()
        
        # Create language nodes
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        
        rust_node = Mock()
        rust_node.key = "rust"
        rust_node.matches = ["rust", "rs"]
        
        self.mock_root.next_nodes = [python_node, rust_node]
    
    def test_apply_language_direct_success(self):
        """Test successful language detection"""
        args = ["py", "local", "test", "abc300", "a"]
        
        new_args, updated_context = _apply_language_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert updated_context.language == "python"
        assert new_args == ["local", "test", "abc300", "a"]
    
    def test_apply_language_direct_no_match(self):
        """Test when no language matches"""
        args = ["unknown", "local", "test", "abc300", "a"]
        
        new_args, updated_context = _apply_language_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert updated_context.language is None
        assert new_args == args
    
    def test_apply_env_type_direct_success(self):
        """Test successful env_type detection"""
        self.mock_context.language = "python"
        
        # Mock env_type resolution
        with patch('src.context.resolver.config_resolver.resolve_by_match_desc') as mock_resolve:
            env_type_parent = Mock()
            local_node = Mock()
            local_node.key = "local"
            local_node.matches = ["local"]
            env_type_parent.next_nodes = [local_node]
            mock_resolve.return_value = [env_type_parent]
            
            args = ["local", "test", "abc300", "a"]
            new_args, updated_context = _apply_env_type_direct(
                args, self.mock_context, self.mock_root
            )
            
            assert updated_context.env_type == "local"
            assert new_args == ["test", "abc300", "a"]
    
    def test_apply_env_type_direct_no_language(self):
        """Test env_type detection when no language is set"""
        self.mock_context.language = None
        
        args = ["local", "test", "abc300", "a"]
        new_args, updated_context = _apply_env_type_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert updated_context.env_type is None
        assert new_args == args
    
    def test_apply_command_direct_success(self):
        """Test successful command detection"""
        self.mock_context.language = "python"
        
        # Mock command resolution
        with patch('src.context.resolver.config_resolver.resolve_by_match_desc') as mock_resolve:
            command_parent = Mock()
            test_node = Mock()
            test_node.key = "test"
            test_node.matches = ["test", "t"]
            command_parent.next_nodes = [test_node]
            mock_resolve.return_value = [command_parent]
            
            args = ["t", "abc300", "a"]
            new_args, updated_context = _apply_command_direct(
                args, self.mock_context, self.mock_root
            )
            
            assert updated_context.command_type == "test"
            assert new_args == ["abc300", "a"]
    
    def test_apply_command_direct_no_language(self):
        """Test command detection when no language is set"""
        self.mock_context.language = None
        
        args = ["test", "abc300", "a"]
        new_args, updated_context = _apply_command_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert updated_context.command_type is None
        assert new_args == args
    
    def test_apply_problem_name_direct(self):
        """Test problem name extraction"""
        args = ["abc300", "a"]
        
        new_args, updated_context = _apply_problem_name_direct(
            args, self.mock_context
        )
        
        assert updated_context.problem_name == "a"
        assert new_args == ["abc300"]
    
    def test_apply_problem_name_direct_empty_args(self):
        """Test problem name extraction with empty args"""
        args = []
        
        new_args, updated_context = _apply_problem_name_direct(
            args, self.mock_context
        )
        
        assert updated_context.problem_name is None
        assert new_args == []
    
    def test_apply_contest_name_direct(self):
        """Test contest name extraction"""
        args = ["abc300"]
        
        new_args, updated_context = _apply_contest_name_direct(
            args, self.mock_context
        )
        
        assert updated_context.contest_name == "abc300"
        assert new_args == []
    
    def test_parse_command_line_direct_complete_flow(self):
        """Test complete command line parsing flow"""
        self.mock_context.language = None
        
        # Setup comprehensive mocks for the complete flow
        with patch('src.context.resolver.config_resolver.resolve_by_match_desc') as mock_resolve:
            # Mock env_type resolution
            env_type_parent = Mock()
            local_node = Mock()
            local_node.key = "local"
            local_node.matches = ["local"]
            env_type_parent.next_nodes = [local_node]
            
            # Mock command resolution
            command_parent = Mock()
            test_node = Mock()
            test_node.key = "test"
            test_node.matches = ["test", "t"]
            command_parent.next_nodes = [test_node]
            
            mock_resolve.side_effect = [
                [env_type_parent],  # env_type resolution
                [command_parent]    # command resolution
            ]
            
            args = ["py", "local", "t", "abc300", "a"]
            
            remaining_args, updated_context = _parse_command_line_direct(
                args, self.mock_context, self.mock_root
            )
            
            assert remaining_args == []
            assert updated_context.language == "python"
            assert updated_context.env_type == "local"
            assert updated_context.command_type == "test"
            assert updated_context.contest_name == "abc300"
            assert updated_context.problem_name == "a"


class TestEnvJsonOperations(BaseTest):
    """Test env.json loading and processing operations"""
    
    def test_load_shared_config_success(self):
        """Test successful shared config loading"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        shared_config = {
            "shared": {
                "paths": {"workspace_path": "./workspace"},
                "output": {"show_details": True}
            }
        }
        
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_content(shared_path, json.dumps(shared_config))
        
        result = _load_shared_config("contest_env", operations)
        
        assert result == shared_config
    
    def test_load_shared_config_file_not_found(self):
        """Test shared config loading when file doesn't exist"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_not_exists(shared_path)
        
        result = _load_shared_config("contest_env", operations)
        
        assert result is None
    
    @patch('glob.glob')
    def test_load_all_env_jsons_success(self, mock_glob):
        """Test successful loading of all env.json files"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup base directory to exist
        mock_file_driver.setup_file_content("contest_env/.placeholder", "")
        
        # Mock glob to return specific paths
        mock_glob.return_value = [
            "contest_env/python/env.json",
            "contest_env/rust/env.json",
            "contest_env/shared/env.json"  # Should be excluded
        ]
        
        # Setup shared config
        shared_config = {"shared": {"test": "data"}}
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_content(shared_path, json.dumps(shared_config))
        
        # Setup environment configs
        python_env = {"python": {"language_name": "Python"}}
        rust_env = {"rust": {"language_name": "Rust"}}
        
        mock_file_driver.setup_file_content("contest_env/python/env.json", json.dumps(python_env))
        mock_file_driver.setup_file_content("contest_env/rust/env.json", json.dumps(rust_env))
        
        # Mock ValidationService to avoid dependency
        with patch('src.context.user_input_parser.ValidationService'):
            result = _load_all_env_jsons("contest_env", operations)
        
        assert len(result) == 2
        assert python_env in result
        assert rust_env in result
    
    @patch('glob.glob')
    @patch('builtins.print')
    def test_load_all_env_jsons_with_invalid_json(self, mock_print, mock_glob):
        """Test loading env.json files with invalid JSON"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup base directory to exist
        mock_file_driver.setup_file_content("contest_env/.placeholder", "")
        
        mock_glob.return_value = ["contest_env/invalid/env.json"]
        
        # Setup shared config (empty)
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_not_exists(shared_path)
        
        # Setup invalid JSON
        mock_file_driver.setup_file_content("contest_env/invalid/env.json", "invalid json")
        
        result = _load_all_env_jsons("contest_env", operations)
        
        assert result == []
        mock_print.assert_called()
        assert "Warning: Failed to load" in mock_print.call_args[0][0]
    
    def test_merge_with_shared_config_no_shared(self):
        """Test merging when there's no shared config"""
        env_json = {"python": {"language_name": "Python"}}
        shared_config = None
        
        result = _merge_with_shared_config(env_json, shared_config)
        
        assert result == env_json
    
    def test_merge_with_shared_config_success(self):
        """Test successful merging with shared config"""
        env_json = {
            "python": {
                "language_name": "Python",
                "commands": {"test": "existing"}
            }
        }
        
        shared_config = {
            "shared": {
                "paths": {"workspace_path": "./workspace"},
                "local": {"timeout": 300},
                "output": {"show_details": True}
            }
        }
        
        result = _merge_with_shared_config(env_json, shared_config)
        
        # Check that shared section is added
        assert "shared" in result
        assert result["shared"] == shared_config["shared"]
        
        # Check that paths are merged into language config
        assert result["python"]["workspace_path"] == "./workspace"
        
        # Check that env_types are created with local config
        assert "env_types" in result["python"]
        assert result["python"]["env_types"]["local"]["timeout"] == 300
        
        # Check that output config is merged
        assert "output" in result["python"]
        assert result["python"]["output"]["show_details"] is True
    
    def test_apply_env_json_with_matching_language(self):
        """Test applying env_json when language matches"""
        context = Mock()
        context.language = "python"
        context.env_json = None
        
        env_jsons = [
            {"rust": {"language_name": "Rust"}},
            {"python": {"language_name": "Python"}}
        ]
        
        # Mock shared config loading
        with patch('src.context.user_input_parser._load_shared_config') as mock_load_shared:
            mock_load_shared.return_value = None
            
            result = _apply_env_json(context, env_jsons, "contest_env", Mock())
        
        assert result.env_json == {"python": {"language_name": "Python"}}
    
    def test_apply_env_json_no_matching_language(self):
        """Test applying env_json when no language matches"""
        context = Mock()
        context.language = "go"
        context.env_json = None
        
        env_jsons = [
            {"rust": {"language_name": "Rust"}},
            {"python": {"language_name": "Python"}}
        ]
        
        result = _apply_env_json(context, env_jsons)
        
        assert result.env_json is None


class TestDockerfileLoader(BaseTest):
    """Test dockerfile loader functionality"""
    
    def test_make_dockerfile_loader(self):
        """Test creating and using dockerfile loader"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        dockerfile_content = "FROM python:3.9\\nRUN pip install pytest"
        mock_file_driver.setup_file_content("/path/to/Dockerfile", dockerfile_content)
        
        loader = make_dockerfile_loader(operations)
        result = loader("/path/to/Dockerfile")
        
        assert result == dockerfile_content


class TestParseUserInputIntegration(BaseTest):
    """Test complete parse_user_input function"""
    
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_parse_user_input_success(self, mock_resolve, mock_create_root, mock_load_env_jsons):
        """Test successful complete user input parsing"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup system info (empty file)
        mock_file_driver.setup_file_not_exists("system_info.json")
        
        # Setup env jsons
        python_env = {
            "python": {
                "language_name": "Python",
                "env_types": {
                    "local": {"aliases": ["local"]}
                },
                "commands": {
                    "test": {"aliases": ["test", "t"]}
                }
            }
        }
        mock_load_env_jsons.return_value = [python_env]
        
        # Setup config root with proper structure
        mock_root = Mock()
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        mock_root.next_nodes = [python_node]
        mock_create_root.return_value = mock_root
        
        # Setup resolve_by_match_desc for env_type and command resolution
        env_type_parent = Mock()
        local_node = Mock()
        local_node.key = "local"
        local_node.matches = ["local"]
        env_type_parent.next_nodes = [local_node]
        
        command_parent = Mock()
        test_node = Mock()
        test_node.key = "test"
        test_node.matches = ["test", "t"]
        command_parent.next_nodes = [test_node]
        
        mock_resolve.side_effect = [
            [env_type_parent],  # env_type resolution
            [command_parent]    # command resolution
        ]
        
        # Setup shared config (empty)
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_not_exists(shared_path)
        
        args = ["py", "local", "t", "abc300", "a"]
        
        with patch('src.context.user_input_parser.ValidationService'):
            result = parse_user_input(args, operations)
        
        assert isinstance(result, ExecutionContext)
        assert result.language == "python"
        assert result.env_type == "local"
        assert result.command_type == "test"
        assert result.contest_name == "abc300"
        assert result.problem_name == "a"
        # previous情報は、コマンドライン引数解析前のsystem_infoから取得
        assert result.previous_contest_name is None  # system_infoが空だったため
        assert result.previous_problem_name is None
    
    def test_parse_user_input_too_many_args(self):
        """Test parse_user_input with too many arguments"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup empty system info
        mock_file_driver.setup_file_not_exists("system_info.json")
        
        # Mock minimal dependencies
        with patch('src.context.user_input_parser._load_all_env_jsons') as mock_load_env_jsons:
            with patch('src.context.user_input_parser.create_config_root_from_dict') as mock_create_root:
                with patch('src.context.user_input_parser.ValidationService'):
                    mock_load_env_jsons.return_value = []
                    mock_create_root.return_value = Mock()
                    
                    # Mock command line parsing to return extra args
                    with patch('src.context.user_input_parser._parse_command_line_direct') as mock_parse:
                        mock_parse.return_value = (["extra", "args"], Mock())
                        
                        with pytest.raises(ValueError, match="引数が多すぎます"):
                            parse_user_input(["py", "local", "t", "abc300", "a", "extra"], operations)
    
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    def test_parse_user_input_validation_fails(self, mock_create_root, mock_load_env_jsons):
        """Test parse_user_input when context validation fails"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup empty system info
        mock_file_driver.setup_file_not_exists("system_info.json")
        
        mock_load_env_jsons.return_value = []
        mock_create_root.return_value = Mock()
        
        # Mock context that fails validation
        mock_context = Mock()
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.env_type = "local"
        mock_context.contest_name = "abc300"
        mock_context.problem_name = "a"
        mock_context.env_json = None
        mock_context.validate.return_value = (False, "Validation error message")
        
        with patch('src.context.user_input_parser._parse_command_line_direct') as mock_parse:
            with patch('src.context.user_input_parser.ExecutionContext') as mock_exec_context:
                with patch('src.context.user_input_parser.ValidationService'):
                    mock_parse.return_value = ([], mock_context)
                    mock_exec_context.return_value = mock_context
                    
                    with pytest.raises(ValueError, match="Validation error message"):
                        parse_user_input(["py", "local", "t", "abc300", "a"], operations)
    
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    @patch('src.context.resolver.config_resolver.resolve_by_match_desc')
    def test_parse_user_input_with_previous_info(self, mock_resolve, mock_create_root, mock_load_env_jsons):
        """Test parse_user_input with existing previous information"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Setup system info with existing data (previous information)
        existing_system_info = {
            "command": "test",
            "language": "python", 
            "contest_name": "abc299",  # previous contest
            "problem_name": "b",       # previous problem
            "env_type": "local",
            "env_json": None
        }
        mock_file_driver.setup_file_content("system_info.json", json.dumps(existing_system_info))
        
        # Setup env jsons
        python_env = {
            "python": {
                "language_name": "Python",
                "env_types": {
                    "local": {"aliases": ["local"]}
                },
                "commands": {
                    "test": {"aliases": ["test", "t"]}
                }
            }
        }
        mock_load_env_jsons.return_value = [python_env]
        
        # Setup config root
        mock_root = Mock()
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        mock_root.next_nodes = [python_node]
        mock_create_root.return_value = mock_root
        
        # Setup resolve_by_match_desc
        env_type_parent = Mock()
        local_node = Mock()
        local_node.key = "local" 
        local_node.matches = ["local"]
        env_type_parent.next_nodes = [local_node]
        
        command_parent = Mock()
        test_node = Mock()
        test_node.key = "test"
        test_node.matches = ["test", "t"]
        command_parent.next_nodes = [test_node]
        
        mock_resolve.side_effect = [
            [env_type_parent],  # env_type resolution
            [command_parent]    # command resolution
        ]
        
        # Setup shared config (empty)
        shared_path = os.path.join("contest_env", "shared", "env.json")
        mock_file_driver.setup_file_not_exists(shared_path)
        
        args = ["py", "local", "t", "abc300", "c"]  # New contest and problem
        
        with patch('src.context.user_input_parser.ValidationService'):
            result = parse_user_input(args, operations)
        
        assert isinstance(result, ExecutionContext)
        # New information from command line args
        assert result.language == "python"
        assert result.env_type == "local"
        assert result.command_type == "test"
        assert result.contest_name == "abc300"
        assert result.problem_name == "c"
        # Previous information from existing system_info.json
        assert result.previous_contest_name == "abc299"
        assert result.previous_problem_name == "b"
        
        # Verify new system_info.json was saved with updated values
        saved_content = mock_file_driver.get_file_content("system_info.json")
        saved_data = json.loads(saved_content)
        assert saved_data["contest_name"] == "abc300"
        assert saved_data["problem_name"] == "c"


class TestErrorHandling(BaseTest):
    """Test error handling in various scenarios"""
    
    def test_load_system_info_invalid_json(self):
        """Test loading system info with invalid JSON"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        mock_file_driver.setup_file_content("system_info.json", "invalid json")
        
        with pytest.raises(json.JSONDecodeError):
            _load_system_info_direct(operations, "system_info.json")
    
    @patch('glob.glob')
    def test_load_all_env_jsons_directory_not_exists(self, mock_glob):
        """Test loading env jsons when base directory doesn't exist"""
        operations = self.create_mock_di_container()
        mock_file_driver = operations.resolve("file_driver")
        
        # Don't setup any files for nonexistent_dir, so EXISTS will return False
        # mock_file_driver.setup_file_not_exists("nonexistent_dir")  # This is redundant
        
        result = _load_all_env_jsons("nonexistent_dir", operations)
        
        assert result == []
        # glob should not be called if directory doesn't exist
        mock_glob.assert_not_called()


class TestEdgeCases(BaseTest):
    """Test edge cases and boundary conditions"""
    
    def setup_test(self):
        """Setup test data"""
        self.mock_context = Mock()
        self.mock_context.language = None
        self.mock_context.env_type = None
        self.mock_context.command_type = None
        self.mock_context.contest_name = None
        self.mock_context.problem_name = None
        
        # Create mock config root
        self.mock_root = Mock()
        
        # Create language nodes
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        
        rust_node = Mock()
        rust_node.key = "rust"
        rust_node.matches = ["rust", "rs"]
        
        self.mock_root.next_nodes = [python_node, rust_node]
    
    def test_apply_language_direct_multiple_matches(self):
        """Test language detection with multiple potential matches"""
        # Setup context where first match should be taken
        args = ["py", "python", "local", "test"]
        
        # Only "py" should match and be consumed
        new_args, updated_context = _apply_language_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert updated_context.language == "python"
        # "python" should remain in args since "py" was already matched
        assert new_args == ["python", "local", "test"]
    
    def test_merge_with_shared_config_complex_structure(self):
        """Test merging with complex shared config structure"""
        env_json = {
            "python": {
                "existing_key": "should_remain",
                "output": {"existing_output": "value"}
            }
        }
        
        shared_config = {
            "shared": {
                "paths": {"workspace_path": "./workspace", "temp_path": "./temp"},
                "output": {"show_details": True, "format": "json"},
                "local": {"timeout": 300, "shell": "bash"}
            }
        }
        
        result = _merge_with_shared_config(env_json, shared_config)
        
        # Verify all paths are merged
        assert result["python"]["workspace_path"] == "./workspace"
        assert result["python"]["temp_path"] == "./temp"
        
        # Verify existing keys are preserved
        assert result["python"]["existing_key"] == "should_remain"
        
        # Verify output configs are merged (existing preserved, new added)
        assert result["python"]["output"]["existing_output"] == "value"
        assert result["python"]["output"]["show_details"] is True
        assert result["python"]["output"]["format"] == "json"
        
        # Verify env_types structure is created correctly
        assert result["python"]["env_types"]["local"]["timeout"] == 300
        assert result["python"]["env_types"]["local"]["shell"] == "bash"
    
    def test_parse_command_line_direct_empty_args(self):
        """Test command line parsing with empty arguments"""
        args = []
        
        remaining_args, updated_context = _parse_command_line_direct(
            args, self.mock_context, self.mock_root
        )
        
        assert remaining_args == []
        assert updated_context.language is None
        assert updated_context.env_type is None
        assert updated_context.command_type is None
        assert updated_context.contest_name is None
        assert updated_context.problem_name is None