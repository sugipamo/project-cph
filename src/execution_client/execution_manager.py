import time
from abc import ABC, abstractmethod

class AbstractExecutionManager(ABC):
    @abstractmethod
    def run_and_measure(self, name, command, timeout=None, **kwargs):
        pass

class ExecutionManager(AbstractExecutionManager):
    def __init__(self, client):
        self.client = client  # AbstractExecutionClient

    def run_and_measure(self, name, command, timeout=None, **kwargs):
        # 事前準備（計測対象外）
        # 例: 入力ファイルの配置、環境変数セットなど

        input_data = kwargs.pop("input", None)
        cwd = kwargs.pop("cwd", None)
        # 既存のコンテナがrunningならexecでコマンド実行
        if hasattr(self.client, "is_container_running") and self.client.is_container_running(name):
            # docker execでコマンド実行
            result = self.client.exec_in(name, command, stdin=input_data, cwd=cwd)
            elapsed = None  # 必要なら計測
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout if result.stdout is not None else "",
                stderr=result.stderr if result.stderr is not None else "",
                extra={"elapsed": elapsed, "timeout": False}
            )
        # それ以外は従来通りrun
        if input_data is not None:
            # detach=Falseで直接実行し、inputを渡す
            result = self.client.run(name, command=command, detach=False, input=input_data, cwd=cwd, **kwargs)
            elapsed = None  # 必要なら計測
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout if result.stdout is not None else "",
                stderr=result.stderr if result.stderr is not None else "",
                extra={"elapsed": elapsed, "timeout": False}
            )
        # プロセス起動（detach=TrueでPopenを取得）
        result = self.client.run(name, command=command, detach=True, cwd=cwd, **kwargs)
        proc = result.extra.get("popen")
        # docker run等の場合はpopenがNone
        start = time.perf_counter()
        timeout_flag = False
        if proc is not None:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except Exception:
                proc.kill()
                stdout, stderr = proc.communicate()
                timeout_flag = True
            end = time.perf_counter()
            elapsed = end - start
            # プロセス終了後にクリーンアップ
            self.client.remove(name)
            return ExecutionResult(
                returncode=proc.returncode,
                stdout=stdout if stdout is not None else "",
                stderr=stderr if stderr is not None else "",
                extra={"elapsed": elapsed, "timeout": timeout_flag}
            )
        else:
            # docker run等: プロセスIDが取得できないので、状態をポーリング
            poll_interval = 0.05
            elapsed = 0.0
            while True:
                if timeout is not None and elapsed >= timeout:
                    timeout_flag = True
                    break
                # is_runningで状態確認
                if not self.client.is_running(name):
                    break
                time.sleep(poll_interval)
                elapsed = time.perf_counter() - start
            # 終了後、ログや出力を取得（必要に応じて拡張）
            self.client.remove(name)
            return ExecutionResult(
                returncode=None,
                stdout="",
                stderr="",
                extra={"elapsed": elapsed, "timeout": timeout_flag}
            ) 