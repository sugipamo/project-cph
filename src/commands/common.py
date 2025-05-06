# ここには他の共通関数のみを残す

from src.docker.path_mapper import DockerPathMapper
import os

def get_project_root_volumes():
    project_root = os.path.abspath(".")
    container_root = "/workspace"
    path_mapper = DockerPathMapper(project_root, container_root)
    # ここでは単純なマッピングを返すが、将来的にpath_mapperを使って柔軟に拡張可能
    volumes = {
        path_mapper.host_root: path_mapper.container_root
    }
    return volumes 