from typing import Any, Dict, List, Optional, Set, Union
from collections import deque

class ConfigNode:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.aliases: Set[str] = set()
        self.value = value
        self.edges: Dict[str, List[ConfigNode]] = {}

    def add_edge(self, to_node: 'ConfigNode'):
        self.edges[to_node.name] = to_node
        to_node.edges[self.name] = self

class ConfigResult:
    def __init__(self, node: ConfigNode):
        self.node = node

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any) -> 'ConfigResolver':
        root = ConfigNode('root', data)
        stack = [(root, data)]
        while stack:
            parent_node, value = stack.pop()
            value_dict = None

            if isinstance(value, dict):
                value_dict = value
            elif isinstance(value, list):
                value_dict = {str(i): v for i, v in enumerate(value)}

            if isinstance(value_dict, dict):
                aliases = value_dict.get('aliases')
                if not isinstance(aliases, list):
                    aliases = []
                for k, v in value_dict.items():
                    if k == 'aliases':
                        continue
                    child_node = ConfigNode(k, v)
                    for alias in aliases:
                        child_node.aliases.add(alias)
                    parent_node.add_edge(child_node)
                    stack.append((child_node, v))
        return cls(root)

    def resolve(self, path: List[str]) -> List[ConfigResult]:
        """
        ノード名一致でedge（child, alias, など）をたどるだけのBFS。
        dict/list/aliasesの違いを意識しないシンプルな構造。
        """
        if not path:
            return []
        
        target = path[-1]

        start_node = self.root
        
        for p in path:
            if p not in start_node.edges:
                break
            start_node = start_node.edges[p]

        queue = deque([(0, start_node)])
        visited: Set[int] = set()

        results = []
        ok_depth = -1
        while queue:
            depth, node = queue.popleft()
            if node.name == target or target in node.aliases:
                results.append(ConfigResult(node))
                ok_depth = depth
            if ok_depth != -1 and depth > ok_depth:
                break
            node_id = id(node)
            if node_id in visited:
                continue
            visited.add(node_id)
            for edge in node.edges.values():
                print(edge)
                queue.append((depth + 1, edge))
        return results
