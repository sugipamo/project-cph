from typing import Any, Dict, List, Optional, Set, Union
from collections import deque

class ConfigNode:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.aliases: Set[str] = set()
        self.value = value
        self.edges: Dict[str, List['ConfigNode']] = {}

    def add_edge(self, to_node: 'ConfigNode'):
        if to_node.name not in self.edges:
            self.edges[to_node.name] = []
        self.edges[to_node.name].append(to_node)
        # 逆方向も追加（必要なら）
        if self.name not in to_node.edges:
            to_node.edges[self.name] = []
        to_node.edges[self.name].append(self)

class ConfigResult:
    def __init__(self, node: ConfigNode):
        self.node = node

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any) -> 'ConfigResolver':
        if not isinstance(data, dict):
            raise ValueError("ConfigResolver: dict以外は未対応です")
        root = ConfigNode('root', data)
        stack = [(root, data)]
        while stack:
            parent_node, value = stack.pop()
            value_dict = None

            if isinstance(value, dict):
                value_dict = value
            elif isinstance(value, list):
                raise ValueError("ConfigResolver: list値は未対応です")

            if isinstance(value_dict, dict):
                for k, v in value_dict.items():
                    if k == 'aliases':
                        # 親ノード自身のaliases
                        aliases = v if isinstance(v, list) else []
                        for alias in aliases:
                            parent_node.aliases.add(alias)
                        continue
                    child_node = ConfigNode(k, v)
                    # 子ノードのaliases
                    aliases = v.get('aliases') if isinstance(v, dict) else []
                    if not isinstance(aliases, list):
                        aliases = []
                    for alias in aliases:
                        child_node.aliases.add(alias)
                    parent_node.add_edge(child_node)
                    stack.append((child_node, v))
        return cls(root)

    def resolve(self, path: List[str]) -> List[ConfigResult]:
        if not path or not isinstance(path, list):
            raise ValueError("resolve: pathは空やNone、list以外は不可")
        target = path[-1]
        # まずroot直下でpath[0]（ノード名またはエイリアス）に一致するノードを列挙
        start_nodes = []
        for nodes in self.root.edges.values():
            for node in nodes:
                if node.name == path[0] or path[0] in node.aliases:
                    start_nodes.append(node)
        if not start_nodes:
            return []
        # パスの途中もノード名またはエイリアス一致でたどる
        for p in path[1:-1]:
            next_nodes = []
            for node in start_nodes:
                for nodes in node.edges.values():
                    for child in nodes:
                        if child.name == p or p in child.aliases:
                            next_nodes.append(child)
            if not next_nodes:
                return []
            start_nodes = next_nodes
        # 完全一致しなかった場合、そこからBFSでtargetを探す
        results = []
        for start_node in start_nodes:
            queue = deque([(0, start_node)])
            visited: Set[int] = set()
            found_depth = -1
            while queue:
                depth, node = queue.popleft()
                # 最後の要素もエイリアス許容
                if node.name == target or target in node.aliases:
                    results.append(ConfigResult(node))
                    found_depth = depth if found_depth == -1 else found_depth
                if found_depth != -1 and depth > found_depth:
                    break
                node_id = id(node)
                if node_id in visited:
                    continue
                visited.add(node_id)
                for edge_nodes in node.edges.values():
                    for edge in edge_nodes:
                        queue.append((depth + 1, edge))
            if results:
                break  # 最初に見つかった深さのみ返す
        return results
