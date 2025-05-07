from .ctl import DockerCtl
from concurrent.futures import ThreadPoolExecutor
import subprocess, json
from .path_mapper import DockerPathMapper
import os
import hashlib

CONTAINER_PREFIX = "cph"
DEFAULT_DOCKERFILE_MAP = {
    "python": "contest_env/python.Dockerfile",
    "pypy": "contest_env/pypy.Dockerfile",
    "rust": "contest_env/rust.Dockerfile",
    "ojtools": "contest_env/oj.Dockerfile",
}

def generate_container_name(purpose, language=None, index=None):
    parts = [CONTAINER_PREFIX, purpose]
    if language:
        parts.append(language)
    if index is not None:
        parts.append(str(index))
    return "_".join(parts)

class DockerImageManager:
    def __init__(self, dockerfile_map=None):
        self.dockerfile_map = dockerfile_map or DEFAULT_DOCKERFILE_MAP
    def get_dockerfile_hash(self, dockerfile_path):
        with open(dockerfile_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    def get_image_name(self, language):
        dockerfile = self.dockerfile_map.get(language, None)
        if not dockerfile or not os.path.exists(dockerfile):
            return language  # fallback
        hashval = self.get_dockerfile_hash(dockerfile)
        return f"cph_image_{language}_{hashval}"
    def cleanup_old_images(self, language):
        prefix = f"cph_image_{language}_"
        current = self.get_image_name(language)
        images = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
        image_names = images.stdout.splitlines()
        for img in image_names:
            if img.startswith(prefix) and img != current:
                subprocess.run(["docker", "rmi", img], capture_output=True)
    def ensure_image(self, language):
        image = self.get_image_name(language)
        images = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
        image_names = images.stdout.splitlines()
        if image not in image_names:
            dockerfile = self.dockerfile_map.get(language, None)
            if dockerfile and os.path.exists(dockerfile):
                subprocess.run(["docker", "build", "-f", dockerfile, "-t", image, "."], check=True)
                self.cleanup_old_images(language)
        return image

class DockerPool:
    def __init__(self, max_workers=8, dockerfile_map=None):
        self.ctl = DockerCtl()
        self.max_workers = max_workers
        self.path_mapper = DockerPathMapper(os.path.abspath("."), "/workspace")
        self.image_manager = DockerImageManager(dockerfile_map)

    def get_dockerfile_hash(self, dockerfile_path):
        with open(dockerfile_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]

    def get_image_name(self, language):
        # 言語ごとにDockerfileパスを決め打ち
        dockerfile = DEFAULT_DOCKERFILE_MAP.get(language, None)
        if not dockerfile or not os.path.exists(dockerfile):
            return language  # fallback
        hashval = self.get_dockerfile_hash(dockerfile)
        return f"cph_image_{language}_{hashval}"

    def adjust(self, requirements):
        """
        requirements: [
            {"type": "test", "language": "python", "count": 3, "volumes": {...}},
            {"type": "ojtools", "count": 1, "volumes": {...}}
        ]
        必要な用途・言語・数を受け取り、
        [{"name": ..., "type": ..., "language": ..., "index": ..., "volumes": ...}, ...] を返す
        """
        # 1. 必要なコンテナ情報を生成
        required_containers = []
        for req in requirements:
            count = req.get("count", 1)
            for i in range(count):
                c = {
                    "type": req["type"],
                    "index": i+1
                }
                if "language" in req:
                    c["language"] = req["language"]
                    c["name"] = generate_container_name(req["type"], req["language"], i+1)
                else:
                    c["name"] = generate_container_name(req["type"], None, i+1)
                if "volumes" in req:
                    c["volumes"] = req["volumes"]
                required_containers.append(c)
        # 2. 既存のcph_コンテナ名を取得
        existing = set(self.ctl.list_cph_containers())
        required_names = set(c["name"] for c in required_containers)
        # 3. 不要なコンテナを並列で削除
        to_remove = list(existing - required_names)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(self.ctl.remove_container, to_remove))
        # 4. 足りないコンテナを並列で起動
        to_start = []
        # 追加: 既存コンテナのボリューム構成が異なる場合、または停止している場合は削除して再作成
        for c in required_containers:
            expected_vols = c.get("volumes")
            if c["name"] in existing:
                needs_restart = False
                # コンテナが停止しているかチェック
                if not self.ctl.is_container_running(c["name"]):
                    needs_restart = True
                # ボリューム構成のチェック
                elif expected_vols:
                    result = self.ctl.exec_in_container(c["name"], ["docker", "inspect", "-f", "{{json .Mounts}}", c["name"]])
                    if result[0]:  # コマンドが成功した場合
                        mounts = json.loads(result[1])
                        for host_path, cont_path in expected_vols.items():
                            found = any(m.get("Source") == host_path and m.get("Destination") == cont_path for m in mounts)
                            if not found:
                                needs_restart = True
                                break
                if needs_restart:
                    self.ctl.remove_container(c["name"])
                    to_start.append(c)
            else:
                to_start.append(c)
        def start_c(c):
            language = "ojtools" if c["type"] == "ojtools" else c.get("language", "python")
            image = self.image_manager.ensure_image(language)
            self.ctl.start_container(c["name"], image, volumes=c.get("volumes"))
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(start_c, to_start))
        return required_containers 