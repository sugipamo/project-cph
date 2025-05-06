import subprocess
import json

class DockerCtl:
    def __init__(self, timeout=30):
        self.timeout = timeout

    def list_cph_containers(self):
        try:
            # まず全てのcph_コンテナ名を取得
            result = subprocess.run([
                "docker", "ps", "-a", "--format", "{{.Names}}"
            ], capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker ps failed: {result.stderr}")
                return []
            all_cph = [name for name in result.stdout.splitlines() if name.startswith("cph_")]
            # それぞれの状態をinspectで確認し、Runningのみ返す
            running_cph = []
            for name in all_cph:
                inspect = subprocess.run([
                    "docker", "inspect", "-f", "{{.State.Running}}", name
                ], capture_output=True, text=True, timeout=self.timeout)
                if inspect.returncode == 0 and inspect.stdout.strip() == "true":
                    running_cph.append(name)
            return running_cph
        except subprocess.TimeoutExpired:
            print("[ERROR] docker ps timed out")
            return []

    def start_container(self, name, image, volumes=None):
        try:
            # 新規起動のみ（既存コンテナの削除は行わない）
            cmd = [
                "docker", "run", "-d", "--name", name
            ]
            if volumes:
                print(f"[DEBUG] volumes: {volumes}")
                for host_path, cont_path in volumes.items():
                    cmd += ["-v", f"{host_path}:{cont_path}"]
            cmd += [image, "tail", "-f", "/dev/null"]
            print(f"[DEBUG] docker run cmd: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker run failed: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            print("[ERROR] docker run timed out")
            return False

    def remove_container(self, name):
        try:
            result = subprocess.run([
                "docker", "rm", "-f", name], capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker rm failed: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            print("[ERROR] docker rm timed out")
            return False

    def exec_in_container(self, name, cmd):
        try:
            result = subprocess.run([
                "docker", "exec", name
            ] + cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker exec failed: {result.stderr}")
                return False, result.stdout, result.stderr
            return True, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print("[ERROR] docker exec timed out")
            return False, "", "timeout"

    def is_container_running(self, name):
        try:
            result = subprocess.run([
                "docker", "inspect", "-f", "{{.State.Running}}", name
            ], capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                return False
            return result.stdout.strip() == "true"
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker inspect timed out for {name}")
            return False

    def cp_from_container(self, container_name, src_path, dst_path):
        try:
            result = subprocess.run([
                "docker", "cp", f"{container_name}:{src_path}", dst_path
            ], capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                print(f"[ERROR] docker cp failed: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            print(f"[ERROR] docker cp timed out for {container_name}")
            return False 