from typing import Any, Dict, List, Optional, Set, Union
from collections import deque

class ConfigEdge:
    def __init__(self, from_node: 'ConfigNode', to_node: 'ConfigNode', edge_type: str):
        self.from_node = from_node
        self.to_node = to_node
        self.edge_type = edge_type  # 'parent', 'child', 'shortcut' など

class ConfigNode:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.value = value
        self.edges: List[ConfigEdge] = []
        self.children: Dict[str, 'ConfigNode'] = {}  # 属性名→子ノード
        self.list_children: List['ConfigNode'] = []  # リスト要素
        self.parent: Optional['ConfigNode'] = None

    def add_edge(self, to_node: 'ConfigNode', edge_type: str):
        edge = ConfigEdge(self, to_node, edge_type)
        self.edges.append(edge)

    def add_child(self, key: str, child: 'ConfigNode'):
        self.children[key] = child
        child.parent = self

    def add_list_child(self, child: 'ConfigNode'):
        self.list_children.append(child)
        child.parent = self

    def get_edges(self, edge_type: Optional[str] = None) -> List[ConfigEdge]:
        if edge_type is None:
            return self.edges
        return [e for e in self.edges if e.edge_type == edge_type]

class ConfigResult:
    def __init__(self, node: ConfigNode):
        self.node = node

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any, root_name: str = 'root') -> 'ConfigResolver':
        root = ConfigNode(root_name, data)
        stack = [(root, data)]  # (親ノード, value)
        while stack:
            parent_node, value = stack.pop()
            if isinstance(value, dict):
                for k, v in value.items():
                    child_node = ConfigNode(k, v)
                    parent_node.add_child(k, child_node)
                    stack.append((child_node, v))
            elif isinstance(value, list):
                for idx, v in enumerate(value):
                    child_node = ConfigNode(str(idx), v)
                    parent_node.add_list_child(child_node)
                    stack.append((child_node, v))
        return cls(root)

    def resolve(self, path: List[str]) -> List[ConfigResult]:
        """
        ConfigNode間のBFSのみで、パスの最後の属性名が一致するノードを返す。
        BFSはcollections.dequeで実装。
        """
        if not path:
            return []
        target_attr = path[-1]
        start_node = self._find_start_node(path)
        if start_node is None:
            return []
        results = []
        queue = deque([start_node])
        visited: Set[int] = set()
        found_level = False
        while queue and not found_level:
            next_queue = deque()
            level_results = []
            while queue:
                node = queue.popleft()
                node_id = id(node)
                if node_id in visited:
                    continue
                visited.add(node_id)
                # dict属性
                if target_attr in node.children:
                    level_results.append(ConfigResult(node.children[target_attr]))
                # list属性
                if node.list_children:
                    for idx, child in enumerate(node.list_children):
                        if str(idx) == target_attr:
                            level_results.append(ConfigResult(child))
                        next_queue.append(child)
                # dictの他の子も次レベル探索
                for child in node.children.values():
                    next_queue.append(child)
            if level_results:
                results.extend(level_results)
                found_level = True
            else:
                queue = next_queue
        return results

    def _find_start_node(self, path: List[str]) -> Optional[ConfigNode]:
        """
        パスの先頭から順にノードをたどり、存在しない場合は1つずつさかのぼる。
        戻り値: 開始ノード
        """
        node = self.root
        idx = 0
        while idx < len(path) - 1:
            key = path[idx]
            found = False
            # dict属性
            if key in node.children:
                node = node.children[key]
                found = True
            # list属性
            elif node.list_children:
                try:
                    i = int(key)
                    node = node.list_children[i]
                    found = True
                except (ValueError, IndexError):
                    pass
            if not found:
                break
            idx += 1
        return node 