import hashlib
import os
from src.shell_process import ShellProcess, ShellProcessOptions



class ContainerImageManager:
    @staticmethod
    def build_image(dockerfile_path: str, image_name: str, workspace_dir: str) -> bool:
        """
        Dockerfileからイメージをビルドする。
        """
        cmd = [
            "docker", "build", "-f", dockerfile_path, "-t", image_name, workspace_dir
        ]
        opts = ShellProcessOptions()
        proc = ShellProcess.run(*cmd, options=opts)
        return proc.returncode == 0

    @staticmethod
    def remove_image(image_name: str) -> bool:
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

    @staticmethod
    def image_exists(image_name: str) -> bool:
        """
        イメージが存在するか確認する。
        """
        cmd = ["docker", "images", "--format", "{{.Repository}}", image_name]
        opts = ShellProcessOptions()
        proc = ShellProcess.run(*cmd, options=opts)
        images = proc.stdout.splitlines() if proc.stdout else []
        return image_name in images

    @staticmethod
    def get_dockerfile_hash(dockerfile_path: str) -> str:
        with open(dockerfile_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]

    @staticmethod
    def get_image_name(key, dockerfile_map) -> str:
        # keyは(言語,バージョン)タプル
        lang, ver = key if isinstance(key, tuple) else (key, None)
        dockerfile_or_image = dockerfile_map.get(key, None)
        # イメージ名が直接指定されていればそれを返す
        if dockerfile_or_image and (":" in dockerfile_or_image or "/" in dockerfile_or_image):
            return dockerfile_or_image
        dockerfile = dockerfile_or_image
        if not dockerfile or not os.path.exists(dockerfile):
            return f"{lang}_{ver}"  # fallback
        hashval = ContainerImageManager.get_dockerfile_hash(dockerfile)
        return f"cph_image_{lang}_{ver}_{hashval}"

    @staticmethod
    def cleanup_old_images(key: str, dockerfile_map) -> None:
        """
        key: 言語名や用途名
        現在のイメージ以外の同prefixイメージを削除
        """
        prefix = f"cph_image_{key}_"
        current = ContainerImageManager.get_image_name(key, dockerfile_map)
        opts = ShellProcessOptions()
        proc = ShellProcess.run("docker", "images", "--format", "{{.Repository}}", options=opts)
        image_names = proc.stdout.splitlines() if proc.stdout else []
        for img in image_names:
            if img.startswith(prefix) and img != current:
                ContainerImageManager.remove_image(img)

    @staticmethod
    def ensure_image(key, dockerfile_map, context_dir: str = ".") -> str:
        image = ContainerImageManager.get_image_name(key, dockerfile_map)
        opts = ShellProcessOptions()
        opts.cmd = ["docker", "images", "--format", "{{.Repository}}"]
        ShellProcess.run(options=opts)
        return image 