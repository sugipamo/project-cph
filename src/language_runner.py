from abc import ABC, abstractmethod
import os
import shutil
import subprocess

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
        # self.temp_dirは使わず、ソースファイルの存在確認のみ
        if not os.path.exists(self.source_path):
            print(f"[エラー] ソースファイルが存在しません: {self.source_path}")
            return False
        self.temp_source = self.source_path  # 直接使う
        return True

    async def run(self, input_path=None):
        temp_container = f"py-tmp-{os.getpid()}"
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, self.docker_image(), "sleep", "300"
        ], check=True)
        try:
            # main.py送信
            subprocess.run(["docker", "cp", self.source_path, f"{temp_container}:/workspace/main.py"], check=True)
            input_cont = None
            if input_path:
                input_cont = "/workspace/input.txt"
                subprocess.run(["docker", "cp", input_path, f"{temp_container}:{input_cont}"], check=True)
            cmd = [self.run_cmd(), "/workspace/main.py"]
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
            subprocess.run(["docker", "rm", "-f", temp_container], check=False)

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
        # self.temp_dirは使わず、ビルドはコンテナ内で完結
        temp_container = f"rust-tmp-{os.getpid()}"
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, "rust", "sleep", "300"
        ], check=True)
        try:
            # main.rs送信
            subprocess.run(["docker", "cp", self.source_path, f"{temp_container}:/workspace/main.rs"], check=True)
            # rustcでビルド
            result = subprocess.run([
                "docker", "exec", temp_container, "rustc", "/workspace/main.rs", "-o", "/workspace/a.out"
            ], capture_output=True)
            if result.returncode != 0:
                print(f"[エラー] rustcビルド失敗: {result.stderr.decode()}")
                return False
            self.binary_path = "/workspace/a.out"
            # a.outをホストにコピーしたい場合はここでdocker cp可能
            return True
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False)

    async def run(self, input_path=None):
        temp_container = f"rust-tmp-{os.getpid()}"
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, "rust", "sleep", "300"
        ], check=True)
        try:
            # a.out送信
            subprocess.run(["docker", "cp", self.source_path, f"{temp_container}:/workspace/main.rs"], check=True)
            subprocess.run([
                "docker", "exec", temp_container, "rustc", "/workspace/main.rs", "-o", "/workspace/a.out"
            ], check=True)
            input_cont = None
            if input_path:
                input_cont = "/workspace/input.txt"
                subprocess.run(["docker", "cp", input_path, f"{temp_container}:{input_cont}"], check=True)
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
            subprocess.run(["docker", "rm", "-f", temp_container], check=False) 