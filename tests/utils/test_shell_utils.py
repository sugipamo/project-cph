"""Tests for shell utilities module."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import subprocess
from queue import Queue, Empty
import os

from src.utils.shell_utils import ShellUtils


class TestShellUtils:
    """Test cases for ShellUtils class."""

    @patch('subprocess.run')
    def test_run_subprocess_simple_command(self, mock_run):
        """Test running simple subprocess command."""
        # Setup mock
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Execute
        result = ShellUtils.run_subprocess(
            cmd=["echo", "Hello, World!"],
            cwd="/tmp",
            env={"KEY": "value"},
            inputdata=None,
            timeout=30
        )
        
        # Verify
        assert result == mock_result
        mock_run.assert_called_once_with(
            ["echo", "Hello, World!"],
            cwd="/tmp",
            env={"KEY": "value"},
            input=None,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )

    @patch('subprocess.run')
    def test_run_subprocess_with_input(self, mock_run):
        """Test running subprocess with input data."""
        # Setup mock
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = "processed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Execute
        result = ShellUtils.run_subprocess(
            cmd="cat",
            cwd=None,
            env=None,
            inputdata="test input",
            timeout=10
        )
        
        # Verify
        assert result == mock_result
        mock_run.assert_called_once_with(
            "cat",
            cwd=None,
            env=None,
            input="test input",
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

    @patch('subprocess.run')
    def test_run_subprocess_timeout(self, mock_run):
        """Test running subprocess that times out."""
        # Setup mock to raise TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["sleep", "100"],
            timeout=1
        )
        
        # Execute and expect exception
        with pytest.raises(subprocess.TimeoutExpired):
            ShellUtils.run_subprocess(
                cmd=["sleep", "100"],
                cwd=None,
                env=None,
                inputdata=None,
                timeout=1
            )

    @patch('subprocess.Popen')
    def test_start_interactive(self, mock_popen):
        """Test starting interactive subprocess."""
        # Setup mock - don't use subprocess.Popen as spec since it's already mocked
        mock_proc = Mock()
        mock_popen.return_value = mock_proc
        
        # Execute
        result = ShellUtils.start_interactive(
            cmd=["python", "-i"],
            cwd="/workspace",
            env={"PYTHONPATH": "/lib"}
        )
        
        # Verify
        assert result == mock_proc
        mock_popen.assert_called_once_with(
            ["python", "-i"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/workspace",
            env={"PYTHONPATH": "/lib"},
            text=True,
            bufsize=1
        )

    def test_enqueue_output(self):
        """Test enqueuing output from stream."""
        # Create mock stream
        mock_stream = Mock()
        mock_stream.readline.side_effect = ["line1\n", "line2\n", "line3\n", ""]
        
        # Create queue
        queue = Queue()
        
        # Execute
        ShellUtils.enqueue_output(mock_stream, queue)
        
        # Verify
        assert queue.get() == "line1\n"
        assert queue.get() == "line2\n"
        assert queue.get() == "line3\n"
        assert queue.empty()
        mock_stream.close.assert_called_once()

    def test_enqueue_output_empty_stream(self):
        """Test enqueuing output from empty stream."""
        # Create mock stream
        mock_stream = Mock()
        mock_stream.readline.return_value = ""
        
        # Create queue
        queue = Queue()
        
        # Execute
        ShellUtils.enqueue_output(mock_stream, queue)
        
        # Verify
        assert queue.empty()
        mock_stream.close.assert_called_once()

    def test_drain_queue_with_items(self):
        """Test draining queue with items."""
        # Create queue with items
        queue = Queue()
        queue.put("item1")
        queue.put("item2")
        queue.put("item3")
        
        # Execute
        items = list(ShellUtils.drain_queue(queue))
        
        # Verify
        assert items == ["item1", "item2", "item3"]
        assert queue.empty()

    def test_drain_queue_empty(self):
        """Test draining empty queue."""
        # Create empty queue
        queue = Queue()
        
        # Execute
        items = list(ShellUtils.drain_queue(queue))
        
        # Verify
        assert items == []
        assert queue.empty()

    def test_enforce_timeout_process_completes(self):
        """Test enforcing timeout when process completes."""
        # Create mock process
        mock_proc = Mock(spec=subprocess.Popen)
        mock_proc.wait.return_value = 0
        
        # Create mock stop function
        stop_func = Mock()
        
        # Execute
        ShellUtils.enforce_timeout(mock_proc, timeout=10, stop_func=stop_func)
        
        # Verify
        mock_proc.wait.assert_called_once_with(timeout=10)
        stop_func.assert_not_called()

    def test_enforce_timeout_process_times_out(self):
        """Test enforcing timeout when process times out."""
        # Create mock process
        mock_proc = Mock(spec=subprocess.Popen)
        mock_proc.wait.side_effect = subprocess.TimeoutExpired(
            cmd="long_running",
            timeout=5
        )
        
        # Create mock stop function
        stop_func = Mock()
        
        # Execute
        ShellUtils.enforce_timeout(mock_proc, timeout=5, stop_func=stop_func)
        
        # Verify
        mock_proc.wait.assert_called_once_with(timeout=5)
        stop_func.assert_called_once_with(force=True)

    @patch('subprocess.run')
    def test_run_subprocess_with_error_output(self, mock_run):
        """Test running subprocess with error output."""
        # Setup mock
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Command failed"
        mock_run.return_value = mock_result
        
        # Execute
        result = ShellUtils.run_subprocess(
            cmd=["false"],
            cwd=None,
            env=None,
            inputdata=None,
            timeout=None
        )
        
        # Verify
        assert result.returncode == 1
        assert result.stderr == "Error: Command failed"
        assert result.stdout == ""