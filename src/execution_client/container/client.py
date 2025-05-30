from abc import ABC, abstractmethod
import subprocess
from typing import Optional, List, Dict, Any, Callable
import json
from execution_client.abstract_client import AbstractExecutionClient
from execution_client.types import ExecutionResult
import threading

class AbstractContainerClient(ABC):
    @abstractmethod
    def run_container(self, name: str, image: str, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True) -> str:
        pass

    @abstractmethod
    def stop_container(self, name: str) -> bool:
        pass

    @abstractmethod
    def remove_container(self, name: str) -> bool:
        pass

    @abstractmethod
    def exec_in_container(self, name: str, cmd: List[str]) -> subprocess.CompletedProcess:
        pass

    @abstractmethod
    def copy_to_container(self, name: str, src_path: str, dst_path: str) -> bool:
        pass

    @abstractmethod
    def copy_from_container(self, name: str, src_path: str, dst_path: str) -> bool:
        pass

class ContainerClient(AbstractExecutionClient, AbstractContainerClient):
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def run_container(self, name: str, image: str, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, env: Optional[Dict[str, str]] = None, ports: Optional[Dict[int, int]] = None, cpus: Optional[float] = None, memory: Optional[str] = None) -> str:
        cmd = ["docker", "run"]
        if detach:
            cmd.append("-d")
        cmd += ["--name", name]
        if volumes:
            for host_path, cont_path in volumes.items():
                cmd += ["-v", f"{host_path}:{cont_path}"]
        if env:
            for k, v in env.items():
                cmd += ["-e", f"{k}={v}"]
        if ports:
            for host_port, cont_port in ports.items():
                cmd += ["-p", f"{host_port}:{cont_port}"]
        if cpus:
            cmd += ["--cpus", str(cpus)]
        if memory:
            cmd += ["--memory", memory]
        cmd.append(image)
        if command:
            cmd += command
        else:
            cmd += ["tail", "-f", "/dev/null"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[ERROR] docker run failed: {result.stderr}")
                return ""
        except subprocess.TimeoutExpired:
            print("[ERROR] docker run timed out")
            return ""

    def stop_container(self, name: str) -> bool:
        cmd = ["docker", "stop", name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return True
            else:
                print(f"[ERROR] docker stop failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] docker stop timed out")
            return False

    def remove_container(self, name: str) -> bool:
        cmd = ["docker", "rm", "-f", name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return True
            else:
                print(f"[ERROR] docker rm failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] docker rm timed out")
            return False

    def exec_in_container(self, name: str, cmd_list: List[str], realtime: bool = False, stdin: str = None) -> subprocess.CompletedProcess:
        cmd = ["docker", "exec", "-i", name] + cmd_list
        if not realtime:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout, input=stdin)
                if result.returncode != 0:
                    print(f"[ERROR] docker exec failed: {result.stderr}")
                return result
            except subprocess.TimeoutExpired:
                print("[ERROR] docker exec timed out")
                return subprocess.CompletedProcess(cmd, 1, '', 'timeout')
        else:
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, stdin=subprocess.PIPE)
                output = ""
                if stdin is not None:
                    proc.stdin.write(stdin)
                    proc.stdin.close()
                try:
                    for line in proc.stdout:
                        output += line
                except Exception:
                    pass
                proc.wait(timeout=self.timeout)
                if proc.returncode != 0:
                    print(f"[ERROR] docker exec (realtime) failed: {output}")
                return subprocess.CompletedProcess(cmd, proc.returncode, output, output if proc.returncode != 0 else "")
            except subprocess.TimeoutExpired:
                print("[ERROR] docker exec (realtime) timed out")
                return subprocess.CompletedProcess(cmd, 1, '', 'timeout')

    def copy_to_container(self, name: str, src_path: str, dst_path: str) -> bool:
        cmd = ["docker", "cp", src_path, f"{name}:{dst_path}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return True
            else:
                print(f"[ERROR] docker cp to container failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] docker cp to container timed out")
            return False

    def copy_from_container(self, name: str, src_path: str, dst_path: str) -> bool:
        cmd = ["docker", "cp", f"{name}:{src_path}", dst_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return True
            else:
                print(f"[ERROR] docker cp from container failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("[ERROR] docker cp from container timed out")
            return False

    def is_container_running(self, name: str) -> bool:
        cmd = ["docker", "inspect", "-f", "{{.State.Running}}", name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                return False
            return result.stdout.strip() == "true"
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker inspect timed out for {name}")
            return False

    def list_containers(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        cmd = ["docker", "ps", "-a" if all else "", "--format", "{{.Names}}"]
        cmd = [c for c in cmd if c]  # 空文字列を除去
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker ps failed: {result.stderr}")
                return []
            names = result.stdout.splitlines()
            if prefix:
                names = [n for n in names if n.startswith(prefix)]
            return names
        except subprocess.TimeoutExpired:
            print("[ERROR] docker ps timed out")
            return []

    def inspect_container(self, name: str) -> Optional[dict]:
        cmd = ["docker", "inspect", name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return json.loads(result.stdout)[0]
            else:
                print(f"[ERROR] docker inspect failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker inspect timed out for {name}")
            return None

    def inspect_image(self, image_name: str) -> Optional[dict]:
        cmd = ["docker", "inspect", image_name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return json.loads(result.stdout)[0]
            else:
                print(f"[ERROR] docker inspect image failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker inspect image timed out for {image_name}")
            return None

    def get_container_logs(self, name: str, tail: Optional[int] = None) -> str:
        cmd = ["docker", "logs"]
        if tail is not None:
            cmd += ["--tail", str(tail)]
        cmd.append(name)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"[ERROR] docker logs failed: {result.stderr}")
                return ""
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker logs timed out for {name}")
            return ""

    def container_exists(self, name: str) -> bool:
        cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                return False
            names = result.stdout.splitlines()
            return name in names
        except subprocess.TimeoutExpired:
            print("[ERROR] docker ps timed out")
            return False

    def image_exists(self, image_name: str) -> bool:
        cmd = ["docker", "images", "--format", "{{.Repository}}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                return False
            images = result.stdout.splitlines()
            return image_name in images
        except subprocess.TimeoutExpired:
            print("[ERROR] docker images timed out")
            return False

    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> Any:
        if not realtime:
            result = self.run_container(name, image, command, volumes, detach)
            return ExecutionResult(returncode=None, stdout=None, stderr=None, extra={"popen": None, "docker_result": result})
        else:
            # docker runのリアルタイム出力取得
            cmd = ["docker", "run", "--rm", "--name", name]
            if volumes:
                for host_path, cont_path in volumes.items():
                    cmd += ["-v", f"{host_path}:{cont_path}"]
            cmd.append(image)
            if command:
                cmd += command
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            def reader(stream, callback):
                for line in iter(stream.readline, ''):
                    if callback:
                        callback(line)
            t_out = threading.Thread(target=reader, args=(proc.stdout, on_stdout))
            t_err = threading.Thread(target=reader, args=(proc.stderr, on_stderr))
            t_out.daemon = True
            t_err.daemon = True
            t_out.start()
            t_err.start()
            return ExecutionResult(returncode=None, stdout=None, stderr=None, extra={"popen": proc})

    def stop(self, name: str) -> bool:
        return self.stop_container(name)

    def remove(self, name: str) -> bool:
        return self.remove_container(name)

    def exec_in(self, name: str, cmd: List[str], realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, **kwargs) -> subprocess.CompletedProcess:
        if not realtime:
            return self.exec_in_container(name, cmd, **kwargs)
        else:
            # docker execのリアルタイム出力取得
            full_cmd = ["docker", "exec", name] + cmd
            proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            def reader(stream, callback):
                for line in iter(stream.readline, ''):
                    if callback:
                        callback(line)
            t_out = threading.Thread(target=reader, args=(proc.stdout, on_stdout))
            t_err = threading.Thread(target=reader, args=(proc.stderr, on_stderr))
            t_out.daemon = True
            t_err.daemon = True
            t_out.start()
            t_err.start()
            return ExecutionResult(returncode=None, stdout=None, stderr=None, extra={"popen": proc})

    def is_running(self, name: str) -> bool:
        return self.is_container_running(name)

    def list(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        return self.list_containers(all=all, prefix=prefix)

    def start_container(self, name: str, image: str = None, opts: dict = None) -> bool:
        cmd = ["docker", "start", name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("[ERROR] docker start timed out")
            return False 