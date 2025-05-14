import subprocess
import time
import json
from typing import Optional, Any, Dict, Union, List, Tuple
import logging
import concurrent.futures
import asyncio
import threading

class ShellProcessOptions:
    def __init__(self, cmd=None, env=None, cwd=None, log_file=None, input_data=None, timeout=None, on_stdout=None, on_stderr=None, **kwargs):
        self.cmd = cmd
        self.env = env
        self.cwd = cwd
        self.log_file = log_file
        self.input_data = input_data
        self.timeout = timeout
        self.on_stdout = on_stdout
        self.on_stderr = on_stderr
        self.extra = kwargs
    def to_dict(self):
        d = dict(cmd=self.cmd, env=self.env, cwd=self.cwd, log_file=self.log_file, input_data=self.input_data, timeout=self.timeout)
        d.update(self.extra)
        return d
    def __getitem__(self, key):
        return self.to_dict()[key]
    def __contains__(self, key):
        return key in self.to_dict()
    def get(self, key, default=None):
        return self.to_dict().get(key, default)
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    @classmethod
    def from_json(cls, json_str: str) -> 'ShellProcessOptions':
        data = json.loads(json_str)
        return cls(**data)

class ShellProcess:
    def __init__(self):
        self.options: Optional[ShellProcessOptions] = None
        self.use_popen = False
        self._result: Optional[Union[subprocess.CompletedProcess, tuple]] = None
        self._popen: Optional[subprocess.Popen] = None
        self._exception: Optional[Exception] = None
        self._has_error: bool = False
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._elapsed: Optional[float] = None

    @classmethod
    def run(cls, options: 'ShellProcessOptions' = None):
        obj = cls()
        obj.options = options or ShellProcessOptions()
        obj.use_popen = False
        obj._run_with_run()
        # runは基本的に同期実行なので、on_stdout/on_stderrは出力全体を渡す
        if obj.options.on_stdout and obj.stdout:
            obj.options.on_stdout(obj.stdout)
        if obj.options.on_stderr and obj.stderr:
            obj.options.on_stderr(obj.stderr)
        return obj

    @classmethod
    def popen(cls, options: 'ShellProcessOptions' = None):
        obj = cls()
        obj.options = options or ShellProcessOptions()
        obj.use_popen = True
        obj._run_with_popen()
        return obj

    def _run_with_run(self):
        self._exception = None
        self._has_error = False
        self._start_time = time.perf_counter()
        try:
            self._result = subprocess.run(
                args=self.options.cmd,
                input=self.options.input_data,
                env=self.options.env,
                cwd=self.options.cwd,
                text=True,
                capture_output=True,
                timeout=self.options.timeout,
                **self.options.extra
            )
        except subprocess.TimeoutExpired as e:
            self._exception = e
            self._has_error = True
        except Exception as e:
            self._exception = e
            self._has_error = True
        self._end_time = time.perf_counter()
        self._elapsed = self._end_time - self._start_time
        self._log_result()

    def _run_with_popen(self):
        self._exception = None
        self._has_error = False
        self._start_time = time.perf_counter()
        try:
            self._popen = subprocess.Popen(
                args=self.options.cmd,
                env=self.options.env,
                cwd=self.options.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **self.options.extra
            )
            stdout, stderr = self._popen.communicate(input=self.options.input_data)
            self._result = (stdout, stderr, self._popen.returncode)
            # コールバックが指定されていればスレッドで呼び出し
            def call_callback(stream, callback):
                for line in stream.splitlines(keepends=True):
                    callback(line)
            if self.options.on_stdout and stdout:
                t_out = threading.Thread(target=call_callback, args=(stdout, self.options.on_stdout))
                t_out.daemon = True
                t_out.start()
            if self.options.on_stderr and stderr:
                t_err = threading.Thread(target=call_callback, args=(stderr, self.options.on_stderr))
                t_err.daemon = True
                t_err.start()
        except Exception as e:
            self._exception = e
            self._has_error = True
        self._end_time = time.perf_counter()
        self._elapsed = self._end_time - self._start_time
        self._log_result()

    @property
    def stdout(self) -> Optional[str]:
        if self.use_popen and self._result:
            return self._result[0]
        if self._result and hasattr(self._result, 'stdout'):
            return self._result.stdout
        return None

    @property
    def stderr(self) -> Optional[str]:
        if self.use_popen and self._result:
            return self._result[1]
        if self._result and hasattr(self._result, 'stderr'):
            return self._result.stderr
        return None

    @property
    def returncode(self) -> Optional[int]:
        if self.use_popen and self._result:
            return self._result[2]
        if self._result and hasattr(self._result, 'returncode'):
            return self._result.returncode
        return None

    @property
    def has_error(self) -> bool:
        if self._has_error:
            return True
        rc = self.returncode
        return rc is not None and rc != 0

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    @property
    def elapsed(self) -> Optional[float]:
        return self._elapsed

    @property
    def start_time(self) -> Optional[float]:
        return self._start_time

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    def raise_if_error(self):
        if self._exception:
            raise self._exception
        rc = self.returncode
        if rc is not None and rc != 0:
            raise subprocess.CalledProcessError(
                rc,
                self.options.cmd,
                output=self.stdout,
                stderr=self.stderr
            )

    def retry(self, max_retry=1, retry_interval=0.5):
        for i in range(max_retry):
            if not self.has_error:
                break
            if self.use_popen:
                self._run_with_popen()
            else:
                self._run_with_run()
            time.sleep(retry_interval)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'options': self.options.to_dict() if self.options else None,
            'use_popen': self.use_popen,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'has_error': self.has_error,
            'exception': str(self._exception) if self._exception else None,
            'elapsed': self.elapsed,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def _log_result(self):
        log_file = self.options.log_file if self.options else None
        if log_file:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(self.to_json() + '\n')
            except Exception as e:
                logging.warning(f"ログファイル書き込み失敗: {e}")
        else:
            logging.debug(self.to_json())

class ShellProcessPool:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers

    def run_many(self, commands: List[ShellProcessOptions], options_list: List[ShellProcessOptions] = None) -> List[ShellProcess]:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, opts in enumerate(commands):
                futures.append(executor.submit(ShellProcess.run, opts))
            for f in futures:
                results.append(f.result())
        return results

    def popen_many(self, commands: List[ShellProcessOptions], options_list: List[ShellProcessOptions] = None) -> List[ShellProcess]:
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, opts in enumerate(commands):
                futures.append(executor.submit(ShellProcess.popen, opts))
            for f in futures:
                results.append(f.result())
        return results

class ShellProcessAsync:
    def __init__(self):
        self.options: Optional[ShellProcessOptions] = None
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._exception: Optional[Exception] = None
        self._has_error: bool = False
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._elapsed: Optional[float] = None
        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self.returncode: Optional[int] = None

    @classmethod
    async def run(cls, options: ShellProcessOptions = None):
        obj = cls()
        obj.options = options or ShellProcessOptions()
        await obj._run_with_asyncio()
        return obj

    async def _run_with_asyncio(self):
        self._exception = None
        self._has_error = False
        self._start_time = time.perf_counter()
        try:
            async def _do():
                proc = await asyncio.create_subprocess_exec(
                    *self.options.cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self.options.env,
                    cwd=self.options.cwd,
                    **self.options.extra
                )
                self._proc = proc
                stdout, stderr = await proc.communicate(input=self.options.input_data.encode() if self.options.input_data else None)
                self.stdout = stdout.decode() if stdout else ''
                self.stderr = stderr.decode() if stderr else ''
                self.returncode = proc.returncode
            if self.options.timeout:
                await asyncio.wait_for(_do(), timeout=self.options.timeout)
            else:
                await _do()
        except asyncio.TimeoutError as e:
            self._exception = e
            self._has_error = True
        except Exception as e:
            self._exception = e
            self._has_error = True
        self._end_time = time.perf_counter()
        self._elapsed = self._end_time - self._start_time
        # ログ出力は省略（必要なら追加可）

    @property
    def has_error(self) -> bool:
        if self._has_error:
            return True
        rc = self.returncode
        return rc is not None and rc != 0

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    @property
    def elapsed(self) -> Optional[float]:
        return self._elapsed

    @property
    def start_time(self) -> Optional[float]:
        return self._start_time

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    def raise_if_error(self):
        if self._exception:
            raise self._exception
        rc = self.returncode
        if rc is not None and rc != 0:
            raise subprocess.CalledProcessError(
                rc,
                self.options.cmd,
                output=self.stdout,
                stderr=self.stderr
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'options': self.options.to_dict() if self.options else None,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode,
            'has_error': self.has_error,
            'exception': str(self._exception) if self._exception else None,
            'elapsed': self.elapsed,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class ShellProcessAsyncPool:
    def __init__(self):
        pass

    async def run_many(self, commands: List[ShellProcessOptions], options_list: List[ShellProcessOptions] = None) -> List[ShellProcessAsync]:
        tasks = []
        for i, opts in enumerate(commands):
            tasks.append(ShellProcessAsync.run(opts))
        return await asyncio.gather(*tasks)
