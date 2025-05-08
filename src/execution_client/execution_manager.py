import time
from execution_client.types import ExecutionResult

class ExecutionManager:
    def __init__(self, client):
        self.client = client  # AbstractExecutionClient

    def run_and_measure(self, name, command, **kwargs):
        # 事前準備（計測対象外）
        # 例: 入力ファイルの配置、環境変数セットなど

        # プロセス起動（detach=TrueでPopenを取得）
        result = self.client.run(name, command=command, detach=True, **kwargs)
        proc = result.extra["popen"]

        # 計測開始
        start = time.perf_counter()

        # プロセス終了まで待機
        stdout, stderr = proc.communicate()

        # 計測終了
        end = time.perf_counter()
        elapsed = end - start

        return ExecutionResult(
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            extra={"elapsed": elapsed}
        ) 