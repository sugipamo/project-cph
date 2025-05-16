from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from src.execution_client.client.container import ContainerClient
from .image_manager import ContainerImageManager

class ContainerOrchestrator:
    def __init__(self, requirements_map: Dict[Tuple[str, str], str], max_workers: int, timeout: int, client):
        self.client = client
        self.max_workers = max_workers
        self.requirements_map = requirements_map
        # unified_path_manager等は必要に応じて

    def orchestrate(self, requirements: List[Dict]) -> List[Dict]:
        """
        requirements: [{type, language, version, count, volumes, ...}]
        必要なコンテナ群を起動・調整し、状態を揃える
        """
        required = self._generate_required_containers(requirements)
        existing = set(self.client.list_containers(prefix="cph_"))
        required_names = set(c["name"] for c in required)
        self._remove_unneeded(existing, required_names)
        existing = set(self.client.list_containers(prefix="cph_"))
        to_start = self._get_to_start(existing, required)
        self._start_containers(to_start)
        return required

    def _generate_required_containers(self, requirements: List[Dict]) -> List[Dict]:
        # 必要なコンテナ情報を生成
        required_containers = []
        for req in requirements:
            count = req.get("count", 1)
            for i in range(count):
                c = {
                    "type": req.get("type"),
                    "language": req.get("language"),
                    "version": req.get("version"),
                    "index": i+1,
                    "name": self._generate_container_name(req.get("type"), req.get("language"), req.get("version"), i+1),
                    "volumes": req.get("volumes", {})
                }
                required_containers.append(c)
        return required_containers

    def _generate_container_name(self, purpose: str, language: Optional[str] = None, version: Optional[str] = None, index: Optional[int] = None) -> str:
        # シンプルな命名規則例
        name = f"cph_{purpose}"
        if language:
            name += f"_{language}"
        if version:
            name += f"_{version}"
        if index:
            name += f"_{index}"
        return name

    def _remove_unneeded(self, existing: set, required_names: set):
        to_remove = list(existing - required_names)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(self.client.remove_container, to_remove))

    def _get_to_start(self, existing: set, required: List[Dict]) -> List[Dict]:
        to_start = []
        for c in required:
            if c["name"] not in existing:
                to_start.append(c)
            else:
                inspect = self.client.inspect_container(c["name"])
                status = None
                if inspect and "State" in inspect:
                    status = inspect["State"].get("Status")
                if status != "running":
                    to_start.append(c)
        return to_start

    def _start_containers(self, to_start: List[Dict]):
        def start_c(c):
            key = (c.get("language", "python"), c.get("version", "default"))
            image = ContainerImageManager.ensure_image(key, self.requirements_map)
            if c["name"] in self.client.list_containers(prefix="cph_"):
                self.client.remove_container(c["name"])
            self.client.run_container(
                name=c["name"],
                image=image,
                volumes=c.get("volumes"),
                detach=True
            )
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(start_c, to_start)) 