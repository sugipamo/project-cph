"""
Comprehensive tests for shell_driver module
"""
import unittest.mock
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
from src.infrastructure.drivers.shell.shell_driver import ShellDriver
from tests.base.base_test import BaseTest


class TestShellDriverInterface(BaseTest):
    """Test abstract ShellDriver interface"""


    def test_abstract_method_execute_shell_command_defined(self):
        """Test that execute_shell_command method is defined as abstract"""
        assert hasattr(ShellDriver, 'execute_shell_command')
        assert callable(ShellDriver.execute_shell_command)


class TestLocalShellDriver(BaseTest):
    """Test LocalShellDriver implementation"""

    def setup_test(self):
        """Setup test data"""
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        self.mock_file_driver = MockFileDriver()
        self.driver = LocalShellDriver(self.mock_file_driver)

        # Mock successful shell result
        self.mock_success_result = Mock()
        self.mock_success_result.stdout = "success output"
        self.mock_success_result.stderr = ""
        self.mock_success_result.returncode = 0

        # Mock failed shell result
        self.mock_failure_result = Mock()
        self.mock_failure_result.stdout = ""
        self.mock_failure_result.stderr = "error output"
        self.mock_failure_result.returncode = 1

    def test_driver_inheritance(self):
        """Test that LocalShellDriver properly inherits from ShellDriver"""
        assert isinstance(self.driver, ShellDriver)
        assert hasattr(self.driver, 'execute_shell_command')

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_basic_command(self, mock_run_subprocess):
        """Test running basic command"""
        mock_run_subprocess.return_value = self.mock_success_result

        result = self.driver.execute_shell_command(["echo", "hello"])

        assert result.stdout == "success output"
        assert result.returncode == 0
        mock_run_subprocess.assert_called_once_with(
            cmd=["echo", "hello"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_cwd(self, mock_run_subprocess):
        """Test running command with working directory"""
        mock_run_subprocess.return_value = self.mock_success_result

        result = self.driver.execute_shell_command(["ls"], cwd="/tmp")

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["ls"],
            cwd="/tmp",
            env=None,
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_environment(self, mock_run_subprocess):
        """Test running command with environment variables"""
        mock_run_subprocess.return_value = self.mock_success_result

        env_vars = {"TEST_VAR": "test_value", "PATH": "/usr/bin"}
        result = self.driver.execute_shell_command(["env"], env=env_vars)

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["env"],
            cwd=None,
            env=env_vars,
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_input_data(self, mock_run_subprocess):
        """Test running command with input data (stdin)"""
        mock_run_subprocess.return_value = self.mock_success_result

        input_text = "line1\\nline2\\nline3"
        result = self.driver.execute_shell_command(["cat"], inputdata=input_text)

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["cat"],
            cwd=None,
            env=None,
            inputdata=input_text,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_timeout(self, mock_run_subprocess):
        """Test running command with timeout"""
        mock_run_subprocess.return_value = self.mock_success_result

        result = self.driver.execute_shell_command(["sleep", "1"], timeout=5)

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["sleep", "1"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=5
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_all_parameters(self, mock_run_subprocess):
        """Test running command with all parameters"""
        mock_run_subprocess.return_value = self.mock_success_result

        env_vars = {"VAR1": "value1"}
        input_data = "test input"

        result = self.driver.execute_shell_command(
            cmd=["grep", "pattern"],
            cwd="/home/user",
            env=env_vars,
            inputdata=input_data,
            timeout=10
        )

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["grep", "pattern"],
            cwd="/home/user",
            env=env_vars,
            inputdata=input_data,
            timeout=10
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_command_failure(self, mock_run_subprocess):
        """Test handling of command execution failure"""
        mock_run_subprocess.return_value = self.mock_failure_result

        result = self.driver.execute_shell_command(["false"])

        assert result.stdout == ""
        assert result.stderr == "error output"
        assert result.returncode == 1
        mock_run_subprocess.assert_called_once()


    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_empty_command(self, mock_run_subprocess):
        """Test running empty command"""
        mock_run_subprocess.return_value = self.mock_success_result

        result = self.driver.execute_shell_command([])

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=[],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_complex_command(self, mock_run_subprocess):
        """Test running complex command with multiple arguments"""
        mock_run_subprocess.return_value = self.mock_success_result

        complex_cmd = ["find", "/tmp", "-name", "*.txt", "-type", "f", "-exec", "ls", "-l", "{}", ";"]
        result = self.driver.execute_shell_command(complex_cmd)

        assert result.stdout == "success output"
        mock_run_subprocess.assert_called_once_with(
            cmd=complex_cmd,
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )


class TestLocalShellDriverIntegration(BaseTest):
    """Integration-style tests for LocalShellDriver"""

    def setup_test(self):
        """Setup test data"""
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        self.mock_file_driver = MockFileDriver()
        self.driver = LocalShellDriver(self.mock_file_driver)

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_multiple_sequential_commands(self, mock_run_subprocess):
        """Test running multiple commands in sequence"""
        # Setup different return values for each call
        results = [
            Mock(stdout="result1", stderr="", returncode=0),
            Mock(stdout="result2", stderr="", returncode=0),
            Mock(stdout="result3", stderr="", returncode=0)
        ]
        mock_run_subprocess.side_effect = results

        commands = [
            ["echo", "first"],
            ["echo", "second"],
            ["echo", "third"]
        ]

        actual_results = []
        for cmd in commands:
            result = self.driver.execute_shell_command(cmd)
            actual_results.append(result.stdout)

        assert actual_results == ["result1", "result2", "result3"]
        assert mock_run_subprocess.call_count == 3

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_command_with_piped_input(self, mock_run_subprocess):
        """Test command that processes piped input"""
        mock_run_subprocess.return_value = Mock(
            stdout="filtered output",
            stderr="",
            returncode=0
        )

        input_data = "line1\\nline2\\nline3\\n"
        result = self.driver.execute_shell_command(["grep", "line2"], inputdata=input_data)

        assert result.stdout == "filtered output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["grep", "line2"],
            cwd=None,
            env=None,
            inputdata=input_data,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_command_with_large_environment(self, mock_run_subprocess):
        """Test command with large environment variable set"""
        mock_run_subprocess.return_value = Mock(
            stdout="env output",
            stderr="",
            returncode=0
        )

        # Create large environment
        large_env = {f"VAR_{i}": f"value_{i}" for i in range(100)}
        result = self.driver.execute_shell_command(["env"], env=large_env)

        assert result.stdout == "env output"
        call_args = mock_run_subprocess.call_args
        assert call_args[1]['env'] == large_env


class TestLocalShellDriverEdgeCases(BaseTest):
    """Test edge cases and boundary conditions"""

    def setup_test(self):
        """Setup test data"""
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        self.mock_file_driver = MockFileDriver()
        self.driver = LocalShellDriver(self.mock_file_driver)

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_none_parameters(self, mock_run_subprocess):
        """Test running with explicitly None parameters"""
        mock_run_subprocess.return_value = Mock(
            stdout="output",
            stderr="",
            returncode=0
        )

        result = self.driver.execute_shell_command(
            cmd=["echo", "test"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )

        assert result.stdout == "output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["echo", "test"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_zero_timeout(self, mock_run_subprocess):
        """Test running with zero timeout"""
        mock_run_subprocess.return_value = Mock(
            stdout="quick output",
            stderr="",
            returncode=0
        )

        result = self.driver.execute_shell_command(["echo", "fast"], timeout=0)

        assert result.stdout == "quick output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["echo", "fast"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=0
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_empty_environment(self, mock_run_subprocess):
        """Test running with empty environment dictionary"""
        mock_run_subprocess.return_value = Mock(
            stdout="output",
            stderr="",
            returncode=0
        )

        result = self.driver.execute_shell_command(["env"], env={})

        assert result.stdout == "output"
        mock_run_subprocess.assert_called_once_with(
            cmd=["env"],
            cwd=None,
            env={},
            inputdata=None,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_empty_input_data(self, mock_run_subprocess):
        """Test running with empty input data"""
        mock_run_subprocess.return_value = Mock(
            stdout="",
            stderr="",
            returncode=0
        )

        result = self.driver.execute_shell_command(["cat"], inputdata="")

        assert result.stdout == ""
        mock_run_subprocess.assert_called_once_with(
            cmd=["cat"],
            cwd=None,
            env=None,
            inputdata="",
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_with_unicode_input(self, mock_run_subprocess):
        """Test running command with unicode input data"""
        mock_run_subprocess.return_value = Mock(
            stdout="unicode output: こんにちは",
            stderr="",
            returncode=0
        )

        unicode_input = "こんにちは世界\\n日本語テスト"
        result = self.driver.execute_shell_command(["cat"], inputdata=unicode_input)

        assert "こんにちは" in result.stdout
        mock_run_subprocess.assert_called_once_with(
            cmd=["cat"],
            cwd=None,
            env=None,
            inputdata=unicode_input,
            timeout=None
        )

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_command_with_special_characters(self, mock_run_subprocess):
        """Test running command with special characters"""
        mock_run_subprocess.return_value = Mock(
            stdout="special output",
            stderr="",
            returncode=0
        )

        special_cmd = ["echo", "test@#$%^&*()_+-={}[]|\\:;\"'<>?,."]
        result = self.driver.execute_shell_command(special_cmd)

        assert result.stdout == "special output"
        mock_run_subprocess.assert_called_once_with(
            cmd=special_cmd,
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )


class TestShellDriverParameterValidation(BaseTest):
    """Test parameter validation and error handling"""

    def setup_test(self):
        """Setup test data"""
        from src.infrastructure.mock.mock_file_driver import MockFileDriver
        self.mock_file_driver = MockFileDriver()
        self.driver = LocalShellDriver(self.mock_file_driver)

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_parameter_types(self, mock_run_subprocess):
        """Test that parameters maintain their types when passed through"""
        mock_run_subprocess.return_value = Mock(
            stdout="output",
            stderr="",
            returncode=0
        )

        # Test with string cwd
        self.driver.execute_shell_command(["echo"], cwd="/path/to/dir")
        call_args = mock_run_subprocess.call_args
        assert isinstance(call_args[1]['cwd'], str)

        # Test with integer timeout
        mock_run_subprocess.reset_mock()
        self.driver.execute_shell_command(["echo"], timeout=30)
        call_args = mock_run_subprocess.call_args
        assert isinstance(call_args[1]['timeout'], int)

        # Test with dict env
        mock_run_subprocess.reset_mock()
        self.driver.execute_shell_command(["echo"], env={"KEY": "value"})
        call_args = mock_run_subprocess.call_args
        assert isinstance(call_args[1]['env'], dict)

    @patch('src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess')
    def test_run_preserves_parameter_order(self, mock_run_subprocess):
        """Test that parameter order is preserved correctly"""
        mock_run_subprocess.return_value = Mock(
            stdout="output",
            stderr="",
            returncode=0
        )

        # Test positional and keyword argument order
        self.driver.execute_shell_command(
            ["test", "command"],
            "/working/dir",
            {"ENV": "test"},
            "input",
            60
        )

        call_args = mock_run_subprocess.call_args
        assert call_args[1]['cmd'] == ["test", "command"]
        assert call_args[1]['cwd'] == "/working/dir"
        assert call_args[1]['env'] == {"ENV": "test"}
        assert call_args[1]['inputdata'] == "input"
        assert call_args[1]['timeout'] == 60
