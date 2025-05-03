from podman_operator import PodmanOperator, LocalPodmanOperator

class CommandExecutor:
    def __init__(self, podman_operator: PodmanOperator = None):
        self.podman_operator = podman_operator or LocalPodmanOperator()

    async def login(self, *args, **kwargs):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        import os
        home = os.path.expanduser("~")
        oj_cache_host = os.path.join(home, ".cache/online-judge-tools")
        oj_cache_cont = "/root/.cache/online-judge-tools"
        volumes = {oj_cache_host: oj_cache_cont}
        workdir = "/workspace"  # 必要に応じて調整
        # 対話的にoj loginを実行
        return await self.podman_operator.run_oj(["login"], volumes, workdir, interactive=True)

    async def open(self, contest_name, problem_name, language_name):
        """
        online-judge-toolsで問題データ取得（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要な場合があるため）
        """
        raise NotImplementedError("openコマンドの実装が必要です")

    async def submit(self, contest_name, problem_name, language_name):
        """
        online-judge-toolsで提出（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要な場合があるため）
        """
        raise NotImplementedError("submitコマンドの実装が必要です")

    async def test(self, contest_name, problem_name, language_name):
        """独自実装でテストを行う"""
        raise NotImplementedError("testコマンドの実装が必要です")

    async def execute(self, command, contest_name=None, problem_name=None, language_name=None):
        """コマンド名に応じて各メソッドを呼び出す"""
        if command == "login":
            return await self.login()
        elif command == "open":
            return await self.open(contest_name, problem_name, language_name)
        elif command == "submit":
            return await self.submit(contest_name, problem_name, language_name)
        elif command == "test":
            return await self.test(contest_name, problem_name, language_name)
        else:
            raise ValueError(f"未対応のコマンドです: {command}") 