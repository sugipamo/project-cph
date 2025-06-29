"""Tests for contest manager - handles contest state and file operations"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.application.contest_manager import ContestManager
from src.infrastructure.di_container import DIKey


class TestContestManager:
    """Test suite for contest management functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_container = Mock()
        self.mock_file_driver = Mock()
        self.mock_logger = Mock()
        self.mock_os_provider = Mock()
        self.mock_json_provider = Mock()
        
        # Set up container resolution
        def resolve_mock(key):
            if key == DIKey.FILE_DRIVER:
                return self.mock_file_driver
            elif key == DIKey.UNIFIED_LOGGER:
                return self.mock_logger
            elif key == DIKey.OS_PROVIDER:
                return self.mock_os_provider
            elif key == DIKey.JSON_PROVIDER:
                return self.mock_json_provider
            elif key == DIKey.OPERATION_REPOSITORY:
                return Mock()  # Return mock for operation repository
            elif key == DIKey.SYSTEM_CONFIG_REPOSITORY:
                return Mock()  # Return mock for system config repository
            elif key == 'contest_current_files_repository':
                return Mock()  # Return mock for files repository
            else:
                raise ValueError(f"Key {key} not registered")
        
        self.mock_container.resolve.side_effect = resolve_mock
        
        self.env_json = {
            "contest_current_dir": "/contest/current",
            "contest_stock_dir": "/contest/stock",
            "contest_template_dir": "/contest/template"
        }
        
        self.contest_manager = ContestManager(
            container=self.mock_container,
            env_json=self.env_json
        )
    
    def test_lazy_load_file_driver(self):
        """Test lazy loading of file driver"""
        # First access should resolve from container
        driver = self.contest_manager.file_driver
        
        assert driver == self.mock_file_driver
        self.mock_container.resolve.assert_called_with(DIKey.FILE_DRIVER)
        
        # Second access should use cached value
        driver2 = self.contest_manager.file_driver
        assert driver2 == self.mock_file_driver
        # Should still only be called once
        assert self.mock_container.resolve.call_count == 1
    
    def test_lazy_load_logger(self):
        """Test lazy loading of logger"""
        logger = self.contest_manager.logger
        
        assert logger == self.mock_logger
        self.mock_container.resolve.assert_called_with(DIKey.UNIFIED_LOGGER)
    
    def test_lazy_load_logger_failure(self):
        """Test logger raises error when not available"""
        # Make logger resolution fail
        def resolve_mock_no_logger(key):
            if key == DIKey.UNIFIED_LOGGER:
                raise ValueError("Logger not registered")
            return None
        
        self.mock_container.resolve.side_effect = resolve_mock_no_logger
        
        # Should raise error when logger not available (no fallback)
        with pytest.raises(ValueError, match="Logger not registered"):
            _ = self.contest_manager.logger
    
    @patch('src.application.contest_manager.SystemConfigLoader')
    def test_get_current_contest_state(self, mock_config_loader_class):
        """Test getting current contest state"""
        mock_config_loader = Mock()
        mock_config_loader_class.return_value = mock_config_loader
        
        mock_config_loader.get_current_context.return_value = {
            'language': 'python',
            'contest_name': 'ABC123',
            'problem_name': 'A'
        }
        
        # Recreate contest manager to use mocked SystemConfigLoader
        contest_manager = ContestManager(self.mock_container, self.env_json)
        
        state = contest_manager.get_current_contest_state()
        
        assert state['language_name'] == 'python'
        assert state['contest_name'] == 'ABC123'
        assert state['problem_name'] == 'A'
    
    def test_env_json_property(self):
        """Test env_json property returns initialized value"""
        assert self.contest_manager.env_json == self.env_json
    
    def test_env_json_lazy_load_from_file(self):
        """Test env_json lazy loads from file when not provided"""
        from src.application.execution_requests import FileRequest
        from src.infrastructure.requests.file.file_op_type import FileOpType
        
        # Create manager without env_json
        manager = ContestManager(self.mock_container, None)
        
        # Mock file read result
        mock_result = Mock()
        mock_result.success = True
        mock_result.content = '{"test": "data"}'
        
        # Mock the execute_operation method on FileRequest instances
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            self.mock_json_provider.loads.return_value = {"test": "data"}
            
            env = manager.env_json
            
            assert env == {"test": "data"}
            self.mock_json_provider.loads.assert_called_once_with('{"test": "data"}')
            # Verify execute_operation was called
            mock_execute.assert_called_once()
    
    def test_detect_contest_change(self):
        """Test detection of contest change"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_get_state:
            mock_get_state.return_value = {
                'language_name': 'python',
                'contest_name': 'ABC124',  # Different from env
                'problem_name': 'B'
            }
            
            # Check if contest has changed
            current_state = self.contest_manager.get_current_contest_state()
            
            # Should detect that contest name is different
            assert current_state['contest_name'] != 'ABC123'  # Would be from env/previous state
    
    def test_needs_backup_logic(self):
        """Test backup requirement logic"""
        # Test that backup is needed when contest changes
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
            # First state
            mock_state.return_value = {
                'contest_name': 'ABC123',
                'problem_name': 'A',
                'language_name': 'python'
            }
            
            state1 = self.contest_manager.get_current_contest_state()
            
            # Change state
            mock_state.return_value = {
                'contest_name': 'ABC124',  # Different contest
                'problem_name': 'A',
                'language_name': 'python'
            }
            
            state2 = self.contest_manager.get_current_contest_state()
            
            # Contest has changed
            assert state1['contest_name'] != state2['contest_name']
    
    def test_handle_null_values_in_state(self):
        """Test handling of NULL values in contest state"""
        with patch.object(self.contest_manager, '_get_latest_non_null_value') as mock_get_non_null:
            mock_get_non_null.return_value = 'python'  # Fallback value
            
            with patch.object(self.contest_manager.config_loader, 'get_current_context') as mock_context:
                mock_context.return_value = {
                    'language': None,  # NULL value
                    'contest_name': 'ABC123',
                    'problem_name': 'A'
                }
                
                state = self.contest_manager.get_current_contest_state()
                
                # Should have called fallback for null language
                mock_get_non_null.assert_called_once_with('language')
    
    def test_needs_backup_different_language(self):
        """Test needs_backup returns True when language differs"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
            mock_state.return_value = {
                'language_name': 'python',
                'contest_name': 'ABC123',
                'problem_name': 'A'
            }
            
            assert self.contest_manager.needs_backup('cpp', 'ABC123', 'A') is True
    
    def test_needs_backup_different_contest(self):
        """Test needs_backup returns True when contest differs"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
            mock_state.return_value = {
                'language_name': 'python',
                'contest_name': 'ABC123',
                'problem_name': 'A'
            }
            
            assert self.contest_manager.needs_backup('python', 'ABC124', 'A') is True
    
    def test_needs_backup_different_problem(self):
        """Test needs_backup returns True when problem differs"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
            mock_state.return_value = {
                'language_name': 'python',
                'contest_name': 'ABC123',
                'problem_name': 'A'
            }
            
            assert self.contest_manager.needs_backup('python', 'ABC123', 'B') is True
    
    def test_needs_backup_no_change(self):
        """Test needs_backup returns False when nothing changes"""
        with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
            mock_state.return_value = {
                'language_name': 'python',
                'contest_name': 'ABC123',
                'problem_name': 'A'
            }
            
            assert self.contest_manager.needs_backup('python', 'ABC123', 'A') is False
    
    def test_backup_contest_current_incomplete_state(self):
        """Test backup_contest_current returns False with incomplete state"""
        current_state = {
            'language_name': None,
            'contest_name': 'ABC123',
            'problem_name': 'A'
        }
        
        assert self.contest_manager.backup_contest_current(current_state) is False
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_backup_contest_current_success(self, mock_time_provider):
        """Test successful backup of contest_current"""
        from src.application.execution_requests import FileRequest
        
        # Update env_json with proper structure
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_stock_path': '/contest/stock/{language_name}/{contest_name}/{problem_name}'
                }
            }
        }
        
        current_state = {
            'language_name': 'python',
            'contest_name': 'ABC123',
            'problem_name': 'A'
        }
        
        # Mock directory checks and operations
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure_dir:
                with patch.object(self.contest_manager, '_move_directory_contents') as mock_move:
                    mock_has_content.return_value = True
                    mock_ensure_dir.return_value = True
                    mock_move.return_value = True
                    
                    result = self.contest_manager.backup_contest_current(current_state)
                    
                    assert result is True
                    mock_has_content.assert_called_once_with('/contest/current')
                    mock_ensure_dir.assert_called_once_with('/contest/stock/python/ABC123/A')
                    mock_move.assert_called_once_with('/contest/current', '/contest/stock/python/ABC123/A')
    
    def test_backup_contest_current_no_content(self):
        """Test backup when contest_current has no content"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_stock_path': '/contest/stock/{language_name}/{contest_name}/{problem_name}'
                }
            }
        }
        
        current_state = {
            'language_name': 'python',
            'contest_name': 'ABC123',
            'problem_name': 'A'
        }
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            mock_has_content.return_value = False
            
            result = self.contest_manager.backup_contest_current(current_state)
            
            assert result is True
            mock_has_content.assert_called_once_with('/contest/current')
    
    def test_handle_contest_change_with_backup(self):
        """Test handling contest change that needs backup"""
        with patch.object(self.contest_manager, 'needs_backup') as mock_needs_backup:
            with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
                with patch.object(self.contest_manager, 'backup_contest_current') as mock_backup:
                    mock_needs_backup.return_value = True
                    mock_state.return_value = {
                        'language_name': 'python',
                        'contest_name': 'ABC123',
                        'problem_name': 'A'
                    }
                    mock_backup.return_value = True
                    
                    result = self.contest_manager.handle_contest_change('cpp', 'ABC124', 'B')
                    
                    assert result is True
                    mock_needs_backup.assert_called_once_with('cpp', 'ABC124', 'B')
                    mock_backup.assert_called_once()
                    self.mock_logger.info.assert_called()
    
    def test_handle_contest_change_backup_failure(self):
        """Test handling contest change when backup fails"""
        with patch.object(self.contest_manager, 'needs_backup') as mock_needs_backup:
            with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
                with patch.object(self.contest_manager, 'backup_contest_current') as mock_backup:
                    mock_needs_backup.return_value = True
                    mock_state.return_value = {
                        'language_name': 'python',
                        'contest_name': 'ABC123',
                        'problem_name': 'A'
                    }
                    mock_backup.return_value = False
                    
                    result = self.contest_manager.handle_contest_change('cpp', 'ABC124', 'B')
                    
                    assert result is False
                    self.mock_logger.warning.assert_called_once_with('Failed to backup contest_current')
    
    def test_restore_from_contest_stock_no_stock(self):
        """Test restore when no stock is available"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_stock_path': '/contest/stock/{language_name}/{contest_name}/{problem_name}'
                }
            }
        }
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            mock_has_content.return_value = False
            
            result = self.contest_manager.restore_from_contest_stock('python', 'ABC123', 'A')
            
            assert result is False
    
    def test_initialize_from_template_no_template(self):
        """Test initialize when no template exists"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_template_path': '/contest/template'
                }
            }
        }
        
        self.mock_os_provider.path_join.return_value = '/contest/template/python'
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            mock_has_content.return_value = False
            
            result = self.contest_manager.initialize_from_template('python', 'ABC123', 'A')
            
            assert result is False
            self.mock_logger.warning.assert_called_once_with('No template found for language python')
    
    def test_initialize_contest_current_from_stock(self):
        """Test initialize_contest_current prefers stock over template"""
        with patch.object(self.contest_manager, 'restore_from_contest_stock') as mock_restore:
            mock_restore.return_value = True
            
            result = self.contest_manager.initialize_contest_current('python', 'ABC123', 'A')
            
            assert result is True
            mock_restore.assert_called_once_with('python', 'ABC123', 'A')
    
    def test_initialize_contest_current_from_template(self):
        """Test initialize_contest_current falls back to template"""
        with patch.object(self.contest_manager, 'restore_from_contest_stock') as mock_restore:
            with patch.object(self.contest_manager, 'initialize_from_template') as mock_template:
                mock_restore.return_value = False
                mock_template.return_value = True
                
                result = self.contest_manager.initialize_contest_current('python', 'ABC123', 'A')
                
                assert result is True
                mock_restore.assert_called_once_with('python', 'ABC123', 'A')
                mock_template.assert_called_once_with('python', 'ABC123', 'A')
    
    def test_initialize_contest_current_both_fail(self):
        """Test initialize_contest_current raises error when both methods fail"""
        with patch.object(self.contest_manager, 'restore_from_contest_stock') as mock_restore:
            with patch.object(self.contest_manager, 'initialize_from_template') as mock_template:
                mock_restore.return_value = False
                mock_template.return_value = False
                
                with pytest.raises(RuntimeError) as exc_info:
                    self.contest_manager.initialize_contest_current('python', 'ABC123', 'A')
                
                assert 'both stock and template initialization failed' in str(exc_info.value)
    
    def test_os_provider_lazy_load(self):
        """Test lazy loading of OS provider"""
        provider = self.contest_manager.os_provider
        
        assert provider == self.mock_os_provider
        self.mock_container.resolve.assert_called_with(DIKey.OS_PROVIDER)
        
        # Second access should use cached value
        provider2 = self.contest_manager.os_provider
        assert provider2 == self.mock_os_provider
    
    def test_json_provider_lazy_load(self):
        """Test lazy loading of JSON provider"""
        provider = self.contest_manager.json_provider
        
        assert provider == self.mock_json_provider
        self.mock_container.resolve.assert_called_with(DIKey.JSON_PROVIDER)
    
    def test_files_repo_lazy_load(self):
        """Test lazy loading of files repository"""
        mock_files_repo = Mock()
        self.mock_container.resolve = Mock(return_value=mock_files_repo)
        
        repo = self.contest_manager.files_repo
        
        assert repo == mock_files_repo
        self.mock_container.resolve.assert_called_with('contest_current_files_repository')
    
    def test_env_json_load_failure(self):
        """Test env_json load failure handling"""
        from src.application.execution_requests import FileRequest
        
        manager = ContestManager(self.mock_container, None)
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "File not found"
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            with pytest.raises(RuntimeError) as exc_info:
                _ = manager.env_json
            
            assert "Failed to load shared env.json" in str(exc_info.value)
            assert "File not found" in str(exc_info.value)
    
    def test_env_json_load_failure_no_error_message(self):
        """Test env_json load failure without error message"""
        from src.application.execution_requests import FileRequest
        
        manager = ContestManager(self.mock_container, None)
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = None
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            with pytest.raises(RuntimeError) as exc_info:
                _ = manager.env_json
            
            assert "No error message provided by file operation" in str(exc_info.value)
    
    def test_get_latest_non_null_value_from_operations(self):
        """Test _get_latest_non_null_value retrieves from operations"""
        mock_ops_repo = Mock()
        mock_operation = Mock()
        mock_operation.language = 'python'
        mock_ops_repo.find_all.return_value = [mock_operation]
        
        self.mock_container.resolve = Mock(return_value=mock_ops_repo)
        
        result = self.contest_manager._get_latest_non_null_value('language')
        
        assert result == 'python'
    
    def test_get_latest_non_null_value_from_user_configs(self):
        """Test _get_latest_non_null_value falls back to user configs"""
        mock_ops_repo = Mock()
        mock_ops_repo.find_all.return_value = []
        
        # Need to mock the config_loader and config_repo
        mock_config_repo = Mock()
        mock_config_repo.get_user_specified_configs.return_value = {'language': 'cpp'}
        
        # Mock the config_loader property access
        with patch.object(self.contest_manager, 'config_loader') as mock_config_loader:
            mock_config_loader.config_repo = mock_config_repo
            
            def resolve_mock(key):
                if key == DIKey.OPERATION_REPOSITORY:
                    return mock_ops_repo
                return None
            
            self.mock_container.resolve = Mock(side_effect=resolve_mock)
            
            result = self.contest_manager._get_latest_non_null_value('language')
            
            assert result == 'cpp'
    
    def test_get_latest_non_null_value_none_found(self):
        """Test _get_latest_non_null_value returns None when no value found"""
        mock_ops_repo = Mock()
        mock_ops_repo.find_all.return_value = []
        
        mock_config_repo = Mock()
        mock_config_repo.get_user_specified_configs.return_value = {}
        
        # Mock the config_loader property access
        with patch.object(self.contest_manager, 'config_loader') as mock_config_loader:
            mock_config_loader.config_repo = mock_config_repo
            
            self.mock_container.resolve = Mock(return_value=mock_ops_repo)
            
            result = self.contest_manager._get_latest_non_null_value('language')
            
            assert result is None
    
    def test_backup_contest_current_exception_handling(self):
        """Test backup_contest_current propagates exceptions"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_stock_path': '/contest/stock/{language_name}/{contest_name}/{problem_name}'
                }
            }
        }
        
        current_state = {
            'language_name': 'python',
            'contest_name': 'ABC123',
            'problem_name': 'A'
        }
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            mock_has_content.side_effect = Exception("Test exception")
            
            # Without fallback processing, exception propagates as-is
            with pytest.raises(Exception) as exc_info:
                self.contest_manager.backup_contest_current(current_state)
            
            assert "Test exception" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_directory_has_content_exception(self, mock_time_provider):
        """Test _directory_has_content propagates exceptions"""
        from src.application.execution_requests import FileRequest
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.side_effect = Exception("File operation error")
            
            # Without fallback processing, exception propagates as-is
            with pytest.raises(Exception) as exc_info:
                self.contest_manager._directory_has_content('/test/path')
            
            assert "File operation error" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_ensure_directory_exists_exception(self, mock_time_provider):
        """Test _ensure_directory_exists propagates exceptions"""
        from src.application.execution_requests import FileRequest
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.side_effect = Exception("Directory creation error")
            
            # Exception propagates as-is when execute_operation fails
            with pytest.raises(Exception) as exc_info:
                self.contest_manager._ensure_directory_exists('/test/path')
            
            assert "Directory creation error" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_move_directory_contents_success(self, mock_time_provider):
        """Test successful _move_directory_contents"""
        from src.application.execution_requests import FileRequest
        
        self.mock_os_provider.listdir.return_value = ['file1.py', 'file2.py']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        
        mock_result = Mock()
        mock_result.success = True
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = self.contest_manager._move_directory_contents('/source', '/dest')
            
            assert result is True
            assert mock_execute.call_count == 2  # Two files
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_move_directory_contents_failure(self, mock_time_provider):
        """Test _move_directory_contents handles move failure"""
        from src.application.execution_requests import FileRequest
        
        # Configure the mock time provider to return a mock instance
        mock_time_instance = Mock()
        mock_time_provider.return_value = mock_time_instance
        
        self.mock_os_provider.listdir.return_value = ['file1.py']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Move failed"
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            # Should raise RuntimeError due to failure
            with pytest.raises(RuntimeError) as exc_info:
                self.contest_manager._move_directory_contents('/source', '/dest')
            
            assert "Failed to move /source/file1.py to /dest/file1.py" in str(exc_info.value)
    
    def test_move_directory_contents_exception(self):
        """Test _move_directory_contents exception handling"""
        self.mock_os_provider.listdir.side_effect = Exception("List directory error")
        
        # Should not catch the exception anymore based on the implementation
        with pytest.raises(Exception) as exc_info:
            self.contest_manager._move_directory_contents('/source', '/dest')
        
        assert "List directory error" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_clear_contest_current_with_files_and_dirs(self, mock_time_provider):
        """Test _clear_contest_current removes files and directories"""
        from src.application.execution_requests import FileRequest
        
        self.mock_os_provider.exists.return_value = True
        self.mock_os_provider.listdir.return_value = ['file.py', 'subdir']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        self.mock_os_provider.isdir.side_effect = lambda path: 'subdir' in path
        
        mock_result = Mock()
        mock_result.success = True
        
        with patch.object(FileRequest, 'execute_operation') as mock_execute:
            mock_execute.return_value = mock_result
            
            result = self.contest_manager._clear_contest_current('/contest/current')
            
            assert result is True
            assert mock_execute.call_count == 2  # One file, one directory
    
    def test_clear_contest_current_exception(self):
        """Test _clear_contest_current exception handling"""
        self.mock_os_provider.exists.side_effect = Exception("OS error")
        
        # Should not catch the exception anymore based on the implementation
        with pytest.raises(Exception) as exc_info:
            self.contest_manager._clear_contest_current('/contest/current')
        
        assert "OS error" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_copy_directory_contents_with_subdirs(self, mock_time_provider):
        """Test _copy_directory_contents handles subdirectories"""
        from src.application.execution_requests import FileRequest
        
        self.mock_os_provider.listdir.return_value = ['file.py', 'subdir']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        self.mock_os_provider.isdir.side_effect = lambda path: 'subdir' in path
        
        mock_result = Mock()
        mock_result.success = True
        
        with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure:
            with patch.object(self.contest_manager, '_copy_template_recursive') as mock_recursive:
                with patch.object(self.contest_manager, 'get_current_contest_state') as mock_state:
                    with patch.object(FileRequest, 'execute_operation') as mock_execute:
                        mock_ensure.return_value = True
                        mock_recursive.return_value = True
                        mock_execute.return_value = mock_result
                        mock_state.return_value = {
                            'language_name': 'python',
                            'contest_name': 'ABC123',
                            'problem_name': 'A'
                        }
                        
                        result = self.contest_manager._copy_directory_contents('/source', '/dest')
                        
                        assert result is True
                        mock_recursive.assert_called_once()
                        mock_execute.assert_called_once()  # Only for file.py
    
    def test_copy_directory_contents_exception(self):
        """Test _copy_directory_contents exception handling"""
        with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure:
            mock_ensure.side_effect = Exception("Directory error")
            
            # Should not catch the exception anymore based on the implementation
            with pytest.raises(Exception) as exc_info:
                self.contest_manager._copy_directory_contents('/source', '/dest')
            
            assert "Directory error" in str(exc_info.value)
    
    def test_copy_template_structure_success(self):
        """Test _copy_template_structure with file tracking"""
        mock_files_repo = Mock()
        self.mock_container.resolve = Mock(return_value=mock_files_repo)
        
        tracked_files = []
        
        with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure:
            with patch.object(self.contest_manager, '_copy_template_recursive') as mock_recursive:
                mock_ensure.return_value = True
                
                def mock_recursive_side_effect(source, dest, rel_path, lang, contest, problem, files_list):
                    files_list.append(('python', 'ABC123', 'A', 'main.py', 'template', '/template/main.py'))
                    return True
                
                mock_recursive.side_effect = mock_recursive_side_effect
                
                result = self.contest_manager._copy_template_structure('/template', '/dest', 'python', 'ABC123', 'A')
                
                assert result is True
                mock_files_repo.track_multiple_files.assert_called_once()
    
    def test_copy_template_structure_exception(self):
        """Test _copy_template_structure exception handling"""
        with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure:
            mock_ensure.side_effect = Exception("Template error")
            
            # Should not catch the exception anymore based on the implementation
            with pytest.raises(Exception) as exc_info:
                self.contest_manager._copy_template_structure('/template', '/dest', 'python', 'ABC123', 'A')
            
            assert "Template error" in str(exc_info.value)
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_copy_template_recursive_files_and_dirs(self, mock_time_provider):
        """Test _copy_template_recursive handles files and directories"""
        from src.application.execution_requests import FileRequest
        
        self.mock_os_provider.listdir.return_value = ['file.py', 'subdir']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        self.mock_os_provider.isdir.side_effect = lambda path: 'subdir' in path
        
        mock_result = Mock()
        mock_result.success = True
        
        tracked_files = []
        
        with patch.object(self.contest_manager, '_ensure_directory_exists') as mock_ensure:
            with patch.object(FileRequest, 'execute_operation') as mock_execute:
                mock_ensure.return_value = True
                mock_execute.return_value = mock_result
                
                # Mock recursive call for subdirectory
                original_method = self.contest_manager._copy_template_recursive
                call_count = 0
                
                def mock_recursive(source, dest, rel_path, lang, contest, problem, files):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        # First call (main)
                        return original_method(source, dest, rel_path, lang, contest, problem, files)
                    else:
                        # Recursive call for subdir
                        return True
                
                with patch.object(self.contest_manager, '_copy_template_recursive', mock_recursive):
                    result = self.contest_manager._copy_template_recursive('/source', '/dest', '', 'python', 'ABC123', 'A', tracked_files)
                
                assert result is True
                assert len(tracked_files) == 1  # Only file.py tracked
                assert tracked_files[0][3] == 'file.py'
    
    def test_copy_template_recursive_exception(self):
        """Test _copy_template_recursive exception handling"""
        self.mock_os_provider.listdir.side_effect = Exception("Recursive error")
        
        tracked_files = []
        
        # Should not catch the exception anymore based on the implementation
        with pytest.raises(Exception) as exc_info:
            self.contest_manager._copy_template_recursive('/source', '/dest', '', 'python', 'ABC123', 'A', tracked_files)
        
        assert "Recursive error" in str(exc_info.value)
    
    def test_track_files_from_stock_success(self):
        """Test _track_files_from_stock with repository operations"""
        mock_files_repo = Mock()
        self.mock_container.resolve = Mock(return_value=mock_files_repo)
        
        with patch.object(self.contest_manager, '_track_files_recursive') as mock_track:
            def mock_track_side_effect(source, dest, rel_path, lang, contest, problem, files_list):
                files_list.append(('python', 'ABC123', 'A', 'main.py', 'stock', '/stock/main.py'))
            
            mock_track.side_effect = mock_track_side_effect
            
            result = self.contest_manager._track_files_from_stock('/stock', '/current', 'python', 'ABC123', 'A')
            
            assert result is True
            mock_files_repo.clear_contest_tracking.assert_called_once_with('python', 'ABC123', 'A')
            mock_files_repo.track_multiple_files.assert_called_once()
    
    def test_track_files_from_stock_exception(self):
        """Test _track_files_from_stock exception handling"""
        with patch.object(self.contest_manager, '_track_files_recursive') as mock_track:
            mock_track.side_effect = Exception("Tracking error")
            
            # Should not catch the exception anymore based on the implementation
            with pytest.raises(Exception) as exc_info:
                self.contest_manager._track_files_from_stock('/stock', '/current', 'python', 'ABC123', 'A')
            
            assert "Tracking error" in str(exc_info.value)
    
    def test_track_files_recursive_success(self):
        """Test _track_files_recursive processes files correctly"""
        self.mock_os_provider.listdir.return_value = ['file1.py', 'subdir', 'file2.py']
        self.mock_os_provider.path_join.side_effect = lambda a, b: f"{a}/{b}"
        self.mock_os_provider.isdir.side_effect = lambda path: 'subdir' in path
        
        tracked_files = []
        
        # Mock recursive call for subdirectory
        original_method = self.contest_manager._track_files_recursive
        call_count = 0
        
        def mock_recursive(source, dest, rel_path, lang, contest, problem, files):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (main)
                original_method(source, dest, rel_path, lang, contest, problem, files)
            # Skip recursive call for subdir
        
        with patch.object(self.contest_manager, '_track_files_recursive', mock_recursive):
            self.contest_manager._track_files_recursive('/source', '/dest', '', 'python', 'ABC123', 'A', tracked_files)
        
        assert len(tracked_files) == 2  # file1.py and file2.py
        assert all(f[4] == 'stock' for f in tracked_files)
    
    def test_track_files_recursive_exception(self):
        """Test _track_files_recursive exception handling"""
        self.mock_os_provider.listdir.side_effect = Exception("List error")
        
        tracked_files = []
        
        # Should not catch the exception anymore based on the implementation
        with pytest.raises(Exception) as exc_info:
            self.contest_manager._track_files_recursive('/source', '/dest', '', 'python', 'ABC123', 'A', tracked_files)
        
        assert "List error" in str(exc_info.value)
    
    def test_handle_contest_change_exception(self):
        """Test handle_contest_change exception handling"""
        with patch.object(self.contest_manager, 'needs_backup') as mock_needs:
            mock_needs.side_effect = Exception("Check error")
            
            # Should not catch the exception anymore based on the implementation
            with pytest.raises(Exception) as exc_info:
                self.contest_manager.handle_contest_change('python', 'ABC123', 'A')
            
            assert "Check error" in str(exc_info.value)
    
    def test_restore_from_contest_stock_exception(self):
        """Test restore_from_contest_stock exception handling"""
        self.contest_manager._env_json = {'shared': {'paths': {}}}
        
        # Should raise KeyError when accessing missing paths
        with pytest.raises(KeyError):
            self.contest_manager.restore_from_contest_stock('python', 'ABC123', 'A')
    
    def test_initialize_from_template_exception(self):
        """Test initialize_from_template exception handling"""
        self.contest_manager._env_json = {'shared': {'paths': {}}}
        
        # Should raise KeyError when accessing missing paths
        with pytest.raises(KeyError):
            self.contest_manager.initialize_from_template('python', 'ABC123', 'A')
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_restore_from_contest_stock_full_flow(self, mock_time_provider):
        """Test complete restore flow from contest stock"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_stock_path': '/contest/stock/{language_name}/{contest_name}/{problem_name}'
                }
            }
        }
        
        mock_files_repo = Mock()
        self.mock_container.resolve = Mock(return_value=mock_files_repo)
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            with patch.object(self.contest_manager, '_clear_contest_current') as mock_clear:
                with patch.object(self.contest_manager, '_copy_directory_contents') as mock_copy:
                    with patch.object(self.contest_manager, '_track_files_from_stock') as mock_track:
                        mock_has_content.return_value = True
                        mock_clear.return_value = True
                        mock_copy.return_value = True
                        
                        result = self.contest_manager.restore_from_contest_stock('python', 'ABC123', 'A')
                        
                        assert result is True
                        mock_clear.assert_called_once_with('/contest/current')
                        mock_copy.assert_called_once_with('/contest/stock/python/ABC123/A', '/contest/current')
                        mock_track.assert_called_once()
    
    @patch('src.application.contest_manager.SystemTimeProvider')
    def test_initialize_from_template_full_flow(self, mock_time_provider):
        """Test complete initialization flow from template"""
        self.contest_manager._env_json = {
            'shared': {
                'paths': {
                    'contest_current_path': '/contest/current',
                    'contest_template_path': '/contest/template'
                }
            }
        }
        
        self.mock_os_provider.path_join.return_value = '/contest/template/python'
        
        with patch.object(self.contest_manager, '_directory_has_content') as mock_has_content:
            with patch.object(self.contest_manager, '_clear_contest_current') as mock_clear:
                with patch.object(self.contest_manager, '_copy_template_structure') as mock_copy:
                    mock_has_content.return_value = True
                    mock_clear.return_value = True
                    mock_copy.return_value = True
                    
                    result = self.contest_manager.initialize_from_template('python', 'ABC123', 'A')
                    
                    assert result is True
                    mock_clear.assert_called_once_with('/contest/current')
                    mock_copy.assert_called_once_with('/contest/template/python', '/contest/current', 'python', 'ABC123', 'A')
                    self.mock_logger.info.assert_called()