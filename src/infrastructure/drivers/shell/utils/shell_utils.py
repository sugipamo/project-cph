"""Shell utilities for subprocess operations."""
import subprocess
from queue import Empty, Queue
from typing import Any, Optional, Union


class ShellUtils:
    """Utility class for shell command operations."""

    @staticmethod
    def run_subprocess(cmd: Union[str, list[str]], cwd: Optional[str] = None,
                      env: Optional[dict[str, str]] = None, inputdata: Optional[str] = None,
                      timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Launch subprocess and capture stdout/stderr.
        If inputdata is specified, pass it to stdin.

        Args:
            cmd: Command to execute
            cwd: Working directory
            env: Environment variables
            inputdata: Input data for stdin
            timeout: Command timeout

        Returns:
            CompletedProcess object with results
        """
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            input=inputdata,
            capture_output=True,
            text=True,
            timeout=timeout, check=False
        )
        return result

    @staticmethod
    def start_interactive(cmd: Union[str, list[str]], cwd: Optional[str] = None,
                         env: Optional[dict[str, str]] = None) -> subprocess.Popen:
        """Start interactive subprocess and return Popen object.

        Args:
            cmd: Command to execute
            cwd: Working directory
            env: Environment variables

        Returns:
            Popen object for interactive communication
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
    def enqueue_output(stream: Any, queue: Queue) -> None:
        """Enqueue output from stream to queue.

        Args:
            stream: Stream to read from
            queue: Queue to put output into
        """
        for line in iter(stream.readline, ''):
            queue.put(line)
        stream.close()

    @staticmethod
    def drain_queue(queue: Queue) -> Any:
        """Drain all items from queue.

        Args:
            queue: Queue to drain

        Yields:
            Items from the queue
        """
        while True:
            try:
                yield queue.get_nowait()
            except Empty:
                break

    @staticmethod
    def enforce_timeout(proc: subprocess.Popen, timeout: int, stop_func: Any) -> None:
        """Enforce timeout on process.

        Args:
            proc: Process to enforce timeout on
            timeout: Timeout in seconds
            stop_func: Function to call when timeout occurs
        """
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_func(force=True)
