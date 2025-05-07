# ここには他の共通関数のみを残す

from src.unified_path_manager import UnifiedPathManager
import os

def get_project_root_volumes():
    project_root = os.path.abspath(".")
    container_root = "/workspace"
    upm = UnifiedPathManager(project_root, container_root)
    mounts = upm.get_mounts()
    # dict形式で返す（host: container）
    volumes = {str(h): str(c) for h, c in mounts}
    return volumes 