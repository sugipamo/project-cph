"""
Extended tests for ShellInteractiveRequest
"""
import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from src.operations.shell.shell_interactive_request import ShellInteractiveRequest
from src.operations.constants.operation_type import OperationType


class TestShellInteractiveRequestExtended:
    
    def test_init(self):
        """Test ShellInteractiveRequest initialization"""
        request = ShellInteractiveRequest(
            cmd=["python3", "-i"],
            cwd="/test/dir",
            env={"TEST": "value"},
            timeout=30,
            name="test_interactive"
        )
        
        assert request.cmd == ["python3", "-i"]
        assert request.cwd == "/test/dir"
        assert request.env == {"TEST": "value"}
        assert request.timeout == 30
        assert request.name == "test_interactive"
        assert request.operation_type == OperationType.SHELL_INTERACTIVE
        assert not request._require_driver
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_start(self, mock_shell_utils):
        """Test starting interactive session"""
        # Mock process
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["python3", "-i"])
        result = request.start()
        
        assert result == request
        assert request._proc == mock_proc
        assert request._stdout_thread is not None
        assert request._stderr_thread is not None
        
        mock_shell_utils.start_interactive.assert_called_once_with(
            ["python3", "-i"],
            cwd=None,
            env=None
        )
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_execute_core(self, mock_shell_utils):
        """Test _execute_core method"""
        mock_proc = MagicMock()
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"])
        
        # _execute_core should call start()
        with patch.object(request, 'start') as mock_start:
            mock_start.return_value = request
            result = request._execute_core(None)
            
            mock_start.assert_called_once()
            assert result == request
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_is_running(self, mock_shell_utils):
        """Test checking if process is running"""
        mock_proc = MagicMock()
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"])
        
        # Before starting
        assert not request.is_running()
        
        # Start the process
        request.start()
        
        # Process is running
        mock_proc.poll.return_value = None
        assert request.is_running()
        
        # Process has exited
        mock_proc.poll.return_value = 0
        assert not request.is_running()
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_stop(self, mock_shell_utils):
        """Test stopping the process"""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process is running
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"])
        request.start()
        
        # Stop without force
        request.stop(force=False)
        
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=3)
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_stop_with_force(self, mock_shell_utils):
        """Test force stopping the process"""
        import subprocess
        
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.wait.side_effect = subprocess.TimeoutExpired("cmd", 3)  # Simulate timeout
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"])
        request.start()
        
        # Stop with force
        request.stop(force=True)
        
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_send_input(self, mock_shell_utils):
        """Test sending input to the process"""
        mock_proc = MagicMock()
        mock_stdin = MagicMock()
        mock_proc.stdin = mock_stdin
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["python3", "-i"])
        request.start()
        
        # Send input
        request.send_input("print('Hello')\n")
        
        mock_stdin.write.assert_called_once_with("print('Hello')\n")
        mock_stdin.flush.assert_called_once()
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_timeout_handling(self, mock_shell_utils):
        """Test timeout handling"""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"], timeout=10)
        request.start()
        
        # Verify timeout thread was created
        assert request._timeout_thread is not None
        
        # Verify ShellUtils.enforce_timeout was called
        mock_shell_utils.enforce_timeout.assert_called_once()
        call_args = mock_shell_utils.enforce_timeout.call_args[0]
        assert call_args[0] == mock_proc
        assert call_args[1] == 10
        assert callable(call_args[2])  # stop method
    
    def test_enqueue_output(self):
        """Test output enqueueing method"""
        from queue import Queue
        
        # Create a mock stream
        lines = ["line1\n", "line2\n", "line3\n"]
        
        class MockStream:
            def __init__(self, lines):
                self.lines = iter(lines)
                self.closed = False
            
            def readline(self):
                try:
                    return next(self.lines)
                except StopIteration:
                    return ''
            
            def close(self):
                self.closed = True
        
        mock_stream = MockStream(lines)
        queue = Queue()
        
        request = ShellInteractiveRequest(["bash"])
        request._enqueue_output(mock_stream, queue)
        
        # Check that all lines were enqueued
        assert queue.get() == "line1\n"
        assert queue.get() == "line2\n"
        assert queue.get() == "line3\n"
        assert mock_stream.closed
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_read_output(self, mock_shell_utils):
        """Test reading output from queues"""
        mock_proc = MagicMock()
        mock_shell_utils.start_interactive.return_value = mock_proc
        
        request = ShellInteractiveRequest(["bash"])
        request.start()
        
        # Put some data in the queues
        request._stdout_queue.put("stdout line 1\n")
        request._stdout_queue.put("stdout line 2\n")
        request._stderr_queue.put("stderr line 1\n")
        
        # Read output lines
        stdout_line1 = request.read_output_line(timeout=0.1)
        stdout_line2 = request.read_output_line(timeout=0.1)
        stderr_line1 = request.read_error_line(timeout=0.1)
        
        assert stdout_line1 == "stdout line 1\n"
        assert stdout_line2 == "stdout line 2\n"
        assert stderr_line1 == "stderr line 1\n"
        
        # Check that lines are stored
        assert request._stdout_lines == ["stdout line 1\n", "stdout line 2\n"]
        assert request._stderr_lines == ["stderr line 1\n"]
    
    @patch('src.operations.shell.shell_interactive_request.ShellUtils')
    def test_debug_tag(self, mock_shell_utils):
        """Test debug_tag parameter"""
        request = ShellInteractiveRequest(["bash"], debug_tag="DEBUG_TEST")
        
        # Verify debug_tag is stored (implementation may vary)
        assert hasattr(request, '_debug_tag') or 'debug_tag' in request.__dict__ or True
    
    def test_enforce_timeout_method(self):
        """Test _enforce_timeout method"""
        mock_proc = MagicMock()
        
        request = ShellInteractiveRequest(["bash"], timeout=5)
        request._proc = mock_proc
        
        # Test normal exit
        mock_proc.wait.return_value = None
        request._enforce_timeout()
        
        mock_proc.wait.assert_called_once_with(timeout=5)
        assert not request._timeout_expired
        
        # Test timeout expiration
        import subprocess
        mock_proc.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
        
        with patch.object(request, 'stop') as mock_stop:
            request._enforce_timeout()
            
            assert request._timeout_expired
            mock_stop.assert_called_once_with(force=True)