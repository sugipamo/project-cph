class CommandLogin:
    def __init__(self, docker_operator):
        self.docker_operator = docker_operator

    async def login(self):
        """
        online-judge-toolsでログインする（ojtラッパー）
        ※このメソッドのテストは手動で行うことを推奨（対話が必要なため）
        """
        import os
        project_root = os.path.abspath(".")
        oj_cache_host = os.path.join(project_root, ".oj/.cache/online-judge-tools")
        oj_cache_cont = "/workspace/.cache/online-judge-tools"
        oj_local_host = os.path.join(project_root, ".oj/.local/share/online-judge-tools")
        oj_local_cont = "/workspace/.local/share/online-judge-tools"
        volumes = {
            oj_cache_host: oj_cache_cont,
            oj_local_host: oj_local_cont,
            project_root: "/workspace"
        }
        workdir = "/workspace"
        # atcoder用URLを明示的に指定
        return await self.docker_operator.run_oj(["login", "https://atcoder.jp/"], volumes, workdir, interactive=True) 