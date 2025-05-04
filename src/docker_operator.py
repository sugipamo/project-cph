from abc import ABC, abstractmethod
import asyncio
import sys
import os
import subprocess

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
        image = "oj"  # 必要に応じて外部から指定可能に
        # まずlsコマンドで.tempディレクトリの中身を表示
        ls_cmd = ["ls", "-l", ".temp"]
        ls_full_cmd = ["docker", "run", "--rm", "-i"]
        ls_full_cmd += ["--user", f"{os.getuid()}:{os.getgid()}"]
        ls_full_cmd += ["-e", "HOME=/workspace"]
        if interactive:
            ls_full_cmd.append("-t")
        if workdir:
            ls_full_cmd += ["-w", workdir]
        ls_full_cmd.append(image)
        ls_full_cmd += ls_cmd
        print("[DEBUG] lsコマンド:", ls_full_cmd)
        proc_ls = await asyncio.create_subprocess_exec(
            *ls_full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_ls, stderr_ls = await proc_ls.communicate()
        print("[DEBUG] .tempディレクトリ内容:\n", stdout_ls.decode(), stderr_ls.decode())
        # その後ojコマンド
        cmd = ["oj"] + oj_args
        return await self.run(image, cmd, volumes, workdir, interactive=interactive)

    def run_oj_download(self, url, cookie_host, test_dir_host):
        """
        oj downloadをdockerコンテナで実行し、成果物（テストケース）とcookieをdocker cpでやりとりする
        url: 問題URL
        cookie_host: ホスト側cookieファイルパス
        test_dir_host: ホスト側テストケース保存ディレクトリ
        """
        temp_container = f"oj-tmp-{os.getpid()}"
        # 1. 一時コンテナ起動
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, "oj", "sleep", "300"
        ], check=True)
        try:
            # 2. cookie送信（存在すれば）
            cookie_cont = "/root/.local/share/online-judge-tools/cookie.jar"
            if cookie_host and os.path.exists(cookie_host):
                # ディレクトリ作成を追加
                subprocess.run([
                    "docker", "exec", temp_container, "mkdir", "-p", "/root/.local/share/online-judge-tools"
                ], check=True)
                subprocess.run(["docker", "cp", cookie_host, f"{temp_container}:{cookie_cont}"], check=True)
            # 3. .tempディレクトリ作成
            subprocess.run([
                "docker", "exec", temp_container, "mkdir", "-p", "/workspace/.temp"
            ], check=True)
            # 4. oj download実行（.tempで）
            try:
                subprocess.run([
                    "docker", "exec", temp_container, "sh", "-c", f"cd /workspace/.temp && oj download {url}"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[エラー] oj download失敗: {e}")
                return False
            # 5. テストケース回収
            test_dir_cont = "/workspace/.temp/test"
            os.makedirs(test_dir_host, exist_ok=True)
            result = subprocess.run(["docker", "exec", temp_container, "test", "-d", test_dir_cont])
            if result.returncode == 0:
                try:
                    # testディレクトリの中身だけをコピー
                    subprocess.run(["docker", "cp", f"{temp_container}:{test_dir_cont}/.", test_dir_host], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[エラー] docker cp失敗: {e}")
            else:
                print(f"[警告] テストケースディレクトリが見つかりません: {test_dir_cont}")
            # 6. cookie回収
            if cookie_host and os.path.exists(cookie_host):
                try:
                    subprocess.run(["docker", "cp", f"{temp_container}:{cookie_cont}", cookie_host], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[エラー] cookie回収失敗: {e}")
            return True
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False)

    def run_oj_login(self, login_url, cookie_host):
        import subprocess
        import os
        temp_container = f"oj-login-{os.getpid()}"
        # 1. 一時コンテナ起動（-itで対話型）
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, "oj", "sleep", "300"
        ], check=True)
        try:
            # 2. cookie送信（存在すれば）
            cookie_cont = "/root/.local/share/online-judge-tools/cookie.jar"
            if cookie_host and os.path.exists(cookie_host):
                # ディレクトリ作成を追加
                subprocess.run([
                    "docker", "exec", temp_container, "mkdir", "-p", "/root/.local/share/online-judge-tools"
                ], check=True)
                subprocess.run(["docker", "cp", cookie_host, f"{temp_container}:{cookie_cont}"], check=True)
            # 3. oj login実行（-itで端末接続）
            subprocess.run([
                "docker", "exec", "-it", temp_container, "oj", "login", login_url
            ])
            # 4. cookie回収
            if cookie_host:
                try:
                    subprocess.run(["docker", "cp", f"{temp_container}:{cookie_cont}", cookie_host], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[エラー] cookie回収失敗: {e}")
            return True
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False)

    def run_oj_submit(self, url, file_path, cookie_host):
        import subprocess
        import os
        temp_container = f"oj-submit-{os.getpid()}"
        # 1. 一時コンテナ起動
        subprocess.run([
            "docker", "run", "-d", "--name", temp_container, "oj", "sleep", "300"
        ], check=True)
        try:
            # 2. cookie送信（存在すれば）
            cookie_cont = "/root/.local/share/online-judge-tools/cookie.jar"
            if cookie_host and os.path.exists(cookie_host):
                # ディレクトリ作成を追加
                subprocess.run([
                    "docker", "exec", temp_container, "mkdir", "-p", "/root/.local/share/online-judge-tools"
                ], check=True)
                subprocess.run(["docker", "cp", cookie_host, f"{temp_container}:{cookie_cont}"], check=True)
            # 3. 提出ファイル送信
            submit_cont = f"/workspace/{os.path.basename(file_path)}"
            subprocess.run(["docker", "cp", file_path, f"{temp_container}:{submit_cont}"], check=True)
            # 4. oj submit実行
            try:
                subprocess.run([
                    "docker", "exec", temp_container, "oj", "submit", url, submit_cont, "--yes"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[エラー] oj submit失敗: {e}")
                return False
            # 5. cookie回収
            if cookie_host:
                try:
                    subprocess.run(["docker", "cp", f"{temp_container}:{cookie_cont}", cookie_host], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"[エラー] cookie回収失敗: {e}")
            return True
        finally:
            subprocess.run(["docker", "rm", "-f", temp_container], check=False)

class LocalDockerOperator(DockerOperator):
    async def run(self, image: str, command: list, volumes: dict = None, workdir: str = None, input_path: str = None, interactive: bool = False):
        cmd = ["docker", "run", "--rm", "-i"]
        cmd += ["--user", f"{os.getuid()}:{os.getgid()}"]
        cmd += ["-e", "HOME=/workspace"]
        # volumesをマウント
        if volumes:
            for host_path, cont_path in volumes.items():
                cmd += ["-v", f"{os.path.abspath(host_path)}:{cont_path}"]
        if interactive:
            cmd.append("-t")  # 擬似端末割り当て
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
        image = "oj"
        # まずlsコマンドで.tempディレクトリの中身を表示
        ls_cmd = ["ls", "-l", ".temp"]
        ls_full_cmd = ["docker", "run", "--rm", "-i"]
        ls_full_cmd += ["--user", f"{os.getuid()}:{os.getgid()}"]
        ls_full_cmd += ["-e", "HOME=/workspace"]
        if interactive:
            ls_full_cmd.append("-t")
        if workdir:
            ls_full_cmd += ["-w", workdir]
        ls_full_cmd.append(image)
        ls_full_cmd += ls_cmd
        print("[DEBUG] lsコマンド:", ls_full_cmd)
        proc_ls = await asyncio.create_subprocess_exec(
            *ls_full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_ls, stderr_ls = await proc_ls.communicate()
        print("[DEBUG] .tempディレクトリ内容:\n", stdout_ls.decode(), stderr_ls.decode())
        # その後ojコマンド
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

    def run_oj_download(self, url, cookie_host, test_dir_host):
        self.calls.append(('run_oj_download', url, cookie_host, test_dir_host))
        return True 