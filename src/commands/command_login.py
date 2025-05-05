class CommandLogin:
    def __init__(self, docker_operator):
        self.docker_operator = docker_operator

    async def login(self):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        from commands.common import get_project_root_volumes
        volumes = get_project_root_volumes()
        workdir = "/workspace"
        # atcoder用URLを明示的に指定
        return await self.docker_operator.run_oj(["login", "https://atcoder.jp/"], volumes, workdir, interactive=True) 