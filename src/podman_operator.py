from abc import ABC, abstractmethod
import asyncio
import sys
import os

class DockerOperator(ABC):
    @abstractmethod
    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None, input_path: str = None, interactive: bool = False):
        pass

    @abstractmethod
    async def build(self, dockerfile: str, tag: str):
        pass

    @abstractmethod
    async def exec(self, container: str, command: list):
        pass

    async def run_oj(self, oj_args: list, volumes: dict, workdir: str, interactive: bool = False):
        """ojtコマンドをdocker経由で実行する。interactive=Trueなら端末接続・標準入力も渡す"""
        image = "python-oj-image"  # 必要に応じて外部から指定可能に
        cmd = ["oj"] + oj_args
        return await self.run(image, cmd, volumes, workdir, interactive=interactive)

class LocalDockerOperator(DockerOperator):
    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None, input_path: str = None, interactive: bool = False):
        cmd = ["docker", "run", "--rm", "-i"]
        cmd += ["--user", f"{os.getuid()}:{os.getgid()}"]
        cmd += ["-e", "HOME=/workspace"]
        if interactive:
            cmd.append("-t")  # 擬似端末割り当て
        if volumes:
            for host, cont in volumes.items():
                cmd += ["-v", f"{host}:{cont}"]
        if workdir:
            cmd += ["-w", workdir]
        cmd.append(image)
        cmd += command
        print("[DEBUG] 実行コマンド:", cmd)  # デバッグ出力
        if interactive:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            await proc.wait()
            return proc.returncode, None, None
        else:
            if input_path:
                with open(input_path, "rb") as f:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=f,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
            else:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
            return proc.returncode, stdout.decode(), stderr.decode()

    async def build(self, dockerfile: str, tag: str):
        cmd = ["docker", "build", "-f", dockerfile, "-t", tag, "."]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def exec(self, container: str, command: list):
        cmd = ["docker", "exec", container] + command
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def run_oj(self, oj_args: list, volumes: dict, workdir: str, interactive: bool = False):
        image = "python-oj-image"
        cmd = ["oj"] + oj_args
        return await self.run(image, cmd, volumes, workdir, interactive=interactive)

class MockDockerOperator(DockerOperator):
    def __init__(self):
        self.calls = []

    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None, input_path: str = None, interactive: bool = False):
        self.calls.append(('run', image, command, volumes, workdir, input_path, interactive))
        return 0, 'mock-stdout', 'mock-stderr'

    async def build(self, dockerfile: str, tag: str):
        self.calls.append(('build', dockerfile, tag))
        return 0, 'mock-stdout', 'mock-stderr'

    async def exec(self, container: str, command: list):
        self.calls.append(('exec', container, command))
        return 0, 'mock-stdout', 'mock-stderr'

    async def run_oj(self, oj_args: list, volumes: dict, workdir: str, interactive: bool = False):
        self.calls.append(('run_oj', oj_args, volumes, workdir, interactive))
        return 0, 'mock-stdout', 'mock-stderr' 