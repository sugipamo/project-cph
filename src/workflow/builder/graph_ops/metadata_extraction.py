"""リクエストメタデータ抽出の純粋関数"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set


@dataclass(frozen=True)
class RequestMetadata:
    """リクエストメタデータ（不変データ構造）"""
    node_id: str
    index: int  # 元の順序
    creates_files: Set[str]
    creates_dirs: Set[str]
    reads_files: Set[str]
    requires_dirs: Set[str]

    @classmethod
    def from_request_node(cls, node, index: int) -> 'RequestMetadata':
        """RequestNodeからメタデータを抽出（純粋関数）"""
        return cls(
            node_id=node.id,
            index=index,
            creates_files=node.creates_files.copy(),
            creates_dirs=node.creates_dirs.copy(),
            reads_files=node.reads_files.copy(),
            requires_dirs=node.requires_dirs.copy()
        )

    @property
    def all_created_resources(self) -> Set[str]:
        """作成するすべてのリソース（純粋関数）"""
        return self.creates_files | self.creates_dirs

    @property
    def all_required_resources(self) -> Set[str]:
        """必要とするすべてのリソース（純粋関数）"""
        return self.reads_files | self.requires_dirs

    def has_resource_conflict_with(self, other: 'RequestMetadata') -> bool:
        """他のメタデータとリソース競合があるか（純粋関数）"""
        # 同じファイル/ディレクトリの作成競合
        creation_conflict = bool(self.all_created_resources & other.all_created_resources)

        # 作成と読み取りの競合
        read_write_conflict = bool(
            (self.all_created_resources & other.all_required_resources) |
            (self.all_required_resources & other.all_created_resources)
        )

        return creation_conflict or read_write_conflict


def extract_request_metadata(nodes: List[Any]) -> List[RequestMetadata]:
    """リクエストからメタデータを抽出（純粋関数）

    Args:
        nodes: RequestNodeのリスト

    Returns:
        RequestMetadataのリスト
    """
    return [
        RequestMetadata.from_request_node(node, index)
        for index, node in enumerate(nodes)
    ]


def calculate_parent_directories(file_paths: Set[str]) -> Set[str]:
    """ファイルパスから親ディレクトリを計算（純粋関数）

    Args:
        file_paths: ファイルパス集合

    Returns:
        親ディレクトリ集合
    """
    parent_dirs = set()
    for file_path in file_paths:
        parent = str(Path(file_path).parent)
        if parent != '.':
            parent_dirs.add(parent)
    return parent_dirs


def group_metadata_by_resource(metadata_list: List[RequestMetadata]) -> Dict[str, Dict[str, List[RequestMetadata]]]:
    """リソース別にメタデータをグループ化（純粋関数）

    Args:
        metadata_list: メタデータリスト

    Returns:
        リソース種別->リソース->メタデータリストの辞書
    """

    grouped = {
        'file_creators': {},
        'dir_creators': {},
        'file_readers': {},
        'dir_requirers': {}
    }

    # ファイル作成者
    for metadata in metadata_list:
        for file_path in metadata.creates_files:
            if file_path not in grouped['file_creators']:
                grouped['file_creators'][file_path] = []
            grouped['file_creators'][file_path].append(metadata)

    # ディレクトリ作成者
    for metadata in metadata_list:
        for dir_path in metadata.creates_dirs:
            if dir_path not in grouped['dir_creators']:
                grouped['dir_creators'][dir_path] = []
            grouped['dir_creators'][dir_path].append(metadata)

    # ファイル読み取り者
    for metadata in metadata_list:
        for file_path in metadata.reads_files:
            if file_path not in grouped['file_readers']:
                grouped['file_readers'][file_path] = []
            grouped['file_readers'][file_path].append(metadata)

    # ディレクトリ要求者
    for metadata in metadata_list:
        for dir_path in metadata.requires_dirs:
            if dir_path not in grouped['dir_requirers']:
                grouped['dir_requirers'][dir_path] = []
            grouped['dir_requirers'][dir_path].append(metadata)

    return grouped


def find_implicit_directory_dependencies(metadata_list: List[RequestMetadata]) -> List[tuple]:
    """暗黙的なディレクトリ依存関係を発見（純粋関数）

    Args:
        metadata_list: メタデータリスト

    Returns:
        (from_metadata, to_metadata, parent_dir)のタプルリスト
    """
    dependencies = []

    # ディレクトリ作成者のマップ
    dir_creators = {}
    for metadata in metadata_list:
        for dir_path in metadata.creates_dirs:
            if dir_path not in dir_creators:
                dir_creators[dir_path] = []
            dir_creators[dir_path].append(metadata)

    # ファイル作成者の親ディレクトリ依存をチェック
    for metadata in metadata_list:
        if metadata.creates_files:
            parent_dirs = calculate_parent_directories(metadata.creates_files)

            for parent_dir in parent_dirs:
                # 親ディレクトリを作成するメタデータを検索
                for dir_path, creators in dir_creators.items():
                    if is_parent_directory(dir_path, parent_dir) or dir_path == parent_dir:
                        for creator in creators:
                            if creator.index < metadata.index:
                                dependencies.append((creator, metadata, dir_path))
                                break

    return dependencies


def is_parent_directory(parent_path: str, child_path: str) -> bool:
    """親ディレクトリ判定（純粋関数）

    Args:
        parent_path: 親ディレクトリパス
        child_path: 子パス

    Returns:
        親ディレクトリの場合True
    """
    parent = Path(parent_path).resolve()
    child = Path(child_path).resolve()

    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def filter_metadata_by_resource_type(metadata_list: List[RequestMetadata],
                                   resource_type: str) -> List[RequestMetadata]:
    """リソースタイプでメタデータをフィルタ（純粋関数）

    Args:
        metadata_list: メタデータリスト
        resource_type: リソースタイプ ("creates_files", "creates_dirs", etc.)

    Returns:
        フィルタされたメタデータリスト
    """
    filtered = []
    for metadata in metadata_list:
        resources = getattr(metadata, resource_type, set())
        if resources:
            filtered.append(metadata)
    return filtered


def sort_metadata_by_index(metadata_list: List[RequestMetadata]) -> List[RequestMetadata]:
    """インデックス順でメタデータをソート（純粋関数）

    Args:
        metadata_list: メタデータリスト

    Returns:
        ソートされたメタデータリスト
    """
    return sorted(metadata_list, key=lambda m: m.index)


def deduplicate_metadata(metadata_list: List[RequestMetadata]) -> List[RequestMetadata]:
    """重複メタデータを削除（純粋関数）

    Args:
        metadata_list: メタデータリスト

    Returns:
        重複削除されたメタデータリスト
    """
    seen_ids = set()
    deduplicated = []

    for metadata in metadata_list:
        if metadata.node_id not in seen_ids:
            deduplicated.append(metadata)
            seen_ids.add(metadata.node_id)

    return deduplicated
