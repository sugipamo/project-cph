from src.info_json_manager import InfoJsonManager
from ..docker.pool import DockerPool
from ..docker.ctl import DockerCtl
from src.docker.pool import DockerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from src.path_manager.file_operator import FileOperator
from src.config_json_manager import ConfigJsonManager

class CommandOpen:
    def __init__(self, file_manager, opener):
        self.file_manager = file_manager
        self.opener = opener
        self.upm = UnifiedPathManager()

    async def open(self, contest_name, problem_name, language_name):
        """
        問題ファイルを準備し、VSCodeとCursorでディレクトリを開く
        必要なコンテナを事前に起動し、system_info.jsonで管理する
        """
        import os
        import subprocess
        file_operator = self.file_manager.file_operator if self.file_manager and hasattr(self.file_manager, 'file_operator') else None
        # 1. 問題ファイル準備（system_info.jsonもここで更新される）
        if self.file_manager:
            self.file_manager.prepare_problem_files(contest_name, problem_name, language_name)
            problem_dir, test_dir = self.file_manager.get_problem_files(contest_name, problem_name, language_name)
        
        # 2. 問題ページをブラウザで開く
        url = f"https://atcoder.jp/contests/{contest_name}/tasks/{contest_name}_{problem_name}"
        if self.opener:
            self.opener.open_browser(url)
            # entry_file（config.json）を参照して開く
            config_path = self.upm.config_json()
            config_manager = ConfigJsonManager(config_path)
            entry_file = config_manager.get_entry_file(language_name)
            if entry_file:
                entry_path = self.upm.contest_current(language_name, entry_file)
                self.opener.open_editor(str(entry_path), language_name)
            else:
                self.opener.open_editor(str(problem_dir), language_name)
        
        # 3. テストケース数カウント
        if file_operator:
            # base_dirからの相対パス＋パターンでglobする
            test_dir_rel = os.path.relpath(self.upm.contest_current("test"), file_operator.base_dir)
            pattern = os.path.join(test_dir_rel, "*.in")
            test_case_count = len(list(file_operator.glob(pattern)))
        else:
            test_case_count = len([f for f in os.listdir(test_dir) if f.endswith('.in')]) if os.path.exists(test_dir) else 0
        
        # 4. DockerPoolで必要なコンテナを調整
        requirements = [
            {"type": "test", "language": language_name, "count": test_case_count},
            {"type": "ojtools", "count": 1}
        ]
        pool = DockerPool()
        containers = pool.adjust(requirements)
        
        # 5. system_info.jsonの更新
        info_path = self.upm.info_json()
        manager = InfoJsonManager(info_path)
        manager.data["contest_name"] = contest_name
        manager.data["problem_name"] = problem_name
        manager.data["language_name"] = language_name
        manager.data["containers"] = containers
        manager.save()
        
        # 6. テストケースダウンロード（ojtoolsコンテナでoj download）
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        ctl = DockerCtl()
        test_dir_host = self.upm.contest_current("test")
        if file_operator:
            if not file_operator.exists(test_dir_host):
                file_operator.makedirs(test_dir_host)
        else:
            os.makedirs(test_dir_host, exist_ok=True)
        if not ctl.is_container_running(ojtools_name):
            ctl.start_container(ojtools_name, DockerImageManager().ensure_image("ojtools"), {})
        # testディレクトリをクリーンアップ＆作成＆oj download
        ctl.exec_in_container(ojtools_name, ["rm", "-rf", f"/workspace/{test_dir_host}"])
        ctl.exec_in_container(ojtools_name, ["mkdir", "-p", f"/workspace/{test_dir_host}"])
        ctl.exec_in_container(ojtools_name, ["oj", "download", url, "-d", f"/workspace/{test_dir_host}"])
        # docker cpでホストにテストケースをコピー（test/testにならないようcontest_current/にコピー）
        ctl.cp_from_container(ojtools_name, f"/workspace/{test_dir_host}", self.upm.contest_current())