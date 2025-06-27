from typing import Any, Optional

from src.domain.config_node_logic import add_edge, find_nearest_key_node, next_nodes_with_key, path


class ConfigNode:

    def __init__(self, key: str, value: Optional[Any]):
        self.key = key
        self.value = value
        self.parent: Optional[ConfigNode] = None
        self.next_nodes: list[ConfigNode] = []
        self.matches: set[str] = {key, '*'}

    def __repr__(self):
        return f'ConfigNode(key={self.key!r}, value={self.value!r}, matches={self.matches!r}, next_nodes={[x.key for x in self.next_nodes]})'

    def add_edge(self, to_node: 'ConfigNode'):
        add_edge(self, to_node)

    def next_nodes_with_key(self, key: str) -> list['ConfigNode']:
        return next_nodes_with_key(self, key)

    def path(self) -> list[str]:
        return path(self)

    def find_nearest_key_node(self, key: str) -> list['ConfigNode']:
        return find_nearest_key_node(self, key)
