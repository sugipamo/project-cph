from abc import ABC, abstractmethod
import os
import shutil
import subprocess
import pathlib
import time
import asyncio
import uuid

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

    @abstractmethod
    def docker_image(self):
        pass

    @abstractmethod
    def run_cmd(self):
        pass

    @property
    def container_prefix(self):
        return "lang-tmp-"

    async def run(self, input_path=None):
        import asyncio, time, uuid, os
        host_temp_dir = getattr(self, '_host_temp_dir', None)
        file_name = os.path.basename(self.source_path)
        temp_container = f"{self.container_prefix}{os.getpid()}-{uuid.uuid4().hex[:8]}"
        docker_run_cmd = [
            "docker", "run", "-d", "--name", temp_container
        ]
        if host_temp_dir:
            docker_run_cmd += ["-v", f"{host_temp_dir}:/workspace/.temp:ro"]
        docker_run_cmd += [self.docker_image(), "sleep", "300"]
        try:
            proc = await asyncio.create_subprocess_exec(*docker_run_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print(f"[エラー] docker run失敗: {stderr.decode().strip()}")
                return False
        except Exception as e:
            print(f"[エラー] docker run失敗: {e}")
            return False
        try:
            main_path = f"/workspace/.temp/{file_name}"
            input_cont = None
            if input_path:
                input_file_name = os.path.basename(input_path)
                input_cont = f"/workspace/.temp/test/{input_file_name}" if "/test/" in input_path else f"/workspace/.temp/{input_file_name}"
            cmd = [self.run_cmd(), main_path]
            start = time.monotonic()
            if input_cont:
                exec_cmd = f"{cmd[0]} {cmd[1]} < {input_cont}"
                result = subprocess.run([
                    "docker", "exec", temp_container, "sh", "-c", exec_cmd
                ], capture_output=True)
            else:
                result = subprocess.run([
                    "docker", "exec", temp_container, cmd[0], cmd[1]], capture_output=True)
            elapsed = time.monotonic() - start
            return result.returncode, result.stdout.decode(), result.stderr.decode(), elapsed
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

class PythonRunner(LanguageRunner):
    async def build(self):
        # ソースファイルの存在確認のみ
        if not os.path.exists(self.source_path):
            print(f"[エラー] ソースファイルが存在しません: {self.source_path}")
            return False
        self.temp_source = self.source_path  # 直接使う
        return True
    def docker_image(self):
        return "python"
    def run_cmd(self):
        return "python3"
    @property
    def container_prefix(self):
        return "py-tmp-"

class PypyRunner(PythonRunner):
    def docker_image(self):
        return "pypy"
    def run_cmd(self):
        return "pypy3"
    @property
    def container_prefix(self):
        return "pypy-tmp-"

class RustRunner(LanguageRunner):
    async def build(self):
        import pathlib
        host_temp_dir = getattr(self, '_host_temp_dir', None)
        file_name = os.path.basename(self.source_path)
        temp_container = f"rust-tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}"
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
    def docker_image(self):
        return "rust"
    def run_cmd(self):
        return "/workspace/a.out"
    @property
    def container_prefix(self):
        return "rust-tmp-" 