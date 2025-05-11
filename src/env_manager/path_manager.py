from src.path_manager.unified_path_manager import UnifiedPathManager

class PathManager:
    def __init__(self, project_root=None, container_root="/workspace", mounts=None):
        self._upm = UnifiedPathManager(project_root, container_root, mounts)

    def to_container_path(self, host_path: str) -> str:
        return str(self._upm.to_container_path(host_path))

    def to_host_path(self, container_path: str) -> str:
        return str(self._upm.to_host_path(container_path))

    def contest_current(self, *paths):
        return self._upm.contest_current(*paths)

    # 必要に応じて他のUnifiedPathManagerのメソッドもラップ

    # パス変換（ホスト⇔コンテナ）
    pass 