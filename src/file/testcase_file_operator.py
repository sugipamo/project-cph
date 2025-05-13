from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import os
import subprocess
from src.logger import Logger

class AbstractTestcaseFileOperator(ABC):
    @abstractmethod
    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        pass

    @abstractmethod
    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        pass

    @abstractmethod
    def collect_test_cases(self, temp_test_dir):
        pass

    @abstractmethod
    def download_testcases(self, url, test_dir_host):
        pass

    @abstractmethod
    def submit_via_ojtools(self, args, workdir):
        print("[DEBUG] AbstractTestcaseFileOperator.submit_via_ojtools called", flush=True)
        pass

    def _build_oj_download_cmd(self, url, test_dir_host):
        return ["oj", "download", url, "-d", test_dir_host]

    def _build_oj_submit_cmd(self, args, cookie_path=".local/share/online-judge-tools/cookie.jar"):
        if not args:
            args = []
        if args and args[0] == "submit":
            return ["oj", "--cookie", cookie_path, "submit"] + args[1:]
        else:
            return ["oj", "--cookie", cookie_path] + args

class LocalTestcaseFileOperator(AbstractTestcaseFileOperator):
    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        temp_dir = Path(env_config.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        if language_config.copy_mode == "dir":
            # 例: Rust
            src_dir = upm.contest_current(language_name)
            dst_dir = temp_dir / language_name
            if dst_dir.exists():
                # 既存の内容を削除（target除外）
                for item in dst_dir.iterdir():
                    if item.name != "target":
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
            else:
                dst_dir.mkdir(parents=True, exist_ok=True)
            # 除外パターンに注意してコピー
            exclude = set(language_config.exclude_patterns)
            for item in src_dir.iterdir():
                if item.name in exclude:
                    continue
                dst_item = dst_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dst_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dst_item)
            return str(dst_dir)
        else:
            # 例: Python/PyPy
            src = upm.contest_current(language_name, language_config.source_file)
            dst_dir = temp_dir / language_name
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / language_config.source_file
            shutil.copy2(src, dst)
            return str(dst)

    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        temp_dir = Path(env_config.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        test_dir = upm.contest_current("test")
        temp_test_dir = temp_dir / "test"
        if temp_test_dir.exists():
            shutil.rmtree(temp_test_dir)
        if test_dir.exists():
            shutil.copytree(test_dir, temp_test_dir, dirs_exist_ok=True)
        return str(temp_test_dir)

    def collect_test_cases(self, temp_test_dir):
        in_files = sorted(Path(temp_test_dir).glob('*.in'))
        out_files = [str(f).replace('.in', '.out') for f in in_files]
        return in_files, out_files

    def download_testcases(self, url, test_dir_host):
        print("[DEBUG] download_testcases: test_dir_host=", test_dir_host, flush=True)
        cmd = self._build_oj_download_cmd(url, test_dir_host)
        if os.path.exists(test_dir_host):
            shutil.rmtree(test_dir_host)
        os.makedirs(test_dir_host, exist_ok=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            if "Failed to download since file already exists" in result.stdout:
                Logger.info("oj download: files already exist, skipping error.")
            else:
                Logger.error(f"oj download failed: {result.stderr}")
                raise RuntimeError("oj download failed")
        Logger.info(result.stdout)

    def submit_via_ojtools(self, args, workdir):
        print("[DEBUG] LocalTestcaseFileOperator.submit_via_ojtools called", flush=True)
        cmd = self._build_oj_submit_cmd(args)
        result = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        ok = result.returncode == 0
        if not ok:
            Logger.error(f"oj submit failed: {result.stderr}")
            Logger.error(f"oj submit stdout: {result.stdout}")
        return ok, result.stdout, result.stderr

# 今後の拡張用
class DockerTestcaseFileOperator(AbstractTestcaseFileOperator):
    def __init__(self, ctl, resource_manager):
        self.ctl = ctl  # ContainerClient等
        self.resource_manager = resource_manager

    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        pass
    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        pass
    def collect_test_cases(self, temp_test_dir):
        return [], []
    def download_testcases(self, url, test_dir_host):
        print("[DEBUG] download_testcases: test_dir_host=", test_dir_host, flush=True)
        cmd = self._build_oj_download_cmd(url, test_dir_host)
        container = self.resource_manager.get_ojtools_container()
        result = self.ctl.exec_in_container(container, cmd)
        print("[DEBUG] download_testcases: container=", container, flush=True)
        print("[DEBUG] download_testcases: cmd=", cmd, flush=True)
        print("[DEBUG] download_testcases: result.returncode=", result.returncode, flush=True)
        print("[DEBUG] download_testcases: result.stdout=", result.stdout, flush=True)
        print("[DEBUG] download_testcases: result.stderr=", result.stderr, flush=True)
        if result.returncode != 0:
            if "Failed to download since file already exists" in result.stdout:
                Logger.info("oj download: files already exist, skipping error.")
            else:
                Logger.error(f"oj download failed: {result.stderr}")
                raise RuntimeError("oj download failed")
        Logger.info(result.stdout)
    def submit_via_ojtools(self, args, workdir):
        print("[DEBUG] DockerTestcaseFileOperator.submit_via_ojtools called", flush=True)
        info_path = self.resource_manager.upm.info_json()
        print("[DEBUG] info_path=", info_path, flush=True)
        print("[DEBUG] info_path exists=", os.path.exists(info_path), flush=True)
        with open(info_path, "r", encoding="utf-8") as f:
            info_json = f.read()
        print("[DEBUG] info_json=", info_json, flush=True)
        from src.execution_env.info_json_manager import InfoJsonManager
        manager = InfoJsonManager(info_path)
        ojtools_list = manager.get_containers(type="ojtools")
        print("[DEBUG] get_containers(type=\"ojtools\")=", ojtools_list, flush=True)
        cmd = self._build_oj_submit_cmd(args)
        container = self.resource_manager.get_ojtools_container()
        print("[DEBUG] container=", container, flush=True)
        print("[DEBUG] cmd=", cmd, flush=True)
        print("[DEBUG] cwd=", workdir, flush=True)
        result = self.ctl.exec_in_container(container, cmd, cwd=workdir)
        ok = result.returncode == 0
        if not ok:
            Logger.error(f"oj submit failed: {result.stderr}")
            Logger.error(f"oj submit stdout: {result.stdout}")
        return ok, result.stdout, result.stderr

class CloudTestcaseFileOperator(AbstractTestcaseFileOperator):
    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        pass
    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        pass
    def collect_test_cases(self, temp_test_dir):
        return [], []
    def download_testcases(self, url, test_dir_host):
        pass
    def submit_via_ojtools(self, args, workdir):
        print("[DEBUG] CloudTestcaseFileOperator.submit_via_ojtools called", flush=True)
        pass 