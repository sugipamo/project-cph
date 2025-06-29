"""Tests for user input parser integration."""
import pytest
from unittest.mock import Mock, MagicMock, PropertyMock
from src.presentation.user_input_parser_integration import (
    UserInputParserIntegration,
    create_new_execution_context
)


class TestUserInputParserIntegration:
    """Test cases for UserInputParserIntegration class."""

    def test_init(self):
        """Test initialization."""
        config_manager = Mock()
        contest_env_dir = "/test/contest"
        system_config_dir = "/test/system"
        
        integration = UserInputParserIntegration(
            config_manager, 
            contest_env_dir, 
            system_config_dir
        )
        
        assert integration.config_manager is config_manager
        assert integration.contest_env_dir == contest_env_dir
        assert integration.system_config_dir == system_config_dir

    def test_create_execution_configuration_from_context(self):
        """Test creating execution configuration from context."""
        # Setup mocks
        config_manager = Mock()
        mock_config = Mock()
        config_manager.create_execution_config.return_value = mock_config
        
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Test parameters
        command_type = "run"
        language = "python"
        contest_name = "test_contest"
        problem_name = "a"
        env_type = "docker"
        env_json = {"key": "value"}
        
        # Execute
        result = integration.create_execution_configuration_from_context(
            command_type, language, contest_name, 
            problem_name, env_type, env_json
        )
        
        # Verify
        assert result is mock_config
        config_manager.load_from_files.assert_called_once_with(
            integration.system_config_dir, 
            integration.contest_env_dir, 
            language
        )
        config_manager.create_execution_config.assert_called_once_with(
            contest_name=contest_name,
            problem_name=problem_name,
            language=language,
            env_type=env_type,
            command_type=command_type
        )

    def test_create_execution_context_adapter(self):
        """Test creating execution context adapter."""
        # Setup mocks
        config_manager = Mock()
        mock_config = Mock()
        config_manager.create_execution_config.return_value = mock_config
        
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Test parameters
        command_type = "test"
        language = "cpp"
        contest_name = "abc123"
        problem_name = "b"
        env_type = "local"
        env_json = {"timeout": 30}
        
        # Execute
        result = integration.create_execution_context_adapter(
            command_type, language, contest_name,
            problem_name, env_type, env_json
        )
        
        # Verify - should call the same method
        assert result is mock_config
        config_manager.create_execution_config.assert_called_once()

    def test_validate_new_system_compatibility_success(self):
        """Test successful compatibility validation."""
        config_manager = Mock()
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Create old context mock
        old_context = Mock()
        old_context.contest_name = "test_contest"
        old_context.language = "python"
        
        # Create new config mock
        new_config = Mock()
        new_config.contest_name = "test_contest"
        new_config.language = "python"
        
        # Execute
        result = integration.validate_new_system_compatibility(
            old_context, new_config
        )
        
        assert result is True

    def test_validate_new_system_compatibility_contest_mismatch(self):
        """Test compatibility validation with contest name mismatch."""
        config_manager = Mock()
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Create old context mock
        old_context = Mock()
        old_context.contest_name = "test_contest"
        old_context.language = "python"
        
        # Create new config mock
        new_config = Mock()
        new_config.contest_name = "different_contest"
        new_config.language = "python"
        
        # Execute
        result = integration.validate_new_system_compatibility(
            old_context, new_config
        )
        
        assert result is False

    def test_validate_new_system_compatibility_language_mismatch(self):
        """Test compatibility validation with language mismatch."""
        config_manager = Mock()
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Create old context mock
        old_context = Mock()
        old_context.contest_name = "test_contest"
        old_context.language = "python"
        
        # Create new config mock
        new_config = Mock()
        new_config.contest_name = "test_contest"
        new_config.language = "cpp"
        
        # Execute
        result = integration.validate_new_system_compatibility(
            old_context, new_config
        )
        
        assert result is False

    def test_validate_new_system_compatibility_no_attributes(self):
        """Test compatibility validation when old context has no attributes."""
        config_manager = Mock()
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Create old context mock without attributes
        old_context = Mock(spec=[])
        
        # Create new config mock
        new_config = Mock()
        new_config.contest_name = "test_contest"
        new_config.language = "python"
        
        # Execute
        result = integration.validate_new_system_compatibility(
            old_context, new_config
        )
        
        assert result is True

    def test_validate_new_system_compatibility_exception(self):
        """Test compatibility validation with exception."""
        config_manager = Mock()
        integration = UserInputParserIntegration(config_manager, "/test/contest", "/test/system")
        
        # Create old context that raises exception when accessed
        old_context = Mock()
        type(old_context).contest_name = PropertyMock(side_effect=Exception("Test error"))
        
        # Create new config
        new_config = Mock()
        new_config.contest_name = "test"
        
        # Execute
        with pytest.raises(ValueError, match="Failed to validate compatibility"):
            integration.validate_new_system_compatibility(
                old_context, new_config
            )


class TestCreateNewExecutionContext:
    """Test cases for create_new_execution_context function."""
    
    def test_create_new_execution_context(self):
        """Test creating new execution context."""
        # Test parameters
        command_type = "run"
        language = "python"
        contest_name = "test_contest"
        problem_name = "a"
        env_type = "docker"
        env_json = {"key": "value"}
        resolver = Mock()
        
        # Mock the integration creation
        from unittest.mock import patch
        with patch('src.presentation.user_input_parser_integration.UserInputParserIntegration') as mock_integration_class:
            mock_integration = Mock()
            mock_config = Mock()
            mock_integration.create_execution_context_adapter.return_value = mock_config
            mock_integration_class.return_value = mock_integration
            
            # Execute
            result = create_new_execution_context(
                command_type, language, contest_name,
                problem_name, env_type, env_json, resolver
            )
            
            # Verify
            assert result is mock_config
            mock_integration_class.assert_called_once()
            mock_integration.create_execution_context_adapter.assert_called_once_with(
                command_type, language, contest_name,
                problem_name, env_type, env_json
            )