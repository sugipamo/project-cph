import hashlib
import os
from src.shell_process import ShellProcess, ShellProcessOptions



class DockerImageManager():
    def build_image(self) -> bool:
        """
        Dockerfileからイメージをビルドする。
        """
        cmd = [
            "docker", "build", "-f", self.__config.dockerfile_path, "-t", self.__config.image_name, self.__config.workspace_dir
        ]
        opts = ShellProcessOptions()
        proc = ShellProcess.run(*cmd, options=opts)
        return proc.returncode == 0

    def remove_image(self, image_name: str) -> bool:
        """
        イメージを削除する。
        """
        cmd = ["docker", "rmi", image_name]
        opts = ShellProcessOptions()
        proc = ShellProcess.run(*cmd, options=opts)
        if proc.returncode == 0:
            return True
        else:
            print(f"[ERROR] docker rmi failed: {proc.stderr}")
            return False

    def image_exists(self, image_name: str) -> bool:
        """
        イメージが存在するか確認する。
        """
        cmd = ["docker", "images", "--format", "{{.Repository}}", image_name]
        opts = ShellProcessOptions()
        proc = ShellProcess.run(*cmd, options=opts)
        images = proc.stdout.splitlines() if proc.stdout else []
        return image_name in images

    def get_dockerfile_hash(self, dockerfile_path: str) -> str:
        with open(dockerfile_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]

    def get_image_name(self, key):
        # keyは(言語,バージョン)タプル
        lang, ver = key if isinstance(key, tuple) else (key, None)
        dockerfile = self.dockerfile_map.get(key, None)
        if not dockerfile or not os.path.exists(dockerfile):
            return f"{lang}_{ver}"  # fallback
        hashval = self.get_dockerfile_hash(dockerfile)
        return f"cph_image_{lang}_{ver}_{hashval}"

    def cleanup_old_images(self, key: str):
        """
        key: 言語名や用途名
        現在のイメージ以外の同prefixイメージを削除
        """
        prefix = f"cph_image_{key}_"
        current = self.get_image_name(key)
        opts = ShellProcessOptions()
        proc = ShellProcess.run("docker", "images", "--format", "{{.Repository}}", options=opts)
        image_names = proc.stdout.splitlines() if proc.stdout else []
        for img in image_names:
            if img.startswith(prefix) and img != current:
                self.remove_image(img)

    def ensure_image(self, key, context_dir: str = ".") -> str:
        image = self.get_image_name(key)
        opts = ShellProcessOptions()
        ShellProcess.run("docker", "images", "--format", "{{.Repository}}", options=opts)
        return image 