"""
Test process utilities
"""
import pytest
import subprocess
import os
import signal
import time
import sys
from unittest.mock import patch, MagicMock, call, Mock

# Mock psutil module before importing ProcessUtil
sys.modules['psutil'] = MagicMock()

from src.operations.utils.process_utils import ProcessUtil


class TestRunCommand:
    """Test run_command method"""
    
    @patch('subprocess.run')
    def test_run_command_basic(self, mock_run):
        """Test basic command execution"""
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = ProcessUtil.run_command(['echo', 'hello'])
        
        mock_run.assert_called_once_with(
            ['echo', 'hello'],
            cwd=None,
            env=None,
            input=None,
            timeout=None,
            capture_output=True,
            text=True
        )
        assert result == mock_result
    
    @patch('subprocess.run')
    def test_run_command_with_all_options(self, mock_run):
        """Test command execution with all options"""
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_run.return_value = mock_result
        
        env = {'PATH': '/usr/bin'}
        result = ProcessUtil.run_command(
            cmd=['ls', '-la'],
            cwd='/tmp',
            env=env,
            inputdata='input data',
            timeout=30,
            capture_output=False,
            text=False
        )
        
        mock_run.assert_called_once_with(
            ['ls', '-la'],
            cwd='/tmp',
            env=env,
            input='input data',
            timeout=30,
            capture_output=False,
            text=False
        )
        assert result == mock_result


class TestRunCommandAsync:
    """Test run_command_async method"""
    
    @patch('subprocess.Popen')
    def test_run_command_async_basic(self, mock_popen):
        """Test basic async command execution"""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        result = ProcessUtil.run_command_async(['sleep', '1'])
        
        mock_popen.assert_called_once_with(
            ['sleep', '1'],
            cwd=None,
            env=None,
            stdin=None,
            stdout=None,
            stderr=None,
            text=True
        )
        assert result == mock_process
    
    @patch('subprocess.Popen')
    def test_run_command_async_with_options(self, mock_popen):
        """Test async command with all options"""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        env = {'PATH': '/usr/bin'}
        result = ProcessUtil.run_command_async(
            cmd=['python', 'script.py'],
            cwd='/home/user',
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        mock_popen.assert_called_once_with(
            ['python', 'script.py'],
            cwd='/home/user',
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        assert result == mock_process


class TestKillProcessTree:
    """Test kill_process_tree method"""
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', False)
    @patch('os.kill')
    def test_kill_process_tree_without_psutil(self, mock_kill):
        """Test kill process tree when psutil is not available"""
        ProcessUtil.kill_process_tree(1234)
        mock_kill.assert_called_once_with(1234, signal.SIGTERM)
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', False)
    @patch('os.kill')
    def test_kill_process_tree_without_psutil_process_not_found(self, mock_kill):
        """Test kill process tree when process doesn't exist"""
        mock_kill.side_effect = ProcessLookupError()
        ProcessUtil.kill_process_tree(1234)  # Should not raise
        mock_kill.assert_called_once_with(1234, signal.SIGTERM)
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', True)
    @patch('src.operations.utils.process_utils.psutil.Process')
    @patch('src.operations.utils.process_utils.psutil.wait_procs')
    def test_kill_process_tree_with_psutil(self, mock_wait_procs, mock_process_cls):
        """Test kill process tree with psutil"""
        # Mock parent process
        mock_parent = MagicMock()
        mock_parent.pid = 1234
        
        # Mock child processes
        mock_child1 = MagicMock()
        mock_child1.pid = 1235
        mock_child2 = MagicMock()
        mock_child2.pid = 1236
        
        mock_parent.children.return_value = [mock_child1, mock_child2]
        mock_process_cls.return_value = mock_parent
        
        # All processes terminate gracefully
        mock_wait_procs.return_value = ([mock_parent, mock_child1, mock_child2], [])
        
        ProcessUtil.kill_process_tree(1234)
        
        # Verify children are signaled first
        mock_child1.send_signal.assert_called_once_with(signal.SIGTERM)
        mock_child2.send_signal.assert_called_once_with(signal.SIGTERM)
        mock_parent.send_signal.assert_called_once_with(signal.SIGTERM)
        
        # Verify wait_procs was called
        mock_wait_procs.assert_called_once()
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', True)
    @patch('src.operations.utils.process_utils.psutil.Process')
    @patch('src.operations.utils.process_utils.psutil.wait_procs')
    def test_kill_process_tree_force_kill(self, mock_wait_procs, mock_process_cls):
        """Test force kill when processes don't terminate gracefully"""
        mock_parent = MagicMock()
        mock_process_cls.return_value = mock_parent
        mock_parent.children.return_value = []
        
        # Process doesn't terminate gracefully
        mock_wait_procs.return_value = ([], [mock_parent])
        
        ProcessUtil.kill_process_tree(1234)
        
        # Verify force kill was called
        mock_parent.kill.assert_called_once()


class TestIsProcessRunning:
    """Test is_process_running method"""
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', False)
    @patch('os.kill')
    def test_is_process_running_without_psutil_true(self, mock_kill):
        """Test process running check without psutil - process exists"""
        mock_kill.return_value = None  # No exception means process exists
        assert ProcessUtil.is_process_running(1234) is True
        mock_kill.assert_called_once_with(1234, 0)
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', False)
    @patch('os.kill')
    def test_is_process_running_without_psutil_false(self, mock_kill):
        """Test process running check without psutil - process doesn't exist"""
        mock_kill.side_effect = ProcessLookupError()
        assert ProcessUtil.is_process_running(1234) is False
        mock_kill.assert_called_once_with(1234, 0)
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', True)
    @patch('src.operations.utils.process_utils.psutil.Process')
    def test_is_process_running_with_psutil_true(self, mock_process_cls):
        """Test process running check with psutil - process exists"""
        mock_process = MagicMock()
        mock_process.is_running.return_value = True
        mock_process_cls.return_value = mock_process
        
        assert ProcessUtil.is_process_running(1234) is True
        mock_process.is_running.assert_called_once()


class TestGetProcessInfo:
    """Test get_process_info method"""
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', False)
    def test_get_process_info_without_psutil(self):
        """Test get process info without psutil"""
        info = ProcessUtil.get_process_info(1234)
        assert info == {'pid': 1234, 'available': False}
    
    @patch('src.operations.utils.process_utils.HAS_PSUTIL', True)
    @patch('src.operations.utils.process_utils.psutil.Process')
    def test_get_process_info_with_psutil(self, mock_process_cls):
        """Test get process info with psutil"""
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.name.return_value = 'python'
        mock_process.cmdline.return_value = ['python', 'script.py']
        mock_process.status.return_value = 'running'
        mock_process.cpu_percent.return_value = 25.5
        mock_process.memory_info.return_value = MagicMock(rss=1024*1024*100)
        mock_process.create_time.return_value = 1234567890.0
        
        mock_process_cls.return_value = mock_process
        
        info = ProcessUtil.get_process_info(1234)
        
        assert info['pid'] == 1234
        assert info['name'] == 'python'
        assert info['cmdline'] == ['python', 'script.py']
        assert info['status'] == 'running'
        assert info['cpu_percent'] == 25.5
        assert info['memory_info'].rss == 1024*1024*100
        assert info['create_time'] == 1234567890.0


class TestFindProcessesByName:
    """Test find_processes_by_name method"""
    
    @patch('src.operations.utils.process_utils.psutil.process_iter')
    def test_find_processes_by_name(self, mock_process_iter):
        """Test finding processes by name"""
        # Mock process objects
        proc1 = MagicMock()
        proc1.info = {'pid': 1234, 'name': 'python'}
        
        proc2 = MagicMock()
        proc2.info = {'pid': 1235, 'name': 'bash'}
        
        proc3 = MagicMock()
        proc3.info = {'pid': 1236, 'name': 'python'}
        
        mock_process_iter.return_value = [proc1, proc2, proc3]
        
        pids = ProcessUtil.find_processes_by_name('python')
        
        assert pids == [1234, 1236]


class TestWaitForProcessCompletion:
    """Test wait_for_process_completion method"""
    
    @patch('src.operations.utils.process_utils.psutil.Process')
    def test_wait_for_process_completion_success(self, mock_process_cls):
        """Test waiting for process completion successfully"""
        mock_process = MagicMock()
        mock_process_cls.return_value = mock_process
        
        result = ProcessUtil.wait_for_process_completion(1234, timeout=30)
        
        assert result is True
        mock_process.wait.assert_called_once_with(timeout=30)


class TestSystemUsage:
    """Test system usage methods"""
    
    @patch('src.operations.utils.process_utils.psutil.virtual_memory')
    def test_get_system_memory_usage(self, mock_virtual_memory):
        """Test getting system memory usage"""
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory.used = 3 * 1024 * 1024 * 1024  # 3GB
        mock_memory.percent = 37.5
        
        mock_virtual_memory.return_value = mock_memory
        
        usage = ProcessUtil.get_system_memory_usage()
        
        assert usage['total'] == 8 * 1024 * 1024 * 1024
        assert usage['available'] == 4 * 1024 * 1024 * 1024
        assert usage['used'] == 3 * 1024 * 1024 * 1024
        assert usage['percent'] == 37.5
    
    @patch('src.operations.utils.process_utils.psutil.cpu_percent')
    def test_get_system_cpu_usage(self, mock_cpu_percent):
        """Test getting system CPU usage"""
        mock_cpu_percent.return_value = 45.2
        
        usage = ProcessUtil.get_system_cpu_usage()
        
        assert usage == 45.2
        mock_cpu_percent.assert_called_once_with(interval=1)