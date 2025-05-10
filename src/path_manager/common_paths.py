import os
from src.path_manager.unified_path_manager import UnifiedPathManager

HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"
upm = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE) 