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
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_source = os.path.join(self.temp_dir, "main.py")
        if not os.path.exists(self.source_path):
            print(f"[エラー] ソースファイルが存在しません: {self.source_path}")
            return False
        try:
            shutil.copy2(self.source_path, self.temp_source)
        except Exception as e:
            print(f"[エラー] main.pyのコピーに失敗しました: {e}")
            return False
        if not os.path.exists(self.temp_source):
            print(f"[エラー] コピー後に {self.temp_source} が存在しません")
            return False
        return True

    async def run(self, input_path=None):
        temp_container = f"py-tmp-{os.getpid()}"
        # 1. 一時コンテナ起動
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, self.docker_image(), "sleep", "300"
        ], check=True)
        try:
            # 2. main.py送信
            subprocess.run(["docker", "cp", self.temp_source, f"{temp_container}:/workspace/main.py"], check=True)
            # 3. inputファイル送信（あれば）
            input_cont = None
            if input_path:
                input_cont = "/workspace/input.txt"
                subprocess.run(["docker", "cp", input_path, f"{temp_container}:{input_cont}"], check=True)
            # 4. 実行
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
        os.makedirs(self.temp_dir, exist_ok=True)
        output_path = os.path.join(self.temp_dir, "a.out")
        cmd = ["rustc", self.source_path, "-o", "a.out"]
        image = "rust"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/work_temp"
        }
        workdir = "/workspace/work_temp"
        result = await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir
        )
        self.binary_path = output_path
        return result[0] == 0

    async def run(self, input_path=None):
        cmd = ["./a.out"]
        image = "rust"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/work_temp"
        }
        workdir = "/workspace/work_temp"
        return await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir, input_path=input_path
        ) 