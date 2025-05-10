import os
from src.path_manager.unified_path_manager import UnifiedPathManager

HOST_PROJECT_ROOT = os.path.abspath(".")
CONTAINER_WORKSPACE = "/workspace"
upm = UnifiedPathManager(HOST_PROJECT_ROOT, CONTAINER_WORKSPACE)

TEMP_DIR = os.path.abspath('.temp')
CONTAINER_TEMP_DIR = "/workspace/.temp"

OJTOOLS_COOKIE_HOST = os.path.abspath(".local/share/online-judge-tools/cookie.jar")
OJTOOLS_COOKIE_CONT = "/root/.local/share/online-judge-tools/cookie.jar" 