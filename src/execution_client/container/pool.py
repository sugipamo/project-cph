from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from src.execution_client.client.container import ContainerClient
from .image_manager import ContainerImageManager
from src.path_manager.unified_path_manager import UnifiedPathManager
from abc import ABC, abstractmethod
from .naming_utils import generate_container_name
import subprocess

class AbstractContainerPool(ABC):
    @abstractmethod
    def adjust(self, requirements: List[Dict]) -> List[Dict]:
        pass

class ContainerPool(AbstractContainerPool):
    def __init__(self, dockerfile_map: Dict[str, str], project_root: Optional[str] = None, container_root: str = "/workspace", max_workers: int = 8, timeout: int = 30, client=None):
        self.client = client if client is not None else ContainerClient(timeout=timeout)
        self.image_manager = ContainerImageManager(dockerfile_map)
        self.max_workers = max_workers
        self.dockerfile_map = dockerfile_map
        self.unified_path_manager = UnifiedPathManager(project_root=project_root, container_root=container_root)

    def generate_container_name(self, purpose: str, language: Optional[str] = None, index: Optional[int] = None) -> str:
        return generate_container_name(purpose, language, index)

    def adjust(self, requirements: List[Dict]) -> List[Dict]:
        required_containers = self._generate_required_containers(requirements)
        existing = set(self._get_existing_container_names())
        required_names = set(c["name"] for c in required_containers)
        self._remove_unneeded_containers(existing, required_names)
        existing = set(self._get_existing_container_names())
        to_start = self._get_containers_to_start(existing, required_containers)
        self._start_containers(to_start)
        return required_containers

    def _generate_required_containers(self, requirements: List[Dict]) -> List[Dict]:
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
                    c["name"] = self.generate_container_name(req["type"], req["language"], i+1)
                else:
                    c["name"] = self.generate_container_name(req["type"], None, i+1)
                if "volumes" in req:
                    c["volumes"] = req["volumes"]
                else:
                    c["volumes"] = {str(h): str(c) for h, c in self.unified_path_manager.get_mounts()}
                required_containers.append(c)
        return required_containers

    def _get_existing_container_names(self) -> List[str]:
        return self.client.list_containers(prefix="cph_")

    def _remove_unneeded_containers(self, existing: set, required_names: set):
        to_remove = list(existing - required_names)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(self.client.remove_container, to_remove))

    def _get_containers_to_start(self, existing: set, required_containers: List[Dict]) -> List[Dict]:
        to_start = []
        for c in required_containers:
            expected_vols = c.get("volumes")
            if c["name"] in existing:
                needs_restart = False
                inspect = self.client.inspect_container(c["name"])
                status = None
                if inspect and "State" in inspect:
                    status = inspect["State"].get("Status")
                if status == "running":
                    continue  # 既に起動中
                elif status in ("exited", "stopped"):
                    c["_reuse"] = True
                    to_start.append(c)
                    continue
                else:
                    # created, dead, paused, 他はremoveしてrun
                    self.client.remove_container(c["name"])
                    to_start.append(c)
                    continue
                if expected_vols and inspect:
                    mounts = inspect.get("Mounts", [])
                    for host_path, cont_path in expected_vols.items():
                        found = any(m.get("Source") == host_path and m.get("Destination") == cont_path for m in mounts)
                        if not found:
                            needs_restart = True
                            break
                if needs_restart:
                    self.client.remove_container(c["name"])
                    to_start.append(c)
            else:
                to_start.append(c)
        return to_start

    def _start_containers(self, to_start: List[Dict]):
        def start_c(c):
            if c["type"] == "ojtools":
                key = ("ojtools", "default")
            else:
                lang = c.get("language", "python")
                ver = c.get("version", "3.8")
                key = (lang, ver)
            image = self.image_manager.ensure_image(key)
            if c.get("_reuse"):
                self.client.start_container(c["name"], image=image)
            else:
                existing_names = self.client.list_containers(prefix="cph_")
                if c["name"] in existing_names:
                    self.client.remove_container(c["name"])
                self.client.run_container(
                    name=c["name"],
                    image=image,
                    volumes=c.get("volumes"),
                    detach=True
                )
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            list(executor.map(start_c, to_start)) 