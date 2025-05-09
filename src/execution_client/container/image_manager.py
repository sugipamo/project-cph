from abc import ABC, abstractmethod
import subprocess
from typing import Optional, Dict
import hashlib
import os

class AbstractContainerImageManager(ABC):
    @abstractmethod
    def build_image(self, dockerfile_path: str, image_name: str, context_dir: str = ".") -> bool:
        pass

    @abstractmethod
    def remove_image(self, image_name: str) -> bool:
        pass

    @abstractmethod
    def image_exists(self, image_name: str) -> bool:
        pass

    @abstractmethod
    def get_image_name(self, base_name: str, tag: Optional[str] = None) -> str:
        pass

class ContainerImageManager(AbstractContainerImageManager):
    def __init__(self, dockerfile_map: Optional[Dict[str, str]] = None):
        self.dockerfile_map = dockerfile_map or {}

    def build_image(self, dockerfile_path: str, image_name: str, context_dir: str = ".") -> bool:
        """
        Dockerfileからイメージをビルドする。
        """
        cmd = [
            "docker", "build", "-f", dockerfile_path, "-t", image_name, context_dir
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] docker build failed: {e.stderr}")
            return False

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

    def get_image_name(self, key: str) -> str:
        # ojtoolsだけはハッシュなしの固定名
        if key == "ojtools":
            return "cph_image_ojtools"
        dockerfile = self.dockerfile_map.get(key, None)
        if not dockerfile or not os.path.exists(dockerfile):
            return key  # fallback
        hashval = self.get_dockerfile_hash(dockerfile)
        return f"cph_image_{key}_{hashval}"

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

    def ensure_image(self, key: str, context_dir: str = ".") -> str:
        image = self.get_image_name(key)
        images = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
        image_names = images.stdout.splitlines()
        if image not in image_names:
            dockerfile = self.dockerfile_map.get(key, None)
            if dockerfile and os.path.exists(dockerfile):
                # ojtoolsだけはハッシュなしでビルド
                self.build_image(dockerfile, image, context_dir)
                if key != "ojtools":
                    self.cleanup_old_images(key)
        return image 