import subprocess
import threading
from queue import Queue, Empty

class ShellUtils:
    @staticmethod
    def run_subprocess(cmd, cwd=None, env=None, inputdata=None, timeout=None):
        """
        サブプロセスを起動し、標準出力・標準エラーを取得して返す。
        inputdataが指定された場合は標準入力に渡す。
        """
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            input=inputdata,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result

    @staticmethod
    def start_interactive(cmd, cwd=None, env=None):
        """
        インタラクティブなサブプロセスを起動し、Popenオブジェクトを返す。
        """
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            text=True,
            bufsize=1
        )
        return proc

    @staticmethod
    def enqueue_output(stream, queue):
        for line in iter(stream.readline, ''):
            queue.put(line)
        stream.close()

    @staticmethod
    def drain_queue(queue):
        while True:
            try:
                yield queue.get_nowait()
            except Empty:
                break

    @staticmethod
    def enforce_timeout(proc, timeout, stop_func):
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_func(force=True) 