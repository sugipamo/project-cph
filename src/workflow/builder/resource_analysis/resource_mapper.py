"""リソースマッピング構築

ノード情報からリソースの作成者・使用者の対応関係を構築する純粋関数群
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..graph_builder_utils import NodeInfo


@dataclass(frozen=True)
class ResourceMapping:
    """リソースマッピングを表現する不変データ構造"""
    file_creators: Dict[str, List[Tuple[int, NodeInfo]]]
    dir_creators: Dict[str, List[Tuple[int, NodeInfo]]]
    file_readers: Dict[str, List[Tuple[int, NodeInfo]]]
    dir_requirers: Dict[str, List[Tuple[int, NodeInfo]]]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（既存APIとの互換性のため）"""
        return {
            'file_creators': self.file_creators,
            'dir_creators': self.dir_creators,
            'file_readers': self.file_readers,
            'dir_requirers': self.dir_requirers
        }


def build_resource_mappings(node_infos: List[NodeInfo]) -> Dict[str, Any]:
    """ノード情報からリソースマッピングを構築する純粋関数

    Args:
        node_infos: ノード情報のリスト

    Returns:
        リソースマッピング辞書（既存APIとの互換性のため）
    """
    mapping = _build_typed_resource_mappings(node_infos)
    return mapping.to_dict()


def _build_typed_resource_mappings(node_infos: List[NodeInfo]) -> ResourceMapping:
    """型安全なリソースマッピングを構築する純粋関数"""
    file_creators = _build_file_creators_mapping(node_infos)
    dir_creators = _build_dir_creators_mapping(node_infos)
    file_readers = _build_file_readers_mapping(node_infos)
    dir_requirers = _build_dir_requirers_mapping(node_infos)

    return ResourceMapping(
        file_creators=file_creators,
        dir_creators=dir_creators,
        file_readers=file_readers,
        dir_requirers=dir_requirers
    )


def _build_file_creators_mapping(node_infos: List[NodeInfo]) -> Dict[str, List[Tuple[int, NodeInfo]]]:
    """ファイル作成者のマッピングを構築"""
    file_creators = {}

    for idx, node_info in enumerate(node_infos):
        for file_path in node_info.creates_files:
            if file_path not in file_creators:
                file_creators[file_path] = []
            file_creators[file_path].append((idx, node_info))

    return file_creators


def _build_dir_creators_mapping(node_infos: List[NodeInfo]) -> Dict[str, List[Tuple[int, NodeInfo]]]:
    """ディレクトリ作成者のマッピングを構築"""
    dir_creators = {}

    for idx, node_info in enumerate(node_infos):
        for dir_path in node_info.creates_dirs:
            if dir_path not in dir_creators:
                dir_creators[dir_path] = []
            dir_creators[dir_path].append((idx, node_info))

    return dir_creators


def _build_file_readers_mapping(node_infos: List[NodeInfo]) -> Dict[str, List[Tuple[int, NodeInfo]]]:
    """ファイル読み取り者のマッピングを構築"""
    file_readers = {}

    for idx, node_info in enumerate(node_infos):
        for file_path in node_info.reads_files:
            if file_path not in file_readers:
                file_readers[file_path] = []
            file_readers[file_path].append((idx, node_info))

    return file_readers


def _build_dir_requirers_mapping(node_infos: List[NodeInfo]) -> Dict[str, List[Tuple[int, NodeInfo]]]:
    """ディレクトリ要求者のマッピングを構築"""
    dir_requirers = {}

    for idx, node_info in enumerate(node_infos):
        for dir_path in node_info.requires_dirs:
            if dir_path not in dir_requirers:
                dir_requirers[dir_path] = []
            dir_requirers[dir_path].append((idx, node_info))

    return dir_requirers
