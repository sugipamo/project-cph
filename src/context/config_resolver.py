from typing import Any, List, Optional, Union
from functools import lru_cache


class ConfigNode:
    def __init__(self, key: str, value: Optional[Any] = None):
        self._key = key
        self._matches, self._value = self._init_matches(key, value)
        self._next_nodes: List['ConfigNode'] = []
        self._parent: Optional['ConfigNode'] = None

    def __lt__(self, other: 'ConfigNode'):
        if not isinstance(other, ConfigNode):
            raise TypeError(f"ConfigNodeとの比較ができません: {other}")
        return self._key < other._key

    def _init_matches(self, key: str, value: Any) -> tuple[set[str], Any]:
        matches = set([key])
        if isinstance(value, dict) and "aliases" in value:
            aliases = value["aliases"]
            if not isinstance(aliases, list):
                raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
            for alias in aliases:
                matches.add(alias)
            del value["aliases"]
        return matches, value

    def add_edge(self, to_node: 'ConfigNode'):
        self._next_nodes.append(to_node)
        to_node._next_nodes.append(self)
        to_node._parent = self

    def get_next_nodes(self, key: str) -> List['ConfigNode']:
        results = []
        for node in self._next_nodes:
            if key == "*" or key in node._matches:
                results.append(node)
        return results
                
    @property
    def key(self) -> str:
        return self._key

    @property
    def matches(self) -> set[str]:
        return self._matches

    @property
    def value(self) -> Any:
        return self._value

    @property
    def next_nodes(self) -> List['ConfigNode']:
        return self._next_nodes

    @property
    def parent(self) -> Optional['ConfigNode']:
        return self._parent
    
    @lru_cache(maxsize=1000)
    def find_nearest_key_node(self, key: str) -> list['ConfigNode']:
        from collections import deque
        que = deque([(0, self)])
        visited = set()
        find_depth = 1 << 31
        results = []
        while que:
            depth, node = que.popleft()
            if depth > find_depth:
                break
            if node in visited:
                continue
            visited.add(node)
            if key in node.matches:
                find_depth = min(find_depth, depth)
                results.append(node)
            for next_node in node.next_nodes:
                que.append((depth + 1, next_node))
        return results

    def __repr__(self):
        return f"ConfigNode(key={self._key}, matches={self._matches}, next_nodes={self._next_nodes})"

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any) -> 'ConfigResolver':
        if not isinstance(data, dict):
            raise ValueError("ConfigResolver: dict以外は未対応です")
        root = ConfigNode('root', data)
        
        que = [(root, data)]
        while que:
            parent, d = que.pop()
            if isinstance(d, dict):
                if "aliases" in d:
                    aliases = d["aliases"]
                    if not isinstance(aliases, list):
                        raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
                    for a in aliases:
                        parent._matches.add(a)
                for k, v in d.items():
                    if k == "aliases":
                        continue
                    node = ConfigNode(k, v)
                    parent.add_edge(node)
                    que.append((node, v))
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    node = ConfigNode(i, v)
                    parent.add_edge(node)
                    que.append((node, v))

        return cls(root)

    @lru_cache(maxsize=1000)
    def _resolve(self, path: tuple) -> list:
        if not path:
            return []
        
        results = []
        que = [(path, 0, self.root)]
        visited = set()
        while que:
            path, match_rank, node = que.pop()
            if node in visited:
                continue
            visited.add(node)
            for i, p in enumerate(path):
                if p in node.matches:
                    if len(path) == 1:
                        results.append((match_rank, node))
                    else:
                        path = path[i+1:]
                        match_rank +=1
                        break
            for next_node in node.next_nodes:
                que.append((path, match_rank, next_node))

        results.sort(reverse=True)
        results = [x[1] for x in results]

        return results           

    
    def resolve(self, path: Union[list, tuple]) -> list:
        if not isinstance(path, (list, tuple)):
            raise TypeError(f"resolve: pathはlistまたはtupleである必要があります: {path}")
        return self._resolve(tuple(path))

    def resolve_values(self, path: Union[list, tuple]) -> list:
        return [x.value for x in self.resolve(path)]