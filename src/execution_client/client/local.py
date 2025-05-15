from typing import Any, Optional, List, Dict, Callable
from src.shell_process import ShellProcess, ShellProcessOptions, ShellProcessPool
import threading
import time

class LocalAsyncClient():
    def __init__(self):
        # name -> (Popen, stdout, stderr)
        self._processes = {}
        self._lock = threading.Lock()

    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> ShellProcess:
        if not command:
            raise ValueError("command must be specified for local execution")
        input_data = kwargs.get("input", None)
        cwd = kwargs.get("cwd", None)
        options = ShellProcessOptions(cmd=command, input_data=input_data, cwd=cwd)
        with self._lock:
            if name in self._processes:
                raise RuntimeError(f"Process with name {name} already running")
            if not realtime:
                if not detach:
                    proc = ShellProcess.run(options=options)
                    return proc
                else:
                    proc = ShellProcess.popen(options=options, detach=True)
                    self._processes[name] = proc
            else:
                proc = ShellProcess.popen(options=options, detach=True)
                self._processes[name] = proc
                def reader(stream, callback):
                    for line in stream.splitlines(keepends=True):
                        if callback:
                            callback(line)
                if on_stdout and proc.stdout:
                    t_out = threading.Thread(target=reader, args=(proc.stdout, on_stdout))
                    t_out.daemon = True
                    t_out.start()
                if on_stderr and proc.stderr:
                    t_err = threading.Thread(target=reader, args=(proc.stderr, on_stderr))
                    t_err.daemon = True
                    t_err.start()
        if detach or realtime:
            return proc

    def stop(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            if not proc:
                return False
            # ShellProcess.popenの返り値はShellProcessインスタンス
            if hasattr(proc, '_popen') and proc._popen:
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

    def exec_in(self, name: str, cmd: List[str], realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> ShellProcess:
        options = ShellProcessOptions(cmd=cmd)
        if not realtime:
            proc = ShellProcess.run(options=options)
            return proc
        else:
            proc = ShellProcess.popen(options=options, detach=True)
            def reader(stream, callback):
                for line in stream.splitlines(keepends=True):
                    if callback:
                        callback(line)
            if on_stdout and proc.stdout:
                t_out = threading.Thread(target=reader, args=(proc.stdout, on_stdout))
                t_out.daemon = True
                t_out.start()
            if on_stderr and proc.stderr:
                t_err = threading.Thread(target=reader, args=(proc.stderr, on_stderr))
                t_err.daemon = True
                t_err.start()
            return proc

    def is_running(self, name: str) -> bool:
        with self._lock:
            proc = self._processes.get(name)
            print(f"[DEBUG] is_running: proc={proc}")
            if not proc:
                return False
            print(f"[DEBUG] is_running: proc._popen={getattr(proc, '_popen', None)}")
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
        options = ShellProcessOptions(cmd=command, input_data=input_data, cwd=cwd)
        proc = ShellProcess.run(options=options)
        return proc 