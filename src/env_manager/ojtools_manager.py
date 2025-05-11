class OjtoolsManager:
    def __init__(self, upm, ctl, image_manager, info_json_manager):
        self.upm = upm
        self.ctl = ctl
        self.image_manager = image_manager
        self.info_json_manager = info_json_manager

    # ojtoolsによるテストケースDL・提出
    def download_testcases(self, url, test_dir_host):
        info_path = self.upm.info_json()
        manager = self.info_json_manager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        if not self.ctl.is_container_running(ojtools_name):
            self.ctl.run_container(ojtools_name, self.image_manager.ensure_image("ojtools"), {})
        # test_dir_hostの親ディレクトリを取得
        self.upm.to_container_path(test_dir_host)

    def submit_via_ojtools(self, args, volumes, workdir):
        info_path = self.upm.info_json()
        manager = self.info_json_manager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        if not ojtools_list:
            raise RuntimeError("ojtools用コンテナがsystem_info.jsonにありません")
        ojtools_name = ojtools_list[0]["name"]
        if not self.ctl.is_container_running(ojtools_name):
            self.ctl.start_container(ojtools_name, self.image_manager.ensure_image("ojtools"), {})
        cmd = ["oj"] + args
        result = self.ctl.exec_in_container(ojtools_name, cmd)
        print(f"returncode: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        ok = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr
        return ok, stdout, stderr 