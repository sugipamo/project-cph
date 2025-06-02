"""
設定解決の純粋関数実装
ConfigNodeの作成と解決ロジックを純粋関数として実装
"""
from dataclasses import dataclass
from typing import Any, List, Dict, Set, Optional, Union, Tuple
from collections import deque
from src.context.resolver.config_node import ConfigNode
from src.context.utils.format_utils import format_with_missing_keys


@dataclass(frozen=True)
class ConfigNodeData:
    """設定ノードデータの不変データクラス"""
    key: Union[str, int]
    value: Any
    matches: Set[str]
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            object.__setattr__(self, 'children_ids', [])


@dataclass(frozen=True)
class ConfigTreeData:
    """設定ツリーデータの不変データクラス"""
    nodes: Dict[str, ConfigNodeData]
    root_id: str
    
    def get_node(self, node_id: str) -> Optional[ConfigNodeData]:
        """ノードIDからノードデータを取得"""
        return self.nodes.get(node_id)
    
    def get_children(self, node_id: str) -> List[ConfigNodeData]:
        """子ノードのリストを取得"""
        node = self.get_node(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children_ids if child_id in self.nodes]
    
    def get_parent(self, node_id: str) -> Optional[ConfigNodeData]:
        """親ノードを取得"""
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return None
        return self.nodes.get(node.parent_id)


@dataclass(frozen=True)
class ResolveResult:
    """解決結果の不変データクラス"""
    nodes: List[ConfigNodeData]
    paths_found: List[Tuple[str, ...]]
    errors: List[str]
    warnings: List[str]


@dataclass(frozen=True)
class FormatResult:
    """フォーマット結果の不変データクラス"""
    formatted_string: str
    resolved_keys: Dict[str, str]
    missing_keys: Set[str]
    errors: List[str]


def build_config_tree_pure(data: Any, root_key: str = "root") -> ConfigTreeData:
    """
    辞書データから設定ツリーを構築する純粋関数
    
    Args:
        data: 構築元のデータ
        root_key: ルートノードのキー
        
    Returns:
        ConfigTreeData: 構築された設定ツリー
    """
    if not isinstance(data, dict):
        raise ValueError("ConfigResolver: dict以外は未対応です")
    
    nodes = {}
    node_counter = 0
    
    def generate_node_id() -> str:
        nonlocal node_counter
        node_counter += 1
        return f"node_{node_counter}"
    
    # ルートノードを作成
    root_id = generate_node_id()
    root_matches = _extract_matches_pure(data)
    root_node = ConfigNodeData(
        key=root_key,
        value=data,
        matches=root_matches,
        parent_id=None,
        children_ids=[]
    )
    nodes[root_id] = root_node
    
    # BFS でツリーを構築
    queue = [(root_id, data)]
    
    while queue:
        parent_id, current_data = queue.pop(0)
        parent_node = nodes[parent_id]
        children_ids = list(parent_node.children_ids)
        
        if isinstance(current_data, dict):
            for key, value in current_data.items():
                if key == "aliases":
                    continue  # エイリアスは既に処理済み
                
                child_id = generate_node_id()
                child_matches = _extract_matches_pure(value)
                child_node = ConfigNodeData(
                    key=key,
                    value=value,
                    matches=child_matches,
                    parent_id=parent_id,
                    children_ids=[]
                )
                nodes[child_id] = child_node
                children_ids.append(child_id)
                queue.append((child_id, value))
        
        elif isinstance(current_data, list):
            for index, value in enumerate(current_data):
                child_id = generate_node_id()
                child_matches = _extract_matches_pure(value)
                child_node = ConfigNodeData(
                    key=index,
                    value=value,
                    matches=child_matches,
                    parent_id=parent_id,
                    children_ids=[]
                )
                nodes[child_id] = child_node
                children_ids.append(child_id)
                queue.append((child_id, value))
        
        # 親ノードの子リストを更新
        updated_parent = ConfigNodeData(
            key=parent_node.key,
            value=parent_node.value,
            matches=parent_node.matches,
            parent_id=parent_node.parent_id,
            children_ids=children_ids
        )
        nodes[parent_id] = updated_parent
    
    return ConfigTreeData(nodes=nodes, root_id=root_id)


def _extract_matches_pure(value: Any) -> Set[str]:
    """
    値からマッチ情報を抽出する純粋関数
    
    Args:
        value: 抽出対象の値
        
    Returns:
        マッチ情報のセット
    """
    matches = set()
    
    if isinstance(value, dict):
        # aliasesを処理
        if "aliases" in value:
            aliases = value["aliases"]
            if isinstance(aliases, list):
                matches.update(str(alias) for alias in aliases)
            else:
                raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
        
        # keyをマッチに追加
        for key in value.keys():
            if key != "aliases":
                matches.add(str(key))
    
    elif isinstance(value, (str, int, float)):
        matches.add(str(value))
    
    return matches


def resolve_by_path_pure(tree: ConfigTreeData, path: Union[List[str], Tuple[str, ...]]) -> ResolveResult:
    """
    パスによる設定解決の純粋関数
    
    Args:
        tree: 設定ツリー
        path: 解決パス
        
    Returns:
        ResolveResult: 解決結果
    """
    if not isinstance(path, (list, tuple)):
        return ResolveResult(
            nodes=[],
            paths_found=[],
            errors=[f"resolve_by_path_pure: pathはlistまたはtupleである必要があります: {path}"],
            warnings=[]
        )
    
    path_tuple = tuple(str(p) for p in path)
    
    if not path_tuple:
        return ResolveResult(nodes=[], paths_found=[], errors=[], warnings=[])
    
    # マッチランクベースの解決
    results = []
    queue = [(path_tuple, 1, tree.root_id)]
    visited = set()
    
    while queue:
        current_path, match_rank, node_id = queue.pop()
        
        if node_id in visited:
            continue
        visited.add(node_id)
        
        node = tree.get_node(node_id)
        if not node:
            continue
        
        children = tree.get_children(node_id)
        
        for child in children:
            child_id = next((nid for nid, n in tree.nodes.items() if n == child), None)
            if not child_id:
                continue
            
            matched = False
            for i, path_part in enumerate(current_path):
                if path_part in child.matches:
                    matched = True
                    remaining_path = current_path[i+1:]
                    new_rank = match_rank + (1 << (len(path_tuple) - i))
                    queue.append((remaining_path, new_rank, child_id))
                    results.append((new_rank, child))
            
            if not matched:
                queue.append((current_path, match_rank, child_id))
    
    # ランクでソート
    results.sort(key=lambda x: x[0], reverse=True)
    resolved_nodes = [result[1] for result in results]
    paths_found = [path_tuple] if resolved_nodes else []
    
    return ResolveResult(
        nodes=resolved_nodes,
        paths_found=paths_found,
        errors=[],
        warnings=[]
    )


def resolve_best_pure(tree: ConfigTreeData, path: Union[List[str], Tuple[str, ...]]) -> Optional[ConfigNodeData]:
    """
    最良のマッチを解決する純粋関数
    
    Args:
        tree: 設定ツリー
        path: 解決パス
        
    Returns:
        最良のマッチノード、またはNone
    """
    result = resolve_by_path_pure(tree, path)
    return result.nodes[0] if result.nodes else None


def resolve_values_pure(tree: ConfigTreeData, path: Union[List[str], Tuple[str, ...]]) -> List[Any]:
    """
    パスに対応する値のリストを取得する純粋関数
    
    Args:
        tree: 設定ツリー
        path: 解決パス
        
    Returns:
        値のリスト
    """
    result = resolve_by_path_pure(tree, path)
    return [node.value for node in result.nodes]


def format_string_pure(
    template: str, 
    tree: ConfigTreeData, 
    initial_values: Optional[Dict[str, str]] = None
) -> FormatResult:
    """
    テンプレート文字列をフォーマットする純粋関数
    
    Args:
        template: フォーマットするテンプレート文字列
        tree: 設定ツリー
        initial_values: 初期値
        
    Returns:
        FormatResult: フォーマット結果
    """
    if not isinstance(template, str):
        return FormatResult(
            formatted_string=str(template),
            resolved_keys={},
            missing_keys=set(),
            errors=["Template must be a string"]
        )
    
    resolved_keys = dict(initial_values) if initial_values else {}
    formatted, missing_keys = format_with_missing_keys(template, **resolved_keys)
    
    if not missing_keys:
        return FormatResult(
            formatted_string=formatted,
            resolved_keys=resolved_keys,
            missing_keys=set(),
            errors=[]
        )
    
    # BFS でキーを解決
    queue = deque([tree.root_id])
    visited = set()
    
    while queue and missing_keys:
        node_id = queue.popleft()
        
        if node_id in visited:
            continue
        visited.add(node_id)
        
        node = tree.get_node(node_id)
        if not node:
            continue
        
        # 現在のノードが未解決のキーに該当するかチェック
        for key in list(missing_keys):
            if key in resolved_keys:
                continue
            
            if str(node.key) == key:
                value = _extract_value_for_formatting_pure(node.value)
                if value is not None:
                    resolved_keys[key] = str(value)
                    missing_keys.remove(key)
        
        # 親と子をキューに追加
        parent = tree.get_parent(node_id)
        if parent:
            parent_id = next((nid for nid, n in tree.nodes.items() if n == parent), None)
            if parent_id:
                queue.append(parent_id)
        
        children = tree.get_children(node_id)
        for child in children:
            child_id = next((nid for nid, n in tree.nodes.items() if n == child), None)
            if child_id:
                queue.append(child_id)
    
    # 最終フォーマット
    final_formatted, still_missing = format_with_missing_keys(template, **resolved_keys)
    
    return FormatResult(
        formatted_string=final_formatted,
        resolved_keys=resolved_keys,
        missing_keys=still_missing,
        errors=[]
    )


def format_node_value_pure(
    node: ConfigNodeData, 
    tree: ConfigTreeData,
    initial_values: Optional[Dict[str, str]] = None
) -> FormatResult:
    """
    ノードの値をフォーマットする純粋関数
    
    Args:
        node: フォーマット対象のノード
        tree: 設定ツリー（コンテキスト用）
        initial_values: 初期値
        
    Returns:
        FormatResult: フォーマット結果
    """
    template = _extract_template_from_node_pure(node)
    return format_string_pure(template, tree, initial_values)


def _extract_template_from_node_pure(node: ConfigNodeData) -> str:
    """
    ノードからテンプレート文字列を抽出する純粋関数
    
    Args:
        node: 対象ノード
        
    Returns:
        テンプレート文字列
    """
    if isinstance(node.value, str):
        return node.value
    elif isinstance(node.value, dict) and "value" in node.value:
        return str(node.value["value"])
    else:
        return str(node.value)


def _extract_value_for_formatting_pure(value: Any) -> Optional[str]:
    """
    フォーマット用の値を抽出する純粋関数
    
    Args:
        value: 抽出対象の値
        
    Returns:
        フォーマット用の文字列、またはNone
    """
    if isinstance(value, dict) and "value" in value:
        return str(value["value"])
    elif isinstance(value, (str, int, float)):
        return str(value)
    else:
        return None


def validate_config_tree_pure(tree: ConfigTreeData) -> List[str]:
    """
    設定ツリーの妥当性を検証する純粋関数
    
    Args:
        tree: 検証対象の設定ツリー
        
    Returns:
        エラーメッセージのリスト
    """
    errors = []
    
    # ルートノードの存在確認
    if tree.root_id not in tree.nodes:
        errors.append("Root node not found in tree")
        return errors
    
    # 各ノードの整合性確認
    for node_id, node in tree.nodes.items():
        # 親子関係の整合性確認
        if node.parent_id:
            if node.parent_id not in tree.nodes:
                errors.append(f"Node {node_id} references non-existent parent {node.parent_id}")
            else:
                parent = tree.nodes[node.parent_id]
                if node_id not in parent.children_ids:
                    errors.append(f"Parent-child relationship inconsistent for node {node_id}")
        
        # 子ノードの存在確認
        for child_id in node.children_ids:
            if child_id not in tree.nodes:
                errors.append(f"Node {node_id} references non-existent child {child_id}")
            else:
                child = tree.nodes[child_id]
                if child.parent_id != node_id:
                    errors.append(f"Child-parent relationship inconsistent for child {child_id}")
    
    return errors


def calculate_tree_metrics_pure(tree: ConfigTreeData) -> Dict[str, Any]:
    """
    設定ツリーのメトリクスを計算する純粋関数
    
    Args:
        tree: 対象の設定ツリー
        
    Returns:
        メトリクス辞書
    """
    node_count = len(tree.nodes)
    
    if node_count == 0:
        return {
            "node_count": 0,
            "max_depth": 0,
            "leaf_count": 0,
            "avg_children": 0,
            "total_matches": 0
        }
    
    # 深度計算
    def calculate_depth(node_id: str, visited: set) -> int:
        if node_id in visited:
            return 0  # 循環を避ける
        visited.add(node_id)
        
        node = tree.get_node(node_id)
        if not node or not node.children_ids:
            return 1
        
        return 1 + max(calculate_depth(child_id, visited.copy()) for child_id in node.children_ids)
    
    max_depth = calculate_depth(tree.root_id, set())
    
    # リーフノード数
    leaf_count = sum(1 for node in tree.nodes.values() if not node.children_ids)
    
    # 平均子ノード数
    total_children = sum(len(node.children_ids) for node in tree.nodes.values())
    avg_children = total_children / node_count if node_count > 0 else 0
    
    # 総マッチ数
    total_matches = sum(len(node.matches) for node in tree.nodes.values())
    
    return {
        "node_count": node_count,
        "max_depth": max_depth,
        "leaf_count": leaf_count,
        "avg_children": avg_children,
        "total_matches": total_matches
    }