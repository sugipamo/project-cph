from .ctl import DockerCtl
from concurrent.futures import ThreadPoolExecutor

CONTAINER_PREFIX = "cph"

def generate_container_name(purpose, language=None, index=None):
    parts = [CONTAINER_PREFIX, purpose]
    if language:
        parts.append(language)
    if index is not None:
        parts.append(str(index))
    return "_".join(parts)

class DockerPool:
    def __init__(self, max_workers=8):
        self.ctl = DockerCtl()
        self.max_workers = max_workers

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
        to_start = [c for c in required_containers if c["name"] not in existing]
        print(f"[DEBUG] required_containers: {required_containers}")
        print(f"[DEBUG] to_start: {to_start}")
        def start_c(c):
            image = "oj" if c["type"] == "ojtools" else c.get("language", "python")
            self.ctl.start_container(c["name"], image, volumes=c.get("volumes"))
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(start_c, to_start))
        return required_containers 