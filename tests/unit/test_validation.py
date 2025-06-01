"""
Test validation utilities
"""
import pytest
from src.utils.validation import (
    validate_execution_context,
    validate_file_path,
    validate_docker_image_name,
    validate_step_config,
    validate_config_keys,
    validate_environment_setup,
    is_script_file
)


class TestValidateExecutionContext:
    """Test execution context validation"""
    
    def test_valid_execution_context(self):
        """Test valid execution context"""
        env_config = {
            "python": {"commands": {"test": {"steps": []}}}
        }
        
        is_valid, error = validate_execution_context(
            "test", "python", "abc300", "a", env_config
        )
        
        assert is_valid is True
        assert error is None
    
    def test_missing_command_type(self):
        """Test missing command type"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "", "python", "abc300", "a", env_config
        )
        
        assert is_valid is False
        assert "コマンドタイプ" in error
    
    def test_missing_language(self):
        """Test missing language"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "test", "", "abc300", "a", env_config
        )
        
        assert is_valid is False
        assert "言語" in error
    
    def test_missing_contest_name(self):
        """Test missing contest name"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "test", "python", "", "a", env_config
        )
        
        assert is_valid is False
        assert "コンテスト名" in error
    
    def test_missing_problem_name(self):
        """Test missing problem name"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "test", "python", "abc300", "", env_config
        )
        
        assert is_valid is False
        assert "問題名" in error
    
    def test_multiple_missing_fields(self):
        """Test multiple missing fields"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "", "", "", "", env_config
        )
        
        assert is_valid is False
        assert "コマンドタイプ" in error
        assert "言語" in error
        assert "コンテスト名" in error
        assert "問題名" in error
    
    def test_empty_env_config(self):
        """Test empty environment config"""
        is_valid, error = validate_execution_context(
            "test", "python", "abc300", "a", {}
        )
        
        assert is_valid is False
        assert "環境設定が見つかりません" in error
    
    def test_unsupported_language(self):
        """Test unsupported language"""
        env_config = {"python": {}}
        
        is_valid, error = validate_execution_context(
            "test", "rust", "abc300", "a", env_config
        )
        
        assert is_valid is False
        assert "rust" in error
        assert "環境設定に含まれていません" in error


class TestValidateFilePath:
    """Test file path validation"""
    
    def test_valid_file_path(self):
        """Test valid file path"""
        is_valid, error = validate_file_path("/home/user/file.txt")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_file_path("relative/path/file.txt")
        assert is_valid is True
        assert error is None
    
    def test_empty_path(self):
        """Test empty path"""
        is_valid, error = validate_file_path("")
        assert is_valid is False
        assert "パスが空です" in error
    
    def test_absolute_path_with_parent_reference(self):
        """Test absolute path with parent directory reference"""
        is_valid, error = validate_file_path("/home/../etc/passwd")
        assert is_valid is False
        assert "絶対パスに '..' を含めることはできません" in error
    
    def test_relative_path_with_parent_reference(self):
        """Test relative path with parent reference is allowed"""
        is_valid, error = validate_file_path("../relative/path")
        assert is_valid is True
        assert error is None
    
    def test_dangerous_characters(self):
        """Test paths with dangerous characters"""
        dangerous_paths = [
            "/path/with|pipe",
            "/path/with;semicolon",
            "/path/with&ampersand",
            "/path/with$dollar",
            "/path/with`backtick"
        ]
        
        for path in dangerous_paths:
            is_valid, error = validate_file_path(path)
            assert is_valid is False
            assert "危険な文字が含まれています" in error


class TestValidateDockerImageName:
    """Test Docker image name validation"""
    
    def test_valid_image_names(self):
        """Test valid Docker image names"""
        valid_names = [
            "ubuntu",
            "ubuntu:20.04",
            "library/ubuntu",
            "docker.io/library/ubuntu:latest",
            "my-registry.com/my-image:1.0.0",
            "test_image-123"
        ]
        
        for name in valid_names:
            is_valid, error = validate_docker_image_name(name)
            assert is_valid is True, f"Failed for: {name}"
            assert error is None
    
    def test_empty_image_name(self):
        """Test empty image name"""
        is_valid, error = validate_docker_image_name("")
        assert is_valid is False
        assert "イメージ名が空です" in error
    
    def test_invalid_image_names(self):
        """Test invalid Docker image names"""
        invalid_names = [
            "with spaces",
            "with@special",
            "with#hash",
            "-startwithdash",
            "endwithdash-",
            "../parent",
            ".",
            ""
        ]
        
        for name in invalid_names:
            is_valid, error = validate_docker_image_name(name)
            assert is_valid is False, f"Should fail for: {name}"
            if name:  # Empty string has different error message
                assert "無効なイメージ名形式" in error


class TestValidateStepConfig:
    """Test step configuration validation"""
    
    def test_valid_step_config(self):
        """Test valid step configuration"""
        step_config = {
            "type": "shell",
            "cmd": ["echo", "hello"]
        }
        
        is_valid, errors = validate_step_config(step_config)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        # Missing both type and cmd
        is_valid, errors = validate_step_config({})
        assert is_valid is False
        assert len(errors) == 2
        assert any("type" in error for error in errors)
        assert any("cmd" in error for error in errors)
        
        # Missing cmd
        is_valid, errors = validate_step_config({"type": "shell"})
        assert is_valid is False
        assert len(errors) == 1
        assert "cmd" in errors[0]
        
        # Missing type
        is_valid, errors = validate_step_config({"cmd": ["echo"]})
        assert is_valid is False
        assert len(errors) == 1
        assert "type" in errors[0]
    
    def test_invalid_step_type(self):
        """Test invalid step type"""
        step_config = {
            "type": "invalid_type",
            "cmd": ["echo", "hello"]
        }
        
        is_valid, errors = validate_step_config(step_config)
        assert is_valid is False
        assert len(errors) == 1
        assert "無効なステップタイプ" in errors[0]
        assert "invalid_type" in errors[0]
    
    def test_empty_command(self):
        """Test empty command"""
        step_config = {
            "type": "shell",
            "cmd": []
        }
        
        is_valid, errors = validate_step_config(step_config)
        assert is_valid is False
        assert len(errors) == 1
        assert "コマンドフィールドが空です" in errors[0]
    
    def test_all_valid_step_types(self):
        """Test all valid step types"""
        valid_types = ['shell', 'python', 'copy', 'move', 'mkdir', 'rmtree', 'remove', 'touch']
        
        for step_type in valid_types:
            step_config = {
                "type": step_type,
                "cmd": ["some", "command"]
            }
            is_valid, errors = validate_step_config(step_config)
            assert is_valid is True, f"Failed for type: {step_type}"
            assert len(errors) == 0


class TestValidateConfigKeys:
    """Test configuration key validation"""
    
    def test_all_keys_present(self):
        """Test when all required keys are present"""
        config = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        required_keys = ["key1", "key2"]
        
        is_valid, missing = validate_config_keys(config, required_keys)
        assert is_valid is True
        assert len(missing) == 0
    
    def test_missing_keys(self):
        """Test when keys are missing"""
        config = {
            "key1": "value1"
        }
        required_keys = ["key1", "key2", "key3"]
        
        is_valid, missing = validate_config_keys(config, required_keys)
        assert is_valid is False
        assert len(missing) == 2
        assert "key2" in missing
        assert "key3" in missing
    
    def test_empty_config(self):
        """Test empty configuration"""
        config = {}
        required_keys = ["key1", "key2"]
        
        is_valid, missing = validate_config_keys(config, required_keys)
        assert is_valid is False
        assert len(missing) == 2
        assert missing == ["key1", "key2"]
    
    def test_no_required_keys(self):
        """Test when no keys are required"""
        config = {"any": "value"}
        required_keys = []
        
        is_valid, missing = validate_config_keys(config, required_keys)
        assert is_valid is True
        assert len(missing) == 0


class TestValidateEnvironmentSetup:
    """Test environment setup validation"""
    
    def test_valid_environment_setup(self):
        """Test valid environment setup"""
        env_config = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {"type": "shell", "cmd": ["pytest"]}
                        ]
                    }
                }
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is True
        assert error is None
    
    def test_missing_language(self):
        """Test missing language in config"""
        env_config = {
            "python": {}
        }
        
        is_valid, error = validate_environment_setup(env_config, "rust", "test")
        assert is_valid is False
        assert "rust" in error
        assert "設定が見つかりません" in error
    
    def test_missing_commands_section(self):
        """Test missing commands section"""
        env_config = {
            "python": {
                "other_config": "value"
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is False
        assert "コマンド設定がありません" in error
    
    def test_missing_command_type(self):
        """Test missing specific command type"""
        env_config = {
            "python": {
                "commands": {
                    "build": {"steps": []}
                }
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is False
        assert "test" in error
        assert "設定がありません" in error
    
    def test_missing_steps_section(self):
        """Test missing steps section"""
        env_config = {
            "python": {
                "commands": {
                    "test": {
                        "other": "value"
                    }
                }
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is False
        assert "ステップ設定がありません" in error
    
    def test_empty_steps_list(self):
        """Test empty steps list"""
        env_config = {
            "python": {
                "commands": {
                    "test": {
                        "steps": []
                    }
                }
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is False
        assert "ステップが空です" in error
    
    def test_steps_not_list(self):
        """Test steps is not a list"""
        env_config = {
            "python": {
                "commands": {
                    "test": {
                        "steps": "not a list"
                    }
                }
            }
        }
        
        is_valid, error = validate_environment_setup(env_config, "python", "test")
        assert is_valid is False
        assert "ステップが空です" in error


class TestIsScriptFile:
    """Test script file detection"""
    
    def test_default_script_extensions(self):
        """Test with default script extensions"""
        script_files = [
            "main.py",
            "script.js",
            "run.sh",
            "app.rb",
            "main.go",
            "lib.rs",
            "program.cpp",
            "code.c",
            "Main.java"
        ]
        
        for file_path in script_files:
            assert is_script_file(file_path) is True, f"Failed for: {file_path}"
    
    def test_non_script_files(self):
        """Test non-script files"""
        non_script_files = [
            "document.txt",
            "image.png",
            "data.json",
            "config.yaml",
            "README.md"
        ]
        
        for file_path in non_script_files:
            assert is_script_file(file_path) is False, f"Failed for: {file_path}"
    
    def test_custom_script_extensions(self):
        """Test with custom script extensions"""
        custom_extensions = [".pl", ".lua", ".php"]
        
        assert is_script_file("script.pl", custom_extensions) is True
        assert is_script_file("game.lua", custom_extensions) is True
        assert is_script_file("index.php", custom_extensions) is True
        assert is_script_file("main.py", custom_extensions) is False
    
    def test_path_with_directories(self):
        """Test file paths with directories"""
        assert is_script_file("/home/user/project/main.py") is True
        assert is_script_file("src/components/App.js") is True
        assert is_script_file("./scripts/run.sh") is True
        assert is_script_file("../lib/helper.rb") is True