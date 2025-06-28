"""Tests for Python utilities module"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import io
from pathlib import Path

from src.utils.python_utils import PythonUtils
from src.operations.python_exceptions import (
    PythonConfigError,
    PythonInterpreterError,
)


class TestPythonUtils:
    """Test suite for PythonUtils class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_config_provider = Mock()
        self.python_utils = PythonUtils(self.mock_config_provider)
    
    def test_is_script_file_with_existing_file(self):
        """Test is_script_file returns True for existing file"""
        with patch('pathlib.Path.is_file') as mock_is_file:
            mock_is_file.return_value = True
            
            result = self.python_utils.is_script_file(['test.py'])
            
            assert result is True
            mock_is_file.assert_called_once()
    
    def test_is_script_file_with_non_existing_file(self):
        """Test is_script_file returns False for non-existing file"""
        with patch('pathlib.Path.is_file') as mock_is_file:
            mock_is_file.return_value = False
            
            result = self.python_utils.is_script_file(['nonexistent.py'])
            
            assert result is False
    
    def test_is_script_file_with_multiple_arguments(self):
        """Test is_script_file returns False for multiple arguments"""
        result = self.python_utils.is_script_file(['arg1', 'arg2'])
        
        assert result is False
    
    def test_is_script_file_with_empty_list(self):
        """Test is_script_file returns False for empty list"""
        result = self.python_utils.is_script_file([])
        
        assert result is False
    
    @patch('subprocess.run')
    def test_run_script_file_success(self, mock_run):
        """Test successful script file execution"""
        mock_result = Mock()
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock the interpreter getter
        self.python_utils._python_interpreter = '/usr/bin/python3'
        
        stdout, stderr, returncode = self.python_utils.run_script_file('test.py', '/tmp')
        
        assert stdout == "Hello, World!"
        assert stderr == ""
        assert returncode == 0
        mock_run.assert_called_once_with(
            ['/usr/bin/python3', 'test.py'],
            capture_output=True,
            text=True,
            cwd='/tmp',
            check=False
        )
    
    @patch('subprocess.run')
    def test_run_script_file_with_error(self, mock_run):
        """Test script file execution with error"""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "Error: File not found"
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        self.python_utils._python_interpreter = '/usr/bin/python3'
        
        stdout, stderr, returncode = self.python_utils.run_script_file('missing.py', None)
        
        assert stdout == ""
        assert stderr == "Error: File not found"
        assert returncode == 1
    
    def test_run_code_string_success(self):
        """Test successful code string execution"""
        code = "print('Hello, World!')"
        
        stdout, stderr, returncode = self.python_utils.run_code_string(code, None)
        
        assert stdout == "Hello, World!\n"
        assert stderr == ""
        assert returncode == 0
    
    def test_run_code_string_with_syntax_error(self):
        """Test code string execution with syntax error"""
        code = "print('Hello World"  # Missing closing quote
        
        # Mock config_manager for error code lookup
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        stdout, stderr, returncode = self.python_utils.run_code_string(code, None)
        
        assert stdout == ""
        assert "SyntaxError" in stderr
        assert returncode == 2  # Syntax error code
    
    def test_run_code_string_with_runtime_error(self):
        """Test code string execution with runtime error"""
        code = "x = 1 / 0"  # Division by zero
        
        # Mock config_manager for error code lookup
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        stdout, stderr, returncode = self.python_utils.run_code_string(code, None)
        
        assert stdout == ""
        assert "ZeroDivisionError" in stderr
        assert returncode == 1  # General error code
    
    def test_run_code_string_with_import_error(self):
        """Test code string execution with import error"""
        code = "import nonexistent_module"
        
        # Mock config_manager for error code lookup
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        stdout, stderr, returncode = self.python_utils.run_code_string(code, None)
        
        assert stdout == ""
        assert "ModuleNotFoundError" in stderr or "ImportError" in stderr
        assert returncode == 3  # Import error code
    
    def test_get_python_interpreter_cached(self):
        """Test _get_python_interpreter returns cached value"""
        self.python_utils._python_interpreter = '/cached/python'
        
        result = self.python_utils._get_python_interpreter()
        
        assert result == '/cached/python'
    
    def test_get_python_interpreter_from_config(self):
        """Test _get_python_interpreter gets from config"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.side_effect = [
            '/usr/bin/python3',  # default interpreter
            ['/usr/bin/python', '/usr/local/bin/python3']  # alternatives
        ]
        
        with patch.object(self.python_utils, '_test_interpreter') as mock_test:
            mock_test.return_value = True
            
            result = self.python_utils._get_python_interpreter()
            
            assert result == '/usr/bin/python3'
            assert self.python_utils._python_interpreter == '/usr/bin/python3'
            mock_test.assert_called_once_with('/usr/bin/python3')
    
    def test_get_python_interpreter_fallback_to_alternative(self):
        """Test _get_python_interpreter falls back to alternative"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.side_effect = [
            '/usr/bin/python3',  # default interpreter
            ['/usr/bin/python', '/usr/local/bin/python3']  # alternatives
        ]
        
        with patch.object(self.python_utils, '_test_interpreter') as mock_test:
            # First interpreter fails, second succeeds
            mock_test.side_effect = [False, True, False]
            
            result = self.python_utils._get_python_interpreter()
            
            assert result == '/usr/bin/python'
            assert mock_test.call_count == 2
    
    def test_get_python_interpreter_no_working_interpreter(self):
        """Test _get_python_interpreter raises when no interpreter works"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.side_effect = [
            '/usr/bin/python3',  # default interpreter
            ['/usr/bin/python']  # alternatives
        ]
        
        with patch.object(self.python_utils, '_test_interpreter') as mock_test:
            mock_test.return_value = False
            
            with pytest.raises(PythonInterpreterError) as exc_info:
                self.python_utils._get_python_interpreter()
            
            assert "No working Python interpreter found" in str(exc_info.value)
    
    def test_get_python_interpreter_config_error(self):
        """Test _get_python_interpreter handles config error"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.side_effect = KeyError("Not found")
        
        with pytest.raises(PythonConfigError) as exc_info:
            self.python_utils._get_python_interpreter()
        
        assert "No default Python interpreter configured" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_test_interpreter_success(self, mock_run):
        """Test _test_interpreter with working interpreter"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.python_utils._test_interpreter('/usr/bin/python3')
        
        assert result is True
        mock_run.assert_called_once_with(
            ['/usr/bin/python3', '--version'],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
    
    @patch('subprocess.run')
    def test_test_interpreter_failure(self, mock_run):
        """Test _test_interpreter with non-working interpreter"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        result = self.python_utils._test_interpreter('/usr/bin/python3')
        
        assert result is False
    
    @patch('subprocess.run')
    def test_test_interpreter_timeout(self, mock_run):
        """Test _test_interpreter with timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired(['python3', '--version'], 5)
        
        with pytest.raises(PythonConfigError) as exc_info:
            self.python_utils._test_interpreter('/usr/bin/python3')
        
        assert "Failed to validate Python interpreter" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_test_interpreter_file_not_found(self, mock_run):
        """Test _test_interpreter with missing interpreter"""
        mock_run.side_effect = FileNotFoundError("python3 not found")
        
        with pytest.raises(PythonConfigError) as exc_info:
            self.python_utils._test_interpreter('/usr/bin/python3')
        
        assert "Failed to validate Python interpreter" in str(exc_info.value)
    
    def test_get_error_return_code_syntax_error(self):
        """Test _get_error_return_code for SyntaxError"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        result = self.python_utils._get_error_return_code(SyntaxError())
        
        assert result == 2
    
    def test_get_error_return_code_import_error(self):
        """Test _get_error_return_code for ImportError"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        result = self.python_utils._get_error_return_code(ImportError())
        
        assert result == 3
    
    def test_get_error_return_code_keyboard_interrupt(self):
        """Test _get_error_return_code for KeyboardInterrupt"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        result = self.python_utils._get_error_return_code(KeyboardInterrupt())
        
        assert result == 130  # 128 + 2 (SIGINT)
    
    def test_get_error_return_code_general_error(self):
        """Test _get_error_return_code for general Exception"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.return_value = {}
        
        result = self.python_utils._get_error_return_code(Exception("General error"))
        
        assert result == 1
    
    def test_get_error_return_code_config_error(self):
        """Test _get_error_return_code with config error"""
        self.python_utils.config_manager = Mock()
        self.python_utils.config_manager.resolve_config.side_effect = KeyError("Not found")
        
        with pytest.raises(PythonConfigError) as exc_info:
            self.python_utils._get_error_return_code(Exception())
        
        assert "Error code configuration not found" in str(exc_info.value)