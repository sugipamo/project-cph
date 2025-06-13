"""グラフクエリの純粋関数 - RequestExecutionGraphから分離"""
from typing import Dict, List, Set, Any
from collections import deque


def get_dependencies_pure(reverse_adjacency_list: Dict[str, Set[str]], node_id: str) -> List[str]:
    """指定ノードが依存するノードのリストを取得（純粋関数）
    
    Args:
        reverse_adjacency_list: 逆隣接リスト
        node_id: ノードID
        
    Returns:
        依存ノードIDリスト
    """
    return list(reverse_adjacency_list.get(node_id, set()))


def get_dependents_pure(adjacency_list: Dict[str, Set[str]], node_id: str) -> List[str]:
    """指定ノードに依存するノードのリストを取得（純粋関数）
    
    Args:
        adjacency_list: 隣接リスト
        node_id: ノードID
        
    Returns:
        被依存ノードIDリスト
    """
    return list(adjacency_list.get(node_id, set()))


def calculate_execution_order(nodes: Dict[str, Any], adjacency_list: Dict[str, Set[str]]) -> List[str]:
    """トポロジカルソートによる実行順序を計算（純粋関数）
    
    Kahnのアルゴリズムを使用
    
    Args:
        nodes: ノード辞書
        adjacency_list: 隣接リスト
        
    Returns:
        実行順序リスト
        
    Raises:
        ValueError: 循環依存がある場合
    """
    # 入次数を計算
    in_degree = dict.fromkeys(nodes, 0)
    for node in nodes:
        for neighbor in adjacency_list.get(node, set()):
            if neighbor in in_degree:
                in_degree[neighbor] += 1
    
    # 入次数が0のノードをキューに追加
    queue = deque([node for node in nodes if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        # 隣接ノードの入次数を減らす
        for neighbor in adjacency_list.get(node, set()):
            if neighbor in in_degree:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
    
    # すべてのノードが処理されたか確認
    if len(result) != len(nodes):
        raise ValueError("Graph has cycles or disconnected components")
    
    return result


def calculate_parallel_groups(nodes: Dict[str, Any], 
                            adjacency_list: Dict[str, Set[str]],
                            reverse_adjacency_list: Dict[str, Set[str]]) -> List[List[str]]:
    """並行実行可能なノードグループを計算（純粋関数）
    
    Args:
        nodes: ノード辞書
        adjacency_list: 隣接リスト
        reverse_adjacency_list: 逆隣接リスト
        
    Returns:
        並列グループリスト
        
    Raises:
        ValueError: 実行不可能な状態の場合
    """
    execution_order = calculate_execution_order(nodes, adjacency_list)
    groups = []
    remaining = set(execution_order)
    completed = set()
    
    while remaining:
        # 依存関係が満たされているノードを見つける
        ready_nodes = []
        for node_id in remaining:
            dependencies = set(get_dependencies_pure(reverse_adjacency_list, node_id))
            if dependencies.issubset(completed):
                ready_nodes.append(node_id)
        
        if not ready_nodes:
            raise ValueError("Unable to find executable nodes - possible deadlock")
        
        groups.append(ready_nodes)
        completed.update(ready_nodes)
        remaining -= set(ready_nodes)
    
    return groups


def find_reachable_nodes(adjacency_list: Dict[str, Set[str]], start_node: str) -> Set[str]:
    """開始ノードから到達可能なノードを探索（純粋関数）
    
    Args:
        adjacency_list: 隣接リスト
        start_node: 開始ノード
        
    Returns:
        到達可能ノード集合
    """
    visited = set()
    queue = deque([start_node])
    
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        
        visited.add(node)
        neighbors = adjacency_list.get(node, set())
        queue.extend(neighbors - visited)
    
    return visited


def calculate_node_levels(nodes: Dict[str, Any],
                         reverse_adjacency_list: Dict[str, Set[str]]) -> Dict[str, int]:
    """各ノードのレベル（深さ）を計算（純粋関数）
    
    Args:
        nodes: ノード辞書
        reverse_adjacency_list: 逆隣接リスト
        
    Returns:
        ノードID -> レベルの辞書
    """
    levels = {}
    execution_order = calculate_execution_order(nodes, reverse_adjacency_list)
    
    for node_id in execution_order:
        dependencies = get_dependencies_pure(reverse_adjacency_list, node_id)
        
        if not dependencies:
            # 依存関係なし（レベル0）
            levels[node_id] = 0
        else:
            # 依存ノードの最大レベル + 1
            levels[node_id] = max(levels.get(dep, 0) for dep in dependencies) + 1
    
    return levels


def find_critical_path(nodes: Dict[str, Any],
                      adjacency_list: Dict[str, Set[str]],
                      reverse_adjacency_list: Dict[str, Set[str]]) -> List[str]:
    """クリティカルパスを発見（純粋関数）
    
    最も深いレベルに到達するパス
    
    Args:
        nodes: ノード辞書
        adjacency_list: 隣接リスト
        reverse_adjacency_list: 逆隣接リスト
        
    Returns:
        クリティカルパスのノードIDリスト
    """
    levels = calculate_node_levels(nodes, reverse_adjacency_list)
    
    if not levels:
        return []
    
    # 最深レベルのノードを見つける
    max_level = max(levels.values())
    deepest_nodes = [node for node, level in levels.items() if level == max_level]
    
    # 最深ノードから逆方向にパスを構築
    critical_path = []
    current_node = deepest_nodes[0]  # 複数ある場合は最初のものを選択
    
    while current_node is not None:
        critical_path.append(current_node)
        
        # 依存ノードの中で最も深いものを選択
        dependencies = get_dependencies_pure(reverse_adjacency_list, current_node)
        if not dependencies:
            break
        
        # 最も深い依存ノードを次のノードとする
        current_node = max(dependencies, key=lambda n: levels.get(n, -1))
    
    critical_path.reverse()
    return critical_path


def count_paths_between_nodes(adjacency_list: Dict[str, Set[str]], 
                             start: str, end: str, max_depth: int = 10) -> int:
    """2ノード間のパス数を計算（純粋関数）
    
    Args:
        adjacency_list: 隣接リスト
        start: 開始ノード
        end: 終了ノード
        max_depth: 最大探索深度
        
    Returns:
        パス数
    """
    if start == end:
        return 1
    
    # DFSでパス数をカウント
    def count_paths_dfs(current: str, target: str, visited: Set[str], depth: int) -> int:
        if depth > max_depth:
            return 0
        
        if current == target:
            return 1
        
        visited.add(current)
        total_paths = 0
        
        for neighbor in adjacency_list.get(current, set()):
            if neighbor not in visited:
                total_paths += count_paths_dfs(neighbor, target, visited.copy(), depth + 1)
        
        return total_paths
    
    return count_paths_dfs(start, end, set(), 0)