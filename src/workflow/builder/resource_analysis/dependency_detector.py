"""依存関係検出器

リソースマッピングから各種依存関係を検出する純粋関数群
"""
from pathlib import Path
from typing import List, Dict, Any
from ..graph_builder_utils import NodeInfo, DependencyInfo


def detect_file_creation_dependencies(resource_mappings: Dict[str, Any]) -> List[DependencyInfo]:
    """ファイル作成依存関係を検出する純粋関数
    
    Args:
        resource_mappings: リソースマッピング辞書
        
    Returns:
        ファイル作成依存関係のリスト
    """
    dependencies = []
    file_creators = resource_mappings['file_creators']
    file_readers = resource_mappings['file_readers']
    
    for file_path, creators in file_creators.items():
        if file_path in file_readers:
            dependencies.extend(
                _create_creation_dependencies(
                    creators, file_readers[file_path], 
                    "FILE_CREATION", file_path,
                    f"File {file_path} must be created before being read"
                )
            )
    
    return dependencies


def detect_directory_creation_dependencies(resource_mappings: Dict[str, Any]) -> List[DependencyInfo]:
    """ディレクトリ作成依存関係を検出する純粋関数
    
    Args:
        resource_mappings: リソースマッピング辞書
        
    Returns:
        ディレクトリ作成依存関係のリスト
    """
    dependencies = []
    dir_creators = resource_mappings['dir_creators']
    dir_requirers = resource_mappings['dir_requirers']
    
    for dir_path, creators in dir_creators.items():
        if dir_path in dir_requirers:
            dependencies.extend(
                _create_creation_dependencies(
                    creators, dir_requirers[dir_path],
                    "DIRECTORY_CREATION", dir_path,
                    f"Directory {dir_path} must be created before being used"
                )
            )
    
    return dependencies


def detect_parent_directory_dependencies(node_infos: List[NodeInfo], 
                                        resource_mappings: Dict[str, Any]) -> List[DependencyInfo]:
    """親ディレクトリ依存関係を検出する純粋関数
    
    Args:
        node_infos: ノード情報のリスト
        resource_mappings: リソースマッピング辞書
        
    Returns:
        親ディレクトリ依存関係のリスト
    """
    dependencies = []
    dir_creators = resource_mappings['dir_creators']
    
    for idx, node_info in enumerate(node_infos):
        if node_info.creates_files:
            parent_dirs = _extract_parent_directories(node_info.creates_files)
            dependencies.extend(
                _find_parent_dir_dependencies(idx, node_info, parent_dirs, dir_creators)
            )
    
    return dependencies


def _create_creation_dependencies(creators, consumers, dep_type, resource_path, description):
    """作成・消費依存関係を生成するヘルパー関数"""
    dependencies = []
    
    for creator_idx, creator_info in creators:
        for consumer_idx, consumer_info in consumers:
            if creator_idx < consumer_idx:  # 順序を保持
                dependency = DependencyInfo(
                    from_node_id=creator_info.id,
                    to_node_id=consumer_info.id,
                    dependency_type=dep_type,
                    resource_path=resource_path,
                    description=description
                )
                dependencies.append(dependency)
    
    return dependencies


def _extract_parent_directories(file_paths):
    """ファイルパスから親ディレクトリを抽出"""
    parent_dirs = set()
    for file_path in file_paths:
        parent = str(Path(file_path).parent)
        if parent != '.' and parent != '/':
            parent_dirs.add(parent)
    return parent_dirs


def _find_parent_dir_dependencies(idx, node_info, parent_dirs, dir_creators):
    """親ディレクトリ依存関係を検出"""
    dependencies = []
    
    for parent_dir in parent_dirs:
        if parent_dir in dir_creators:
            for creator_idx, creator_info in dir_creators[parent_dir]:
                if creator_idx < idx:  # 親ディレクトリが先に作成される
                    dependency = DependencyInfo(
                        from_node_id=creator_info.id,
                        to_node_id=node_info.id,
                        dependency_type="DIRECTORY_CREATION",
                        resource_path=parent_dir,
                        description=f"Parent directory {parent_dir} must exist before creating files"
                    )
                    dependencies.append(dependency)
    
    return dependencies