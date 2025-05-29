from typing import Any, Optional, List, Set
from .config_node_logic import add_edge, next_nodes_with_key, path, find_nearest_key_node

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
        add_edge(self, to_node)

    def next_nodes_with_key(self, key: str) -> List['ConfigNode']:
        return next_nodes_with_key(self, key)

    def path(self) -> List[str]:
        return path(self)

    def find_nearest_key_node(self, key: str) -> List['ConfigNode']:
        return find_nearest_key_node(self, key)
