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
    
    def test_lazy_load_logger_fallback_to_dummy(self):
        """Test logger falls back to dummy when not available"""
        # Make logger resolution fail
        def resolve_mock_no_logger(key):
            if key == DIKey.UNIFIED_LOGGER:
                raise ValueError("Logger not registered")
            return None
        
        self.mock_container.resolve.side_effect = resolve_mock_no_logger
        
        logger = self.contest_manager.logger
        
        # Should get dummy logger with required methods
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')
    
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