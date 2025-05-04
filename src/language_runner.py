from abc import ABC, abstractmethod
import os
import shutil

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
        shutil.copy2(self.source_path, self.temp_source)
        return True

    async def run(self, input_path=None):
        cmd = ["python3", "main.py"]
        image = "python-oj-image"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/.temp"
        }
        workdir = "/workspace/.temp"
        return await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir, input_path=input_path
        )

class PypyRunner(PythonRunner):
    async def run(self, input_path=None):
        cmd = ["pypy3", "main.py"]
        image = "pypy-oj-image"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/.temp"
        }
        workdir = "/workspace/.temp"
        return await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir, input_path=input_path
        )

class RustRunner(LanguageRunner):
    async def build(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        output_path = os.path.join(self.temp_dir, "a.out")
        cmd = ["rustc", self.source_path, "-o", "a.out"]
        image = "rust-oj-image"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/.temp"
        }
        workdir = "/workspace/.temp"
        result = await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir
        )
        self.binary_path = output_path
        return result[0] == 0

    async def run(self, input_path=None):
        cmd = ["./a.out"]
        image = "rust-oj-image"
        volumes = {
            os.path.abspath(self.temp_dir): "/workspace/.temp"
        }
        workdir = "/workspace/.temp"
        return await self.docker_operator.run(
            image, cmd, volumes=volumes, workdir=workdir, input_path=input_path
        ) 