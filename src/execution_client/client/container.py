from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable
import json
from src.shell_process import ShellProcess, ShellProcessOptions

class ContainerClient():
    def __init__(self):
        pass

    def run_container(self, name: str, image: str, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, env: Optional[Dict[str, str]] = None, ports: Optional[Dict[int, int]] = None, cpus: Optional[float] = None, memory: Optional[str] = None, cwd: Optional[str] = None, timeout: Optional[float] = None) -> str:
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
        if cwd:
            cmd += ["-w", cwd]
        cmd.append(image)
        if command:
            cmd += command
        else:
            cmd += ["tail", "-f", "/dev/null"]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return proc.stdout.strip() if proc.stdout else ""
        else:
            raise RuntimeError(f"docker run failed: {proc.stderr}")

    def stop_container(self, name: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "stop", name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return True
        else:
            err = proc.stderr if proc.stderr is not None else ""
            if proc.exception:
                raise RuntimeError(f"docker stop failed: exception={proc.exception}, returncode={proc.returncode}, stdout={proc.stdout!r}, stderr={err!r}")
            raise RuntimeError(f"docker stop failed: returncode={proc.returncode}, stdout={proc.stdout!r}, stderr={err!r}")

    def remove_container(self, name: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "rm", "-f", name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return True
        else:
            err = proc.stderr if proc.stderr is not None else ""
            if proc.exception:
                raise RuntimeError(f"docker rm failed: exception={proc.exception}, returncode={proc.returncode}, stdout={proc.stdout!r}, stderr={err!r}")
            raise RuntimeError(f"docker rm failed: returncode={proc.returncode}, stdout={proc.stdout!r}, stderr={err!r}")

    def exec_in_container(self, name: str, cmd_list: List[str], realtime: bool = False, stdin: str = None, cwd: str = None, on_stdout=None, on_stderr=None, timeout: Optional[float] = None) -> ShellProcess:
        cmd = ["docker", "exec", "-i"]
        if cwd:
            cmd += ["-w", cwd]
        cmd.append(name)
        cmd += cmd_list
        opts = ShellProcessOptions(timeout=timeout, input_data=stdin, on_stdout=on_stdout, on_stderr=on_stderr)
        opts.cmd = cmd
        if not realtime:
            proc = ShellProcess.run(options=opts)
            if proc.returncode != 0:
                raise RuntimeError(f"docker exec failed: {proc.stderr}")
            return proc
        else:
            proc = ShellProcess.popen(options=opts)
            if proc.returncode != 0:
                raise RuntimeError(f"docker exec (realtime) failed: {proc.stderr}")
            return proc

    def copy_to_container(self, name: str, src_path: str, dst_path: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "cp", src_path, f"{name}:{dst_path}"]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return True
        else:
            raise RuntimeError(f"docker cp to container failed: {proc.stderr}")

    def copy_from_container(self, name: str, src_path: str, dst_path: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "cp", f"{name}:{src_path}", dst_path]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return True
        else:
            raise RuntimeError(f"docker cp from container failed: {proc.stderr}")

    def is_container_running(self, name: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "inspect", "-f", "{{.State.Running}}", name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode != 0:
            return False
        return proc.stdout.strip() == "true" if proc.stdout else False

    def list_containers(self, all: bool = True, prefix: Optional[str] = None, timeout: Optional[float] = None) -> List[str]:
        cmd = ["docker", "ps", "-a" if all else "", "--format", "{{.Names}}"]
        cmd = [c for c in cmd if c]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        try:
            proc = ShellProcess.run(options=opts)
            if proc.returncode != 0:
                print(f"[ERROR] docker ps failed: {proc.stderr}")
                return []
            names = proc.stdout.splitlines() if proc.stdout else []
            if prefix:
                names = [n for n in names if n.startswith(prefix)]
            return names
        except Exception as e:
            print(f"[ERROR] docker ps error: {e}")
            return []

    def inspect_container(self, name: str, timeout: Optional[float] = None) -> Optional[dict]:
        cmd = ["docker", "inspect", name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        try:
            proc = ShellProcess.run(options=opts)
            if proc.returncode == 0 and proc.stdout:
                return json.loads(proc.stdout)[0]
            else:
                print(f"[ERROR] docker inspect failed: {proc.stderr}")
                return None
        except Exception as e:
            print(f"[ERROR] docker inspect timed out for {name}: {e}")
            return None

    def inspect_image(self, image_name: str, timeout: Optional[float] = None) -> Optional[dict]:
        cmd = ["docker", "inspect", image_name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        try:
            proc = ShellProcess.run(options=opts)
            if proc.returncode == 0 and proc.stdout:
                return json.loads(proc.stdout)[0]
            else:
                print(f"[ERROR] docker inspect image failed: {proc.stderr}")
                return None
        except Exception as e:
            print(f"[ERROR] docker inspect image timed out for {image_name}: {e}")
            return None

    def get_container_logs(self, name: str, tail: Optional[int] = None, timeout: Optional[float] = None) -> str:
        cmd = ["docker", "logs"]
        if tail is not None:
            cmd += ["--tail", str(tail)]
        cmd.append(name)
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode == 0:
            return proc.stdout if proc.stdout else ""
        else:
            raise RuntimeError(f"docker logs failed: {proc.stderr}")

    def container_exists(self, name: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode != 0:
            return False
        names = proc.stdout.splitlines() if proc.stdout else []
        return name in names

    def image_exists(self, image_name: str, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "images", "--format", "{{.Repository}}"]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        if proc.returncode != 0:
            return False
        images = proc.stdout.splitlines() if proc.stdout else []
        return image_name in images

    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, cwd: Optional[str] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        if not realtime:
            return self.run_container(name, image, command, volumes, detach, cwd=cwd, timeout=timeout)
        else:
            cmd = ["docker", "run", "--rm", "--name", name]
            if volumes:
                for host_path, cont_path in volumes.items():
                    cmd += ["-v", f"{host_path}:{cont_path}"]
            if cwd:
                cmd += ["-w", cwd]
            cmd.append(image)
            if command:
                cmd += command
            opts = ShellProcessOptions(timeout=timeout, on_stdout=on_stdout, on_stderr=on_stderr)
            opts.cmd = cmd
            proc = ShellProcess.popen(options=opts)
            return proc

    def stop(self, name: str, timeout: Optional[float] = None) -> bool:
        return self.stop_container(name, timeout=timeout)

    def remove(self, name: str, timeout: Optional[float] = None) -> bool:
        return self.remove_container(name, timeout=timeout)

    def exec_in(self, name: str, cmd: List[str], realtime: bool = False, on_stdout: Optional[Callable[[str], None]] = None, on_stderr: Optional[Callable[[str], None]] = None, timeout: Optional[float] = None, **kwargs) -> ShellProcess:
        return self.exec_in_container(name, cmd, realtime=realtime, on_stdout=on_stdout, on_stderr=on_stderr, timeout=timeout, **kwargs)

    def is_running(self, name: str, timeout: Optional[float] = None) -> bool:
        return self.is_container_running(name, timeout=timeout)

    def list(self, all: bool = True, prefix: Optional[str] = None, timeout: Optional[float] = None) -> List[str]:
        return self.list_containers(all=all, prefix=prefix, timeout=timeout)

    def start_container(self, name: str, image: str = None, opts: dict = None, timeout: Optional[float] = None) -> bool:
        cmd = ["docker", "start", name]
        opts = ShellProcessOptions(timeout=timeout)
        opts.cmd = cmd
        proc = ShellProcess.run(options=opts)
        return proc.returncode == 0

    def build(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, timeout: Optional[float] = None, **kwargs) -> Any:
        if not command:
            raise ValueError("build command must be specified for container execution")
        if not self.container_exists(name, timeout=timeout):
            self.run_container(name, image, detach=True, volumes=volumes, timeout=timeout)
        proc = self.exec_in_container(name, command, timeout=timeout, **kwargs)
        return proc 