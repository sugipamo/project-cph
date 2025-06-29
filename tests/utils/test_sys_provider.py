"""Tests for sys_provider module"""
from unittest.mock import Mock, patch
import pytest
from src.utils.sys_provider import SystemSysProvider, MockSysProvider


class TestSystemSysProvider:
    """Tests for SystemSysProvider"""
    
    def test_init_requires_logger(self):
        """Test that logger is required"""
        with pytest.raises(ValueError, match="logger parameter is required"):
            SystemSysProvider(None)
    
    def test_get_argv(self):
        """Test get_argv returns sys.argv"""
        logger = Mock()
        provider = SystemSysProvider(logger)
        
        with patch('sys.argv', ['test.py', 'arg1', 'arg2']):
            assert provider.get_argv() == ['test.py', 'arg1', 'arg2']
    
    def test_exit(self):
        """Test exit calls sys.exit"""
        logger = Mock()
        provider = SystemSysProvider(logger)
        
        with patch('sys.exit') as mock_exit:
            provider.exit(0)
            mock_exit.assert_called_once_with(0)
            
        with patch('sys.exit') as mock_exit:
            provider.exit(1)
            mock_exit.assert_called_once_with(1)
    
    def test_get_platform(self):
        """Test get_platform returns sys.platform"""
        logger = Mock()
        provider = SystemSysProvider(logger)
        
        with patch('sys.platform', 'linux'):
            assert provider.get_platform() == 'linux'
            
        with patch('sys.platform', 'darwin'):
            assert provider.get_platform() == 'darwin'
    
    def test_get_version_info(self):
        """Test get_version_info returns sys.version_info"""
        logger = Mock()
        provider = SystemSysProvider(logger)
        
        import sys
        assert provider.get_version_info() == sys.version_info
    
    def test_print_stdout(self):
        """Test print_stdout calls logger.info"""
        logger = Mock()
        provider = SystemSysProvider(logger)
        
        provider.print_stdout("test message")
        logger.info.assert_called_once_with("test message")
        
        provider.print_stdout("another message")
        assert logger.info.call_count == 2
        logger.info.assert_called_with("another message")


class TestMockSysProvider:
    """Tests for MockSysProvider"""
    
    def test_init_requires_argv(self):
        """Test that argv is required"""
        with pytest.raises(ValueError, match="argv parameter is required"):
            MockSysProvider(None, "linux")
    
    def test_get_argv(self):
        """Test get_argv returns configured argv"""
        provider = MockSysProvider(['test.py', 'arg1'], "linux")
        assert provider.get_argv() == ['test.py', 'arg1']
    
    def test_set_argv(self):
        """Test set_argv updates argv"""
        provider = MockSysProvider(['test.py'], "linux")
        assert provider.get_argv() == ['test.py']
        
        provider.set_argv(['new.py', 'arg1', 'arg2'])
        assert provider.get_argv() == ['new.py', 'arg1', 'arg2']
    
    def test_exit(self):
        """Test exit stores exit code"""
        provider = MockSysProvider(['test.py'], "linux")
        
        assert provider.get_last_exit_code() is None
        
        provider.exit(0)
        assert provider.get_last_exit_code() == 0
        
        provider.exit(1)
        assert provider.get_last_exit_code() == 1
    
    def test_exit_callback(self):
        """Test exit callback is called"""
        provider = MockSysProvider(['test.py'], "linux")
        
        callback_calls = []
        def callback(code):
            callback_calls.append(code)
        
        provider.set_exit_callback(callback)
        
        provider.exit(0)
        assert callback_calls == [0]
        
        provider.exit(42)
        assert callback_calls == [0, 42]
    
    def test_get_platform(self):
        """Test get_platform returns configured platform"""
        provider = MockSysProvider(['test.py'], "linux")
        assert provider.get_platform() == "linux"
        
        provider = MockSysProvider(['test.py'], "darwin")
        assert provider.get_platform() == "darwin"
    
    def test_get_version_info(self):
        """Test get_version_info returns real sys.version_info"""
        provider = MockSysProvider(['test.py'], "linux")
        
        import sys
        assert provider.get_version_info() == sys.version_info
    
    def test_print_stdout(self):
        """Test print_stdout stores messages"""
        provider = MockSysProvider(['test.py'], "linux")
        
        assert provider.get_stdout_messages() == []
        
        provider.print_stdout("message 1")
        assert provider.get_stdout_messages() == ["message 1"]
        
        provider.print_stdout("message 2")
        assert provider.get_stdout_messages() == ["message 1", "message 2"]
    
    def test_clear_stdout_messages(self):
        """Test clear_stdout_messages clears messages"""
        provider = MockSysProvider(['test.py'], "linux")
        
        provider.print_stdout("message 1")
        provider.print_stdout("message 2")
        assert len(provider.get_stdout_messages()) == 2
        
        provider.clear_stdout_messages()
        assert provider.get_stdout_messages() == []
    
    def test_get_stdout_messages_returns_copy(self):
        """Test get_stdout_messages returns a copy"""
        provider = MockSysProvider(['test.py'], "linux")
        
        provider.print_stdout("message")
        messages = provider.get_stdout_messages()
        messages.append("should not affect internal list")
        
        assert provider.get_stdout_messages() == ["message"]