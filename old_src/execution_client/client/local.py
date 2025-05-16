from typing import Any, Optional, List, Dict, Callable
from src.shell_process import ShellProcess, ShellProcessOptions, ShellProcessPool
import threading
import time
from src.operations.shell.shell_request import ShellRequest

class LocalAsyncClient():
    def __init__(self):
        # name -> (Popen, stdout, stderr)
        self._processes = {}
        self._lock = threading.Lock()

    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> ShellRequest:
        if not command:
            raise ValueError("command must be specified for local execution")
        input_data = kwargs.get("input", None)
        cwd = kwargs.get("cwd", None)
        options = dict(cmd=command, inputdata=input_data, cwd=cwd)
        with self._lock:
            if name in self._processes:
                raise RuntimeError(f"Process with name {name} already running")
            if not realtime:
                if not detach:
                    req = ShellRequest(**options)
                    result = req.execute()
                    return result
                else:
                    # detachやrealtime対応はShellInteractiveRequestで対応可能
                    from src.operations.shell.shell_interactive_request import ShellInteractiveRequest
                    req = ShellInteractiveRequest(command, cwd=cwd)
                    req.start()
                    self._processes[name] = req
            else:
                from src.operations.shell.shell_interactive_request import ShellInteractiveRequest
                req = ShellInteractiveRequest(command, cwd=cwd)
                req.start()
                self._processes[name] = req
                def reader(get_line, callback):
                    while True:
                        line = get_line()
                        if line is None:
                            break
                        if callback:
                            callback(line)
                if on_stdout:
                    t_out = threading.Thread(target=reader, args=(req.read_output_line, on_stdout))
                    t_out.daemon = True
                    t_out.start()
                if on_stderr:
                    t_err = threading.Thread(target=reader, args=(req.read_error_line, on_stderr))
                    t_err.daemon = True
                    t_err.start()
        if detach or realtime:
            return req

    def stop(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            if not proc:
                return False
            # ShellInteractiveRequest対応
            if hasattr(proc, 'stop'):
                proc.stop()
            # 旧ShellProcess対応
            elif hasattr(proc, '_popen') and proc._popen:
                proc._popen.terminate()
                try:
                    proc._popen.wait(timeout=5)
                except Exception:
                    proc._popen.kill()
            del self._processes[name]
        return True

    def remove(self, name: str) -> bool:
        # ローカルプロセスの場合、stopと同じ
        return self.stop(name)

    def exec_in(self, name: str, cmd: List[str], realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> ShellRequest:
        options = dict(cmd=cmd)
        if not realtime:
            req = ShellRequest(**options)
            result = req.execute()
            return result
        else:
            from src.operations.shell.shell_interactive_request import ShellInteractiveRequest
            req = ShellInteractiveRequest(cmd)
            req.start()
            def reader(get_line, callback):
                while True:
                    line = get_line()
                    if line is None:
                        break
                    if callback:
                        callback(line)
            if on_stdout:
                t_out = threading.Thread(target=reader, args=(req.read_output_line, on_stdout))
                t_out.daemon = True
                t_out.start()
            if on_stderr:
                t_err = threading.Thread(target=reader, args=(req.read_error_line, on_stderr))
                t_err.daemon = True
                t_err.start()
            return req

    def is_running(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            print(f"[DEBUG] is_running: proc={proc}")
            if not proc:
                return False
            # ShellInteractiveRequest対応
            if hasattr(proc, 'is_running'):
                running = proc.is_running()
                print(f"[DEBUG] is_running: ShellInteractiveRequest.is_running()={running}")
                return running
            # 旧ShellProcess対応
            if hasattr(proc, '_popen') and proc._popen:
                poll_val = proc._popen.poll()
                print(f"[DEBUG] is_running: poll={poll_val}")
                return poll_val is None
            return False

    def list(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        with self._lock:
            names = list(self._processes.keys())
        if prefix:
            names = [n for n in names if n.startswith(prefix)]
        return names

    def run_many(self, commands: List[ShellProcessOptions], options_list: Optional[List[ShellProcessOptions]] = None, max_workers: int = 4) -> List[ShellProcess]:
        """
        commands: List of ShellProcessOptions
        options_list: List of ShellProcessOptions or None
        return: List[ExecutionResult]
        """
        pool = ShellProcessPool(max_workers=max_workers)
        procs = pool.run_many(commands, options_list=options_list)
        return procs

    def exec_many(self, commands: List[ShellProcessOptions], options_list: Optional[List[ShellProcessOptions]] = None, max_workers: int = 4) -> List[ShellProcess]:
        """
        commands: List of ShellProcessOptions
        options_list: List of ShellProcessOptions or None
        return: List[ExecutionResult]
        """
        pool = ShellProcessPool(max_workers=max_workers)
        procs = pool.popen_many(commands, options_list=options_list)
        return procs

    def build(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, **kwargs) -> Any:
        # 通常はビルドコマンド（例: gcc, javacなど）をcommandで指定して実行
        if not command:
            raise ValueError("build command must be specified for local execution")
        input_data = kwargs.get("input", None)
        cwd = kwargs.get("cwd", None)
        options = dict(cmd=command, inputdata=input_data, cwd=cwd)
        req = ShellRequest(**options)
        result = req.execute()
        return result 