from typing import Any, List, Optional, Set

class ConfigNode:
    def __init__(self, key: str, value: Optional[Any] = None):
        self.key = key
        self.value = value
        self.parent: Optional['ConfigNode'] = None
        self.next_nodes: List['ConfigNode'] = []
        self.matches: Set[str] = set([key, "*"])

    def __repr__(self):
        return f"ConfigNode(key={self.key!r}, value={self.value!r}, matches={self.matches!r}, next_nodes={[x.key for x in self.next_nodes]})"

    def add_edge(self, to_node: 'ConfigNode'):
        ConfigNodeLogic.add_edge(self, to_node)

    def next_nodes_with_key(self, key: str) -> List['ConfigNode']:
        return ConfigNodeLogic.next_nodes_with_key(self, key)

    def path(self) -> List[str]:
        return ConfigNodeLogic.path(self)

    def find_nearest_key_node(self, key: str) -> List['ConfigNode']:
        return ConfigNodeLogic.find_nearest_key_node(self, key)

class ConfigNodeLogic:
    @staticmethod
    def init_matches(node: ConfigNode, value: Any):
        if isinstance(value, dict) and "aliases" in value:
            aliases = value["aliases"]
            if not isinstance(aliases, list):
                raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
            for alias in aliases:
                node.matches.add(alias)
            del value["aliases"]
        node.value = value

    @staticmethod
    def add_edge(parent: ConfigNode, to_node: ConfigNode):
        if to_node in parent.next_nodes:
            raise ValueError(f"重複したエッジは許可されていません: {to_node}")
        parent.next_nodes.append(to_node)
        to_node.parent = parent

    @staticmethod
    def path(node: ConfigNode) -> List[str]:
        path = []
        n = node
        while n.parent:
            path.append(n.key)
            n = n.parent
        return path[::-1]

    @staticmethod
    def next_nodes_with_key(node: ConfigNode, key: str) -> List['ConfigNode']:
        return [n for n in node.next_nodes if key in n.matches]

    @staticmethod
    def find_nearest_key_node(node: 'ConfigNode', key: str) -> List['ConfigNode']:
        from functools import lru_cache
        from collections import deque
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