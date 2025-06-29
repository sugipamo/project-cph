"""Tests for the ExecutionDriver class."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from typing import Any, Optional

from src.infrastructure.drivers.generic.execution_driver import ExecutionDriver


class TestExecutionDriver:
    """Test suite for ExecutionDriver."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        config_manager = Mock()
        config_manager.resolve_config.side_effect = lambda key: {
            "infrastructure_defaults.shell.cwd": None,
            "infrastructure_defaults.shell.env": {},
            "infrastructure_defaults.shell.inputdata": None,
            "infrastructure_defaults.shell.timeout": 30,
            "infrastructure_defaults.python.cwd": "."
        }.get(key)
        return config_manager

    @pytest.fixture
    def mock_file_driver(self):
        """Create a mock file driver."""
        return Mock()

    @pytest.fixture
    def mock_container(self):
        """Create a mock DI container."""
        return Mock()

    @pytest.fixture
    def driver(self, mock_config_manager, mock_file_driver, mock_container):
        """Create an ExecutionDriver instance."""
        driver = ExecutionDriver(mock_config_manager, mock_file_driver, mock_container)
        # Mock _get_default_value to return values from config_manager
        driver._get_default_value = mock_config_manager.resolve_config
        return driver

    def test_init(self, mock_config_manager, mock_file_driver, mock_container):
        """Test ExecutionDriver initialization."""
        driver = ExecutionDriver(mock_config_manager, mock_file_driver, mock_container)
        
        assert driver.config_manager == mock_config_manager
        assert driver.file_driver == mock_file_driver
        assert driver.python_utils is not None

    def test_validate_shell_request(self, driver):
        """Test validate method with shell request."""
        request = Mock()
        request.cmd = "echo test"
        
        assert driver.validate(request) is True

    def test_validate_python_request(self, driver):
        """Test validate method with Python request."""
        request = Mock()
        request.code_or_file = "print('test')"
        
        assert driver.validate(request) is True

    def test_validate_invalid_request(self, driver):
        """Test validate method with invalid request."""
        request = Mock(spec=[])  # Empty spec means no attributes
        
        assert driver.validate(request) is False

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_execute_shell_command_with_defaults(self, mock_shell_utils, driver):
        """Test execute_shell_command with default values."""
        mock_result = Mock()
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.execute_shell_command(
            cmd="echo test",
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )
        
        assert result == mock_result
        mock_shell_utils.run_subprocess.assert_called_once_with(
            cmd="echo test",
            cwd=".",
            env=None,
            inputdata="",
            timeout=None
        )

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_execute_shell_command_creates_cwd(self, mock_shell_utils, driver, mock_file_driver):
        """Test execute_shell_command creates working directory if needed."""
        mock_result = Mock()
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        # Mock Path.exists to return False
        with patch.object(Path, 'exists', return_value=False):
            result = driver.execute_shell_command(
                cmd="echo test",
                cwd="/tmp/test",
                env={"VAR": "value"},
                inputdata="input",
                timeout=30
            )
        
        assert result == mock_result
        mock_file_driver.makedirs.assert_called_once_with(Path("/tmp/test"), exist_ok=True)

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_execute_shell_command_list(self, mock_shell_utils, driver):
        """Test execute_shell_command with command as list."""
        mock_result = Mock()
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.execute_shell_command(
            cmd=["ls", "-la"],
            cwd="/tmp",
            env=None,
            inputdata=None,
            timeout=60
        )
        
        assert result == mock_result
        mock_shell_utils.run_subprocess.assert_called_once_with(
            cmd=["ls", "-la"],
            cwd="/tmp",
            env=None,
            inputdata="",
            timeout=60
        )

    def test_execute_command_shell_request(self, driver):
        """Test execute_command with shell request."""
        request = Mock()
        request.cmd = "echo test"
        request.cwd = "/tmp"
        request.env = {"VAR": "value"}
        request.inputdata = "input"
        request.timeout = 30
        
        with patch.object(driver, 'execute_shell_command') as mock_exec:
            mock_exec.return_value = "result"
            result = driver.execute_command(request)
        
        assert result == "result"
        mock_exec.assert_called_once_with(
            cmd="echo test",
            cwd="/tmp",
            env={"VAR": "value"},
            inputdata="input",
            timeout=30
        )

    def test_execute_command_shell_request_with_defaults(self, driver):
        """Test execute_command with shell request using default values."""
        request = Mock(spec=['cmd'])
        request.cmd = "echo test"
        # Only cmd attribute exists, so defaults should be used
        
        with patch.object(driver, 'execute_shell_command') as mock_exec:
            mock_exec.return_value = "result"
            result = driver.execute_command(request)
        
        assert result == "result"
        mock_exec.assert_called_once_with(
            cmd="echo test",
            cwd=None,
            env={},
            inputdata=None,
            timeout=30
        )

    def test_execute_command_python_script(self, driver):
        """Test execute_command with Python script request."""
        request = Mock(spec=['code_or_file', 'cwd'])
        request.code_or_file = ["test.py"]
        request.cwd = "/tmp"
        
        with patch.object(driver.python_utils, 'is_script_file', return_value=True):
            with patch.object(driver, 'run_python_script') as mock_run:
                mock_run.return_value = ("output", "", 0)
                result = driver.execute_command(request)
        
        assert result == ("output", "", 0)
        mock_run.assert_called_once_with("test.py", "/tmp")

    def test_execute_command_python_code(self, driver):
        """Test execute_command with Python code request."""
        request = Mock(spec=['code_or_file', 'cwd'])
        request.code_or_file = "print('hello')"
        request.cwd = "/tmp"
        
        with patch.object(driver.python_utils, 'is_script_file', return_value=False):
            with patch.object(driver, 'run_python_code') as mock_run:
                mock_run.return_value = ("hello\n", "", 0)
                result = driver.execute_command(request)
        
        assert result == ("hello\n", "", 0)
        mock_run.assert_called_once_with("print('hello')", "/tmp")

    def test_execute_command_python_code_list(self, driver):
        """Test execute_command with Python code as list."""
        request = Mock(spec=['code_or_file', 'cwd'])
        request.code_or_file = ["print('line1')", "print('line2')"]
        request.cwd = None  # Use default
        
        with patch.object(driver.python_utils, 'is_script_file', return_value=False):
            with patch.object(driver, 'run_python_code') as mock_run:
                mock_run.return_value = ("line1\nline2\n", "", 0)
                result = driver.execute_command(request)
        
        assert result == ("line1\nline2\n", "", 0)
        mock_run.assert_called_once_with("print('line1')\nprint('line2')", ".")

    def test_execute_command_invalid_request(self, driver):
        """Test execute_command with invalid request."""
        request = Mock(spec=[])
        # No cmd or code_or_file attribute
        
        with pytest.raises(ValueError, match="Invalid request type"):
            driver.execute_command(request)

    def test_run_python_code(self, driver):
        """Test run_python_code method."""
        with patch.object(driver.python_utils, 'run_code_string') as mock_run:
            mock_run.return_value = ("output", "", 0)
            result = driver.run_python_code("print('test')", "/tmp")
        
        assert result == ("output", "", 0)
        mock_run.assert_called_once_with("print('test')", "/tmp")

    def test_run_python_code_default_cwd(self, driver):
        """Test run_python_code with default cwd."""
        with patch.object(driver.python_utils, 'run_code_string') as mock_run:
            mock_run.return_value = ("output", "", 0)
            result = driver.run_python_code("print('test')", None)
        
        assert result == ("output", "", 0)
        mock_run.assert_called_once_with("print('test')", ".")

    def test_run_python_script(self, driver):
        """Test run_python_script method."""
        with patch.object(driver.python_utils, 'run_script_file') as mock_run:
            mock_run.return_value = ("output", "", 0)
            result = driver.run_python_script("test.py", "/tmp")
        
        assert result == ("output", "", 0)
        mock_run.assert_called_once_with("test.py", "/tmp")

    def test_run_python_script_default_cwd(self, driver):
        """Test run_python_script with default cwd."""
        with patch.object(driver.python_utils, 'run_script_file') as mock_run:
            mock_run.return_value = ("output", "", 0)
            result = driver.run_python_script("test.py", None)
        
        assert result == ("output", "", 0)
        mock_run.assert_called_once_with("test.py", ".")

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_chmod(self, mock_shell_utils, driver):
        """Test chmod method."""
        mock_result = Mock()
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.chmod("/tmp/file.txt", "+x", "/tmp")
        
        assert result == mock_result
        mock_shell_utils.run_subprocess.assert_called_once_with(
            cmd=["chmod", "+x", "/tmp/file.txt"],
            cwd="/tmp",
            env={},
            inputdata="",
            timeout=30
        )

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_which_found(self, mock_shell_utils, driver):
        """Test which method when command is found."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/bin/python3\n"
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.which("python3")
        
        assert result == "/usr/bin/python3"
        mock_shell_utils.run_subprocess.assert_called_once_with(
            cmd=["which", "python3"],
            cwd=".",
            env={},
            inputdata="",
            timeout=30
        )

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_which_not_found(self, mock_shell_utils, driver):
        """Test which method when command is not found."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.which("nonexistent")
        
        assert result is None

    @patch('src.infrastructure.drivers.generic.execution_driver.ShellUtils')
    def test_which_empty_stdout(self, mock_shell_utils, driver):
        """Test which method with empty stdout."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_shell_utils.run_subprocess.return_value = mock_result
        
        result = driver.which("command")
        
        assert result is None

    def test_is_command_available_true(self, driver):
        """Test is_command_available when command exists."""
        with patch.object(driver, 'which', return_value="/usr/bin/git"):
            assert driver.is_command_available("git") is True

    def test_is_command_available_false(self, driver):
        """Test is_command_available when command doesn't exist."""
        with patch.object(driver, 'which', return_value=None):
            assert driver.is_command_available("nonexistent") is False