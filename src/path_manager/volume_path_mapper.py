from pathlib import Path
from typing import List, Tuple, Optional
import os

class VolumePathMapper:
    """
    複数の(ホスト,コンテナ)マウントペアを管理し、
    パス変換・自動マウント生成・Pathlib統一・未マウント時None返却を提供する。
    """
    def __init__(self, mounts: List[Tuple[Path, Path]]):
        # mounts: [(host_path, container_path), ...]
        self.mounts = [(Path(h).resolve(), Path(c)) for h, c in mounts]

    @classmethod
    def from_required_paths(cls, required_paths: List[Path], container_root: Path = Path("/workspace")):
        """
        必要なファイル・フォルダリストから最小限のマウントペアを自動生成。
        現状は全てのパスの共通親ディレクトリを1つマウントする簡易実装。
        """
        if not required_paths:
            raise ValueError("required_pathsは空にできません")
        abs_paths = [Path(p).resolve() for p in required_paths]
        common = abs_paths[0]
        for p in abs_paths[1:]:
            common = cls._common_path(common, p)
        # コンテナ側はcontainer_root直下に同名でマウント
        container_mount = container_root / common.name
        return cls([(common, container_mount)])

    @staticmethod
    def _common_path(p1: Path, p2: Path) -> Path:
        # 2つのパスの共通親ディレクトリ
        parts1 = p1.parts
        parts2 = p2.parts
        minlen = min(len(parts1), len(parts2))
        i = 0
        while i < minlen and parts1[i] == parts2[i]:
            i += 1
        return Path(*parts1[:i])

    def to_container_path(self):
        host_path = self.host_path
        for h_root, c_root in self.mounts:
            if hasattr(host_path, 'is_relative_to'):
                if host_path.is_relative_to(h_root):
                    rel = host_path.relative_to(h_root)
                    return c_root / rel
            else:
                try:
                    rel = host_path.relative_to(h_root)
                    return c_root / rel
                except ValueError:
                    continue
        return None

    def to_host_path(self):
        container_path = self.container_path
        for h_root, c_root in self.mounts:
            if hasattr(container_path, 'is_relative_to'):
                if container_path.is_relative_to(c_root):
                    rel = container_path.relative_to(c_root)
                    return h_root / rel
            else:
                try:
                    rel = container_path.relative_to(c_root)
                    return h_root / rel
                except ValueError:
                    continue
        return None

    def add_mount(self):
        self.mounts.append((self.host_path.resolve(), self.container_path))

    def get_mounts(self) -> List[Tuple[Path, Path]]:
        return list(self.mounts) 