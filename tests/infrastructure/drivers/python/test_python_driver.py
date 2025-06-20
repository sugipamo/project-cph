"""Tests for Python driver implementation"""
import subprocess
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.configuration.config_manager import TypeSafeConfigNodeManager
from src.infrastructure.drivers.python.python_driver import LocalPythonDriver, PythonDriver


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    mock_config = Mock(spec=TypeSafeConfigNodeManager)

    # Mock the configuration values
    def mock_resolve_config(path, value_type):
        if path == ['python_config', 'interpreters', 'default']:
            return 'python3'
        if path == ['python_config', 'interpreters', 'alternatives']:
            return ['python3', 'python']
        if path == ['python_config', 'error_handling']:
            return {}
        raise KeyError(f"Configuration path not found: {path}")

    mock_config.resolve_config.side_effect = mock_resolve_config
    return mock_config


class TestPythonDriver:
    """Test suite for abstract Python driver"""

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError"""
        with pytest.raises(TypeError):
            # Can't instantiate abstract class directly
            PythonDriver()

    def test_execute_command_with_code_string(self, mock_config_manager):
        """Test executing command with code string request"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return "output", "error", 0

            def run_script_file(self, file_path, cwd=None):
                return "file_output", "file_error", 0

        driver = TestPythonDriver(mock_config_manager)

        # Mock request with code_or_file as string
        request = Mock()
        request.code_or_file = "print('hello')"

        result = driver.execute_command(request)
        assert result == ("output", "error", 0)

    def test_execute_command_with_code_list(self):
        """Test executing command with code list request"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return f"executed: {code}", "", 0

            def run_script_file(self, file_path, cwd=None):
                return "file_output", "file_error", 0

        driver = TestPythonDriver()

        # Mock request with code_or_file as list
        request = Mock()
        request.code_or_file = ["print('hello')", "print('world')"]

        result = driver.execute_command(request)
        assert result[0] == "executed: print('hello')\nprint('world')"

    @patch('src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file')
    def test_execute_command_with_script_file(self, mock_is_script_file):
        """Test executing command with script file request"""
        mock_is_script_file.return_value = True

        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return "code_output", "code_error", 0

            def run_script_file(self, file_path, cwd=None):
                return f"executed file: {file_path}", "", 0

        driver = TestPythonDriver()

        # Mock request with script file
        request = Mock()
        request.code_or_file = ["script.py"]

        result = driver.execute_command(request)
        assert result[0] == "executed file: script.py"

    def test_execute_command_with_cwd(self):
        """Test executing command with working directory"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return f"code in {cwd}", "", 0

            def run_script_file(self, file_path, cwd=None):
                return f"file in {cwd}", "", 0

        driver = TestPythonDriver()

        # Mock request with cwd
        request = Mock()
        request.code_or_file = "print('test')"
        request.cwd = "/test/dir"

        result = driver.execute_command(request)
        assert result[0] == "code in /test/dir"

    def test_execute_command_without_cwd(self):
        """Test executing command without working directory"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return f"code in {cwd}", "", 0

            def run_script_file(self, file_path, cwd=None):
                return f"file in {cwd}", "", 0

        driver = TestPythonDriver()

        # Mock request without cwd attribute
        request = Mock()
        request.code_or_file = "print('test')"
        del request.cwd  # Remove cwd attribute

        result = driver.execute_command(request)
        assert result[0] == "code in None"

    def test_execute_command_invalid_request(self):
        """Test executing command with invalid request"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return "output", "error", 0

            def run_script_file(self, file_path, cwd=None):
                return "file_output", "file_error", 0

        driver = TestPythonDriver()

        # Mock invalid request without code_or_file
        request = Mock()
        del request.code_or_file

        with pytest.raises(ValueError, match="Invalid request type for PythonDriver"):
            driver.execute_command(request)

    def test_validate_valid_request(self):
        """Test validating valid request"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return "output", "error", 0

            def run_script_file(self, file_path, cwd=None):
                return "file_output", "file_error", 0

        driver = TestPythonDriver()

        # Mock valid request
        request = Mock()
        request.code_or_file = "print('test')"

        assert driver.validate(request) is True

    def test_validate_invalid_request(self):
        """Test validating invalid request"""
        class TestPythonDriver(PythonDriver):
            def run_code_string(self, code, cwd=None):
                return "output", "error", 0

            def run_script_file(self, file_path, cwd=None):
                return "file_output", "file_error", 0

        driver = TestPythonDriver()

        # Mock invalid request
        request = Mock()
        del request.code_or_file

        assert driver.validate(request) is False


class TestLocalPythonDriver:
    """Test suite for local Python driver implementation"""

    @pytest.fixture
    def driver(self):
        """Create LocalPythonDriver instance for testing"""
        return LocalPythonDriver()

    @patch('subprocess.run')
    def test_run_code_string_success(self, mock_run, driver):
        """Test successful code string execution"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "Hello World"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        stdout, stderr, returncode = driver.run_code_string("print('Hello World')")

        assert stdout == "Hello World"
        assert stderr == ""
        assert returncode == 0

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            [sys.executable, '-c', "print('Hello World')"],
            cwd=None,
            capture_output=True,
            text=True,
            check=False
        )

    @patch('subprocess.run')
    def test_run_code_string_with_error(self, mock_run, driver):
        """Test code string execution with error"""
        # Mock subprocess result with error
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "NameError: name 'undefined_var' is not defined"
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        stdout, stderr, returncode = driver.run_code_string("print(undefined_var)")

        assert stdout == ""
        assert "NameError" in stderr
        assert returncode == 1

    @patch('subprocess.run')
    def test_run_code_string_with_cwd(self, mock_run, driver):
        """Test code string execution with working directory"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        driver.run_code_string("import os; print(os.getcwd())", cwd="/test/dir")

        # Verify cwd was passed correctly
        mock_run.assert_called_once_with(
            [sys.executable, '-c', "import os; print(os.getcwd())"],
            cwd="/test/dir",
            capture_output=True,
            text=True,
            check=False
        )

    @patch('subprocess.run')
    def test_run_script_file_success(self, mock_run, driver):
        """Test successful script file execution"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "Script executed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        stdout, stderr, returncode = driver.run_script_file("/path/to/script.py")

        assert stdout == "Script executed"
        assert stderr == ""
        assert returncode == 0

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once_with(
            [sys.executable, "/path/to/script.py"],
            cwd=None,
            capture_output=True,
            text=True,
            check=False
        )

    @patch('subprocess.run')
    def test_run_script_file_with_error(self, mock_run, driver):
        """Test script file execution with error"""
        # Mock subprocess result with error
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "FileNotFoundError: [Errno 2] No such file or directory"
        mock_result.returncode = 2
        mock_run.return_value = mock_result

        stdout, stderr, returncode = driver.run_script_file("/nonexistent/script.py")

        assert stdout == ""
        assert "FileNotFoundError" in stderr
        assert returncode == 2

    @patch('subprocess.run')
    def test_run_script_file_with_cwd(self, mock_run, driver):
        """Test script file execution with working directory"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        driver.run_script_file("script.py", cwd="/script/dir")

        # Verify cwd was passed correctly
        mock_run.assert_called_once_with(
            [sys.executable, "script.py"],
            cwd="/script/dir",
            capture_output=True,
            text=True,
            check=False
        )

    def test_inheritance_from_python_driver(self, driver):
        """Test that LocalPythonDriver properly inherits from PythonDriver"""
        assert isinstance(driver, PythonDriver)
        assert hasattr(driver, 'run_code_string')
        assert hasattr(driver, 'run_script_file')
        assert hasattr(driver, 'execute_command')
        assert hasattr(driver, 'validate')

    @patch('subprocess.run')
    def test_integration_execute_command_code_string(self, mock_run, driver):
        """Test integration of execute_command with code string"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "Integration test"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Mock request
        request = Mock()
        request.code_or_file = "print('Integration test')"

        result = driver.execute_command(request)

        assert result == ("Integration test", "", 0)

    @patch('subprocess.run')
    @patch('src.infrastructure.drivers.python.utils.python_utils.PythonUtils.is_script_file')
    def test_integration_execute_command_script_file(self, mock_is_script_file, mock_run, driver):
        """Test integration of execute_command with script file"""
        mock_is_script_file.return_value = True

        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "File execution"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Mock request
        request = Mock()
        request.code_or_file = ["test.py"]

        result = driver.execute_command(request)

        assert result == ("File execution", "", 0)

    @patch('subprocess.run')
    def test_subprocess_exception_handling(self, mock_run, driver):
        """Test handling of subprocess exceptions"""
        # Mock subprocess.run to raise an exception
        mock_run.side_effect = subprocess.SubprocessError("Test exception")

        with pytest.raises(subprocess.SubprocessError):
            driver.run_code_string("print('test')")

    @patch('subprocess.run')
    def test_multiline_code_execution(self, mock_run, driver):
        """Test execution of multiline code"""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.stdout = "1\n2\n3\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        multiline_code = """
for i in range(1, 4):
    print(i)
"""

        stdout, stderr, returncode = driver.run_code_string(multiline_code)

        assert "1\n2\n3\n" in stdout
        assert returncode == 0

        # Verify the multiline code was passed correctly
        mock_run.assert_called_once_with(
            [sys.executable, '-c', multiline_code],
            cwd=None,
            capture_output=True,
            text=True,
            check=False
        )

    def test_sys_executable_usage(self, driver):
        """Test that sys.executable is used for Python execution"""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            driver.run_code_string("pass")

            # Verify sys.executable is used
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == sys.executable
