from typing import Any, Optional


class ConfigNode:

    def __init__(self, key: str, value: Optional[Any]):
        self.key = key
        self.value = value
        self.parent: Optional[ConfigNode] = None
        self.next_nodes: list[ConfigNode] = []
        self.matches: set[str] = {key, '*'}

    def __repr__(self):
        return f'ConfigNode(key={self.key!r}, value={self.value!r}, matches={self.matches!r}, next_nodes={[x.key for x in self.next_nodes]})'
