from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.configuration.resolver.config_node import ConfigNode

def init_matches(node: 'ConfigNode', value: Any):
    if isinstance(value, dict) and "aliases" in value:
        aliases = value["aliases"]
        if not isinstance(aliases, list):
            raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
        for alias in aliases:
            node.matches.add(alias)
        del value["aliases"]
    node.value = value

def add_edge(parent: 'ConfigNode', to_node: 'ConfigNode'):
    if to_node in parent.next_nodes:
        raise ValueError(f"重複したエッジは許可されていません: {to_node}")
    parent.next_nodes.append(to_node)
    to_node.parent = parent

def path(node: 'ConfigNode') -> list[str]:
    path = []
    n = node
    while n.parent:
        path.append(n.key)
        n = n.parent
    return path[::-1]

def next_nodes_with_key(node: 'ConfigNode', key: str) -> list['ConfigNode']:
    return [n for n in node.next_nodes if key in n.matches]

def find_nearest_key_node(node: 'ConfigNode', key: str) -> list['ConfigNode']:
    que = deque([(0, node)])
    visited = set()
    find_depth = 1 << 31
    results = []
    while que:
        depth, n = que.popleft()
        if depth > find_depth:
            break
        if n in visited:
            continue
        visited.add(n)
        if key in n.matches:
            find_depth = min(find_depth, depth)
            results.append(n)
        for next_node in n.next_nodes:
            que.append((depth + 1, next_node))
    return results
