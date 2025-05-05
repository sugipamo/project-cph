from commands.info_json_manager import InfoJsonManager
from docker.pool import DockerPool
from docker.ctl import DockerCtl

class CommandOpen:
    def __init__(self, file_manager, opener):
        self.file_manager = file_manager
        self.opener = opener

    async def open(self, contest_name, problem_name, language_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        必要なコンテナを事前に起動し、info.jsonで管理する
        """
        import os
        import subprocess
        
        # 1. 問題ファイル準備（info.jsonもここで更新される）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
        
        # 2. 問題ページをブラウザで開く
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        if self.opener:
            self.opener.open_browser(url)
        
        # 3. テストケース数カウント
        test_dir = "contest_current/test"
        test_case_count = len([f for f in os.listdir(test_dir) if f.endswith('.in')]) if os.path.exists(test_dir) else 0
        
        # 4. DockerPoolで必要なコンテナを調整
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count},
            {"type": "ojtools", "count": 1}
        ]
        pool = DockerPool()
        containers = pool.adjust(requirements)
        
        # 5. info.jsonの更新
        info_path = "contest_current/info.json"
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.data["containers"] = containers
        manager.save()
        
        # 6. テストケースダウンロード（ojtoolsコンテナでoj download）
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがinfo.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        ctl = DockerCtl()
        test_dir_host = "contest_current/test"
        os.makedirs(test_dir_host, exist_ok=True)
        if not ctl.is_container_running(ojtools_name):
            ctl.start_container(ojtools_name, "oj", {})
        # testディレクトリをクリーンアップ＆作成＆oj download
        ctl.exec_in_container(ojtools_name, ["rm", "-rf", f"/workspace/{test_dir_host}"])
        ctl.exec_in_container(ojtools_name, ["mkdir", "-p", f"/workspace/{test_dir_host}"])
        ctl.exec_in_container(ojtools_name, ["oj", "download", url, "-d", f"/workspace/{test_dir_host}"])
        # docker cpでホストにテストケースをコピー（test/testにならないようcontest_current/にコピー）
        ctl.cp_from_container(ojtools_name, f"/workspace/{test_dir_host}", "contest_current/") 