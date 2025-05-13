from pathlib import Path
from typing import List, Tuple, Optional
from src.path_manager.project_path_manager import ProjectPathManager
from src.path_manager.volume_path_mapper import VolumePathMapper
from src.path_manager.common_paths import CONTAINER_WORKSPACE, HOST_WORKSPACE

class UnifiedPathManager:
    """
    ProjectPathManagerとVolumePathMapperをラップし、
    プロジェクト内の論理パス管理・ホスト⇔コンテナ変換・マウント管理を一元化するクラス。
    """
    def __init__(self, project_root=None, container_root="/workspace", mounts: Optional[List[Tuple[Path, Path]]] = None):
        self.project_root = str(project_root) if project_root else str(Path.cwd().resolve())
        self.container_root = str(container_root)
        self.project_path = ProjectPathManager(project_root)
        if mounts is None:
            # デフォルトはproject_root→container_rootの1ペア
            host_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
            mounts = [(host_root, Path(container_root))]
        self.volume_mapper = VolumePathMapper(mounts)

    # ProjectPathManagerのラップ
    def contest_current(self, *paths) -> Path:
        return self.project_path.contest_current(*paths)
    def contest_stocks(self, *args, **kwargs) -> Path:
        return self.project_path.contest_stocks(*args, **kwargs)
    def contest_env(self, filename) -> Path:
        return self.project_path.contest_env(filename)
    def contest_template(self, *args, **kwargs) -> Path:
        return self.project_path.contest_template(*args, **kwargs)
    def info_json(self) -> Path:
        return self.project_path.info_json()
    def config_json(self) -> Path:
        return self.project_path.config_json()
    def test_dir(self) -> Path:
        return self.project_path.test_dir()
    def readme_md(self) -> Path:
        return self.project_path.readme_md()

    # VolumePathMapperのラップ
    def to_container_path(self):
        return self.volume_mapper.to_container_path()
    def to_host_path(self):
        return self.volume_mapper.to_host_path()
    def get_mounts(self) -> List[Tuple[Path, Path]]:
        return self.volume_mapper.get_mounts()
    def add_mount(self):
        self.volume_mapper.add_mount()

    # 論理パス→コンテナパスのショートカット
    def contest_current_in_container(self, *paths) -> Optional[Path]:
        return self.to_container_path(self.contest_current(*paths))
    def contest_stocks_in_container(self, *args, **kwargs) -> Optional[Path]:
        return self.to_container_path(self.contest_stocks(*args, **kwargs))
    def contest_env_in_container(self, filename) -> Optional[Path]:
        return self.to_container_path(self.contest_env(filename))
    def contest_template_in_container(self, *args, **kwargs) -> Optional[Path]:
        return self.to_container_path(self.contest_template(*args, **kwargs))
    def info_json_in_container(self) -> Optional[Path]:
        return self.to_container_path(self.info_json())
    def config_json_in_container(self) -> Optional[Path]:
        return self.to_container_path(self.config_json())
    def test_dir_in_container(self) -> Optional[Path]:
        return self.to_container_path(self.test_dir())
    def readme_md_in_container(self) -> Optional[Path]:
        return self.to_container_path(self.readme_md())

    # --- 追加: パスのバリデーション ---
    @staticmethod
    def is_valid_path(path, must_exist=True, must_be_file=None, must_be_dir=None):
        """
        パスが存在するか、ファイル/ディレクトリ種別が正しいかをチェック。
        must_exist: 存在チェック
        must_be_file: ファイルであることを要求（Noneなら無視）
        must_be_dir: ディレクトリであることを要求（Noneなら無視）
        """
        from pathlib import Path as _Path
        p = _Path(path)
        if must_exist and not p.exists():
            return False
        if must_be_file is True and not p.is_file():
            return False
        if must_be_dir is True and not p.is_dir():
            return False
        return True

    @staticmethod
    def ensure_exists(path, create_if_missing=False, is_dir=False):
        """
        パスが存在しない場合、create_if_missing=Trueなら作成する。
        is_dir: ディレクトリとして作成するかどうか。
        """
        from pathlib import Path as _Path
        p = _Path(path)
        if not p.exists() and create_if_missing:
            if is_dir:
                p.mkdir(parents=True, exist_ok=True)
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch()
        return p.exists()

    # --- 追加: パスの正規化・解決 ---
    @staticmethod
    def normalize_path(path) -> Path:
        """
        パスを絶対パスに正規化する。
        """
        from pathlib import Path as _Path
        return _Path(path).resolve()

    @staticmethod
    def resolve_symlink(path) -> Path:
        """
        シンボリックリンクを解決した実体パスを返す。
        """
        from pathlib import Path as _Path
        return _Path(path).resolve(strict=False)

    def is_host_path(self, path: str) -> bool:
        """
        指定パスがホスト側のパスかどうかを判定
        """
        import os
        abs_path = os.path.abspath(str(path))
        for host_root, _ in self.get_mounts():
            if abs_path.startswith(str(host_root)):
                return True
        return False

    def is_container_path(self, path: str) -> bool:
        """
        指定パスがコンテナ側のパスかどうかを判定
        """
        path_str = str(path)
        for _, cont_root in self.get_mounts():
            if path_str.startswith(str(cont_root)):
                return True
        return False 