from pathlib import Path
from typing import List, Tuple, Optional
from src.project_path_manager import ProjectPathManager
from src.volume_path_mapper import VolumePathMapper

class UnifiedPathManager:
    """
    ProjectPathManagerとVolumePathMapperをラップし、
    プロジェクト内の論理パス管理・ホスト⇔コンテナ変換・マウント管理を一元化するクラス。
    """
    def __init__(self, project_root=None, container_root="/workspace", mounts: Optional[List[Tuple[Path, Path]]] = None):
        self.project_path = ProjectPathManager(project_root)
        if mounts is None:
            # デフォルトはproject_root→container_rootの1ペア
            host_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
            mounts = [(host_root, Path(container_root))]
        self.volume_mapper = VolumePathMapper(mounts)

    # ProjectPathManagerのラップ
    def contest_current(self, *paths):
        return self.project_path.contest_current(*paths)
    def contest_stocks(self, *args, **kwargs):
        return self.project_path.contest_stocks(*args, **kwargs)
    def contest_env(self, filename):
        return self.project_path.contest_env(filename)
    def contest_template(self, *args, **kwargs):
        return self.project_path.contest_template(*args, **kwargs)
    def info_json(self):
        return self.project_path.info_json()
    def config_json(self):
        return self.project_path.config_json()
    def test_dir(self):
        return self.project_path.test_dir()
    def readme_md(self):
        return self.project_path.readme_md()

    # VolumePathMapperのラップ
    def to_container_path(self, host_path: Path) -> Optional[Path]:
        return self.volume_mapper.to_container_path(host_path)
    def to_host_path(self, container_path: Path) -> Optional[Path]:
        return self.volume_mapper.to_host_path(container_path)
    def get_mounts(self) -> List[Tuple[Path, Path]]:
        return self.volume_mapper.get_mounts()
    def add_mount(self, host_path: Path, container_path: Path):
        self.volume_mapper.add_mount(host_path, container_path)

    # 論理パス→コンテナパスのショートカット
    def contest_current_in_container(self, *paths):
        return self.to_container_path(Path(self.contest_current(*paths)))
    def contest_stocks_in_container(self, *args, **kwargs):
        return self.to_container_path(Path(self.contest_stocks(*args, **kwargs)))
    def contest_env_in_container(self, filename):
        return self.to_container_path(Path(self.contest_env(filename)))
    def contest_template_in_container(self, *args, **kwargs):
        return self.to_container_path(Path(self.contest_template(*args, **kwargs)))
    def info_json_in_container(self):
        return self.to_container_path(Path(self.info_json()))
    def config_json_in_container(self):
        return self.to_container_path(Path(self.config_json()))
    def test_dir_in_container(self):
        return self.to_container_path(Path(self.test_dir()))
    def readme_md_in_container(self):
        return self.to_container_path(Path(self.readme_md())) 