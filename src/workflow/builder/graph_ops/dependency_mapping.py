"""依存関係マッピングの純粋関数"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set

from .metadata_extraction import RequestMetadata


class DependencyType(Enum):
    """依存関係の種類"""
    FILE_CREATION = "file_creation"
    DIRECTORY_CREATION = "dir_creation"
    RESOURCE_ACCESS = "resource_access"
    EXECUTION_ORDER = "exec_order"


@dataclass(frozen=True)
class DependencyMapping:
    """依存関係マッピング（不変データ構造）"""
    from_node_id: str
    to_node_id: str
    dependency_type: DependencyType
    resource_path: str = ""
    description: str = ""

    def to_edge_dict(self) -> Dict[str, str]:
        """エッジ辞書に変換（純粋関数）"""
        return {
            'from_node': self.from_node_id,
            'to_node': self.to_node_id,
            'type': self.dependency_type.value,
            'resource': self.resource_path,
            'description': self.description
        }


@dataclass(frozen=True)
class DependencyGraph:
    """依存関係グラフ（不変データ構造）"""
    mappings: List[DependencyMapping]

    @property
    def adjacency_dict(self) -> Dict[str, Set[str]]:
        """隣接リスト辞書を生成（純粋関数）"""
        adj = {}
        for mapping in self.mappings:
            if mapping.from_node_id not in adj:
                adj[mapping.from_node_id] = set()
            adj[mapping.from_node_id].add(mapping.to_node_id)
        return adj

    @property
    def reverse_adjacency_dict(self) -> Dict[str, Set[str]]:
        """逆隣接リスト辞書を生成（純粋関数）"""
        reverse_adj = {}
        for mapping in self.mappings:
            if mapping.to_node_id not in reverse_adj:
                reverse_adj[mapping.to_node_id] = set()
            reverse_adj[mapping.to_node_id].add(mapping.from_node_id)
        return reverse_adj

    @property
    def node_ids(self) -> Set[str]:
        """すべてのノードIDを取得（純粋関数）"""
        nodes = set()
        for mapping in self.mappings:
            nodes.add(mapping.from_node_id)
            nodes.add(mapping.to_node_id)
        return nodes

    def with_mapping(self, mapping: DependencyMapping) -> 'DependencyGraph':
        """新しいマッピングを追加した新グラフを返却（純粋関数）"""
        return DependencyGraph([*self.mappings, mapping])

    def filter_by_type(self, dependency_type: DependencyType) -> 'DependencyGraph':
        """依存関係タイプでフィルタした新グラフを返却（純粋関数）"""
        filtered = [m for m in self.mappings if m.dependency_type == dependency_type]
        return DependencyGraph(filtered)


def build_dependency_mapping(metadata_list: List[RequestMetadata]) -> DependencyGraph:
    """メタデータから依存関係グラフを構築（純粋関数）

    Args:
        metadata_list: リクエストメタデータリスト

    Returns:
        依存関係グラフ
    """
    from .metadata_extraction import group_metadata_by_resource

    mappings = []
    grouped = group_metadata_by_resource(metadata_list)

    # ファイル作成依存を検出
    file_mappings = _build_file_creation_dependencies(
        grouped['file_creators'],
        grouped['file_readers']
    )
    mappings.extend(file_mappings)

    # ディレクトリ作成依存を検出
    dir_mappings = _build_directory_creation_dependencies(
        grouped['dir_creators'],
        grouped['dir_requirers']
    )
    mappings.extend(dir_mappings)

    # 暗黙的ディレクトリ依存を検出
    implicit_mappings = _build_implicit_directory_dependencies(metadata_list)
    mappings.extend(implicit_mappings)

    # 順序依存を検出
    order_mappings = _build_execution_order_dependencies(metadata_list)
    mappings.extend(order_mappings)

    return DependencyGraph(mappings)


def _build_file_creation_dependencies(file_creators: Dict[str, List[RequestMetadata]],
                                    file_readers: Dict[str, List[RequestMetadata]]) -> List[DependencyMapping]:
    """ファイル作成依存を構築（純粋関数）"""
    mappings = []

    for file_path, creators in file_creators.items():
        if file_path in file_readers:
            readers = file_readers[file_path]

            for creator in creators:
                for reader in readers:
                    if creator.index < reader.index:
                        mapping = DependencyMapping(
                            from_node_id=creator.node_id,
                            to_node_id=reader.node_id,
                            dependency_type=DependencyType.FILE_CREATION,
                            resource_path=file_path,
                            description=f"File {file_path} must be created before being read"
                        )
                        mappings.append(mapping)

    return mappings


def _build_directory_creation_dependencies(dir_creators: Dict[str, List[RequestMetadata]],
                                         dir_requirers: Dict[str, List[RequestMetadata]]) -> List[DependencyMapping]:
    """ディレクトリ作成依存を構築（純粋関数）"""
    mappings = []

    for dir_path, creators in dir_creators.items():
        if dir_path in dir_requirers:
            requirers = dir_requirers[dir_path]

            for creator in creators:
                for requirer in requirers:
                    if creator.index < requirer.index:
                        mapping = DependencyMapping(
                            from_node_id=creator.node_id,
                            to_node_id=requirer.node_id,
                            dependency_type=DependencyType.DIRECTORY_CREATION,
                            resource_path=dir_path,
                            description=f"Directory {dir_path} must be created before being used"
                        )
                        mappings.append(mapping)

    return mappings


def _build_implicit_directory_dependencies(metadata_list: List[RequestMetadata]) -> List[DependencyMapping]:
    """暗黙的ディレクトリ依存を構築（純粋関数）"""
    from .metadata_extraction import find_implicit_directory_dependencies

    mappings = []
    dependencies = find_implicit_directory_dependencies(metadata_list)

    for creator, file_creator, dir_path in dependencies:
        mapping = DependencyMapping(
            from_node_id=creator.node_id,
            to_node_id=file_creator.node_id,
            dependency_type=DependencyType.DIRECTORY_CREATION,
            resource_path=dir_path,
            description=f"Directory {dir_path} must exist for file creation"
        )
        mappings.append(mapping)

    return mappings


def _build_execution_order_dependencies(metadata_list: List[RequestMetadata]) -> List[DependencyMapping]:
    """実行順序依存を構築（純粋関数）"""
    mappings = []

    # 隣接するノード間でリソース競合がある場合のみ順序依存を追加
    for i in range(len(metadata_list) - 1):
        current = metadata_list[i]
        next_meta = metadata_list[i + 1]

        # リソース競合がある場合のみ順序依存を追加
        if current.has_resource_conflict_with(next_meta):
            mapping = DependencyMapping(
                from_node_id=current.node_id,
                to_node_id=next_meta.node_id,
                dependency_type=DependencyType.EXECUTION_ORDER,
                description="Preserve original execution order due to resource conflict"
            )
            mappings.append(mapping)

    return mappings


def merge_dependency_graphs(graph1: DependencyGraph, graph2: DependencyGraph) -> DependencyGraph:
    """依存関係グラフをマージ（純粋関数）

    Args:
        graph1: グラフ1
        graph2: グラフ2

    Returns:
        マージされたグラフ
    """
    # 重複を除去してマージ
    all_mappings = graph1.mappings + graph2.mappings
    unique_mappings = []
    seen = set()

    for mapping in all_mappings:
        key = (mapping.from_node_id, mapping.to_node_id, mapping.dependency_type)
        if key not in seen:
            unique_mappings.append(mapping)
            seen.add(key)

    return DependencyGraph(unique_mappings)


def filter_transitive_dependencies(graph: DependencyGraph) -> DependencyGraph:
    """推移的依存関係を除去（純粋関数）

    Args:
        graph: 元グラフ

    Returns:
        推移的依存を除去したグラフ
    """
    adj = graph.adjacency_dict

    # Floyd-Warshall風のアルゴリズムで推移的閉包を計算
    all_nodes = list(graph.node_ids)
    reachable = {}

    # 初期化：直接の依存関係
    for node in all_nodes:
        reachable[node] = adj.get(node, set()).copy()

    # 推移的閉包を計算
    for k in all_nodes:
        for i in all_nodes:
            for j in all_nodes:
                if k in reachable.get(i, set()) and j in reachable.get(k, set()):
                    if i not in reachable:
                        reachable[i] = set()
                    reachable[i].add(j)

    # 推移的依存を除去
    filtered_mappings = []
    for mapping in graph.mappings:
        from_node = mapping.from_node_id
        to_node = mapping.to_node_id

        # 直接依存のみ保持（中間ノード経由でアクセス可能でない）
        is_direct = True
        for intermediate in all_nodes:
            if (intermediate != from_node and intermediate != to_node and
                intermediate in reachable.get(from_node, set()) and
                to_node in reachable.get(intermediate, set())):
                is_direct = False
                break

        if is_direct:
            filtered_mappings.append(mapping)

    return DependencyGraph(filtered_mappings)


def calculate_dependency_statistics(graph: DependencyGraph) -> Dict[str, int]:
    """依存関係統計を計算（純粋関数）

    Args:
        graph: 依存関係グラフ

    Returns:
        統計情報辞書
    """
    stats = {
        'total_dependencies': len(graph.mappings),
        'total_nodes': len(graph.node_ids),
        'file_dependencies': 0,
        'directory_dependencies': 0,
        'order_dependencies': 0
    }

    for mapping in graph.mappings:
        if mapping.dependency_type == DependencyType.FILE_CREATION:
            stats['file_dependencies'] += 1
        elif mapping.dependency_type == DependencyType.DIRECTORY_CREATION:
            stats['directory_dependencies'] += 1
        elif mapping.dependency_type == DependencyType.EXECUTION_ORDER:
            stats['order_dependencies'] += 1

    return stats
