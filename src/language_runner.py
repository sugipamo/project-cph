from abc import ABC, abstractmethod
import os
import shutil
import subprocess
import pathlib

class LanguageRunner(ABC):
    def __init__(self, source_path, temp_dir, docker_operator):
        self.source_path = source_path
        self.temp_dir = temp_dir
        self.docker_operator = docker_operator

    @abstractmethod
    async def build(self):
        """ビルド工程（.tempに成果物を出力）"""
        pass

    @abstractmethod
    async def run(self, input_path=None):
        """ビルド成果物を使って実行"""
        pass

class PythonRunner(LanguageRunner):
    async def build(self):
        # ソースファイルの存在確認のみ
        if not os.path.exists(self.source_path):
            print(f"[エラー] ソースファイルが存在しません: {self.source_path}")
            return False
        self.temp_source = self.source_path  # 直接使う
        return True

    async def run(self, input_path=None):
        import pathlib
        host_temp_dir = getattr(self, '_host_temp_dir', None)
        file_name = os.path.basename(self.source_path)
        temp_container = f"py-tmp-{os.getpid()}"
        docker_run_cmd = [
            "docker", "run", "-d", "--name", temp_container
        ]
        if host_temp_dir:
            docker_run_cmd += ["-v", f"{host_temp_dir}:/workspace/.temp:ro"]
        docker_run_cmd += [self.docker_image(), "sleep", "300"]
        # docker runの出力を抑制し、エラー時はメッセージを出して停止
        try:
            result = subprocess.run(docker_run_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"[エラー] docker run失敗: {e.stderr.decode().strip()}")
            return False
        try:
            # .temp配下を直接参照して実行
            main_path = f"/workspace/.temp/{file_name}"
            input_cont = None
            if input_path:
                input_file_name = os.path.basename(input_path)
                input_cont = f"/workspace/.temp/test/{input_file_name}" if "/test/" in input_path else f"/workspace/.temp/{input_file_name}"
            cmd = [self.run_cmd(), main_path]
            if input_cont:
                exec_cmd = f"{cmd[0]} {cmd[1]} < {input_cont}"
                result = subprocess.run([
                    "docker", "exec", temp_container, "sh", "-c", exec_cmd
                ], capture_output=True)
            else:
                result = subprocess.run([
                    "docker", "exec", temp_container, cmd[0], cmd[1]], capture_output=True)
            return result.returncode, result.stdout.decode(), result.stderr.decode()
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def docker_image(self):
        return "python"
    def run_cmd(self):
        return "python3"

class PypyRunner(PythonRunner):
    def docker_image(self):
        return "pypy"
    def run_cmd(self):
        return "pypy3"

class RustRunner(LanguageRunner):
    async def build(self):
        import pathlib
        host_temp_dir = getattr(self, '_host_temp_dir', None)
        file_name = os.path.basename(self.source_path)
        temp_container = f"rust-tmp-{os.getpid()}"
        docker_run_cmd = [
            "docker", "run", "-d", "--name", temp_container
        ]
        if host_temp_dir:
            docker_run_cmd += ["-v", f"{host_temp_dir}:/workspace/.temp:ro"]
        docker_run_cmd += ["rust", "sleep", "300"]
        # docker runの出力を抑制し、エラー時はメッセージを出して停止
        try:
            result = subprocess.run(docker_run_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"[エラー] docker run失敗: {e.stderr.decode().strip()}")
            return False
        try:
            # .temp配下を直接参照してビルド
            main_path = f"/workspace/.temp/{file_name}"
            result = subprocess.run([
                "docker", "exec", temp_container, "rustc", main_path, "-o", "/workspace/a.out"
            ], capture_output=True)
            if result.returncode != 0:
                print(f"[エラー] rustcビルド失敗: {result.stderr.decode()}")
                return False
            self.binary_path = "/workspace/a.out"
            return True
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    async def run(self, input_path=None):
        import pathlib
        host_temp_dir = getattr(self, '_host_temp_dir', None)
        file_name = os.path.basename(self.source_path)
        temp_container = f"rust-tmp-{os.getpid()}"
        docker_run_cmd = [
            "docker", "run", "-d", "--name", temp_container
        ]
        if host_temp_dir:
            docker_run_cmd += ["-v", f"{host_temp_dir}:/workspace/.temp:ro"]
        docker_run_cmd += ["rust", "sleep", "300"]
        # docker runの出力を抑制し、エラー時はメッセージを出して停止
        try:
            result = subprocess.run(docker_run_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"[エラー] docker run失敗: {e.stderr.decode().strip()}")
            return False
        try:
            # .temp配下を直接参照してビルド・実行
            main_path = f"/workspace/.temp/{file_name}"
            subprocess.run([
                "docker", "exec", temp_container, "rustc", main_path, "-o", "/workspace/a.out"
            ], check=True)
            input_cont = None
            if input_path:
                input_file_name = os.path.basename(input_path)
                input_cont = f"/workspace/.temp/test/{input_file_name}" if "/test/" in input_path else f"/workspace/.temp/{input_file_name}"
            cmd = ["/workspace/a.out"]
            if input_cont:
                exec_cmd = f"{cmd[0]} < {input_cont}"
                result = subprocess.run([
                    "docker", "exec", temp_container, "sh", "-c", exec_cmd
                ], capture_output=True)
            else:
                result = subprocess.run([
                    "docker", "exec", temp_container, cmd[0]], capture_output=True)
            return result.returncode, result.stdout.decode(), result.stderr.decode()
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 