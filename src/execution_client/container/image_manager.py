import subprocess
from typing import Optional, Dict
import hashlib
import os


class DockerImageConfig():
    def __init__(self, contest_env):
        self.__contest_env = contest_env

    @property
    def dockerfile_path(self):
        return os.path.abspath(self.__contest_env.dockerfile_path)

    @property
    def image_name(self):
        with open(self.dockerfile_path, "rb") as f:
            hashval = hashlib.sha256(f.read()).hexdigest()[:12]
        return self.__contest_env.language_name + "_" + hashval
    
    @property
    def workspace_dir(self):
        return os.path.abspath(self.__contest_env.workspace_dir)

class DockerImageManager():
    def __init__(self, config: DockerImageConfig):
        self.__config = config

    def build_image(self) -> bool:
        """
        Dockerfileからイメージをビルドする。
        """
        cmd = [
            "docker", "build", "-f", self.__config.dockerfile_path, "-t", self.__config.image_name, self.__config.workspace_dir
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        

    def remove_image(self, image_name: str) -> bool:
        """
        イメージを削除する。
        """
        cmd = ["docker", "rmi", image_name]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] docker rmi failed: {e.stderr}")
            return False

    def image_exists(self, image_name: str) -> bool:
        """
        イメージが存在するか確認する。
        """
        cmd = ["docker", "images", "--format", "{{.Repository}}", image_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        images = result.stdout.splitlines()
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
        images = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
        image_names = images.stdout.splitlines()
        for img in image_names:
            if img.startswith(prefix) and img != current:
                self.remove_image(img)

    def ensure_image(self, key, context_dir: str = ".") -> str:
        image = self.get_image_name(key)
        images = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
        return image 