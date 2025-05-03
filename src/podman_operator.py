from abc import ABC, abstractmethod
import asyncio

class PodmanOperator(ABC):
    @abstractmethod
    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None):
        pass

    @abstractmethod
    async def build(self, dockerfile: str, tag: str):
        pass

    @abstractmethod
    async def exec(self, container: str, command: list):
        pass

class LocalPodmanOperator(PodmanOperator):
    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None):
        cmd = ["podman", "run", "--rm", "-i"]
        if volumes:
            for host, cont in volumes.items():
                cmd += ["-v", f"{host}:{cont}"]
        if workdir:
            cmd += ["-w", workdir]
        cmd.append(image)
        cmd += command
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def build(self, dockerfile: str, tag: str):
        cmd = ["podman", "build", "-f", dockerfile, "-t", tag, "."]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

    async def exec(self, container: str, command: list):
        cmd = ["podman", "exec", container] + command
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()

class MockPodmanOperator(PodmanOperator):
    def __init__(self):
        self.calls = []

    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None):
        self.calls.append(('run', image, command, volumes, workdir))
        return 0, 'mock-stdout', 'mock-stderr'

    async def build(self, dockerfile: str, tag: str):
        self.calls.append(('build', dockerfile, tag))
        return 0, 'mock-stdout', 'mock-stderr'

    async def exec(self, container: str, command: list):
        self.calls.append(('exec', container, command))
        return 0, 'mock-stdout', 'mock-stderr' 