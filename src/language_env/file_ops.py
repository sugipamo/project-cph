from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import os
import subprocess

class AbstractFileOps(ABC):
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

class LocalFileOps(AbstractFileOps):
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
        cmd = self._build_oj_download_cmd(url, test_dir_host)
        if os.path.exists(test_dir_host):
            shutil.rmtree(test_dir_host)
        os.makedirs(test_dir_host, exist_ok=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] oj download failed: {result.stderr}")
            raise RuntimeError("oj download failed")
        print(result.stdout)

    def submit_via_ojtools(self, args, workdir):
        cmd = self._build_oj_submit_cmd(args)
        result = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
        ok = result.returncode == 0
        if not ok:
            print(f"[ERROR] oj submit failed: {result.stderr}")
            print(f"[ERROR] oj submit stdout: {result.stdout}")
        return ok, result.stdout, result.stderr

# 今後の拡張用
class DockerFileOps(AbstractFileOps):
    def __init__(self, ctl, resource_manager):
        self.ctl = ctl  # ContainerClient等
        self.resource_manager = resource_manager

    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        pass
    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        pass
    def collect_test_cases(self, temp_test_dir):
        pass
    def download_testcases(self, url, test_dir_host):
        cmd = self._build_oj_download_cmd(url, test_dir_host)
        container = self.resource_manager.get_ojtools_container()
        # スケルトン: ctl.exec_in_container(container, cmd) を想定
        result = self.ctl.exec_in_container(container, cmd)
        if result.returncode != 0:
            print(f"[ERROR] oj download failed: {result.stderr}")
            raise RuntimeError("oj download failed")
        print(result.stdout)
    def submit_via_ojtools(self, args, workdir):
        cmd = self._build_oj_submit_cmd(args)
        container = self.resource_manager.get_ojtools_container()
        result = self.ctl.exec_in_container(container, cmd, workdir=workdir)
        ok = result.returncode == 0
        if not ok:
            print(f"[ERROR] oj submit failed: {result.stderr}")
            print(f"[ERROR] oj submit stdout: {result.stdout}")
        return ok, result.stdout, result.stderr

class CloudFileOps(AbstractFileOps):
    def prepare_source_code(self, contest_name, problem_name, language_name, upm, language_config, env_config):
        pass
    def prepare_test_cases(self, contest_name, problem_name, upm, env_config):
        pass
    def collect_test_cases(self, temp_test_dir):
        pass
    def download_testcases(self, url, test_dir_host):
        pass
    def submit_via_ojtools(self, args, workdir):
        pass 