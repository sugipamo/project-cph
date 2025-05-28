from typing import Any, List, Optional, Union, Set
from functools import lru_cache


class ConfigNode:
    def __init__(self, key: str, value: Optional[Any] = None):
        self.key = key
        self.value = value
        self.parent: Optional['ConfigNode'] = None
        self.next_nodes: List['ConfigNode'] = []
        self._matches: Set[str] = set([key, "*"])
        ConfigNodeLogic.init_matches(self, value)

    @property
    def matches(self) -> Set[str]:
        return self._matches

    def add_edge(self, to_node: 'ConfigNode'):
        ConfigNodeLogic.add_edge(self, to_node)

    def next_nodes_with_key(self, key: str) -> List['ConfigNode']:
        return ConfigNodeLogic.next_nodes_with_key(self, key)

    def path(self) -> List[str]:
        return ConfigNodeLogic.path(self)

    def find_nearest_key_node(self, key: str) -> List['ConfigNode']:
        return ConfigNodeLogic.find_nearest_key_node(self, key)

    def __repr__(self):
        return f"ConfigNode(key={self.key!r}, value={self.value!r}, matches={self.matches!r}, next_nodes={[x.key for x in self.next_nodes]})"

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
    def next_nodes_with_key(node: ConfigNode, key: str) -> List[ConfigNode]:
        return [n for n in node.next_nodes if key in n.matches]

    @staticmethod
    @lru_cache(maxsize=1000)
    def find_nearest_key_node(node: ConfigNode, key: str) -> List[ConfigNode]:
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

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any) -> 'ConfigResolver':
        if not isinstance(data, dict):
            raise ValueError("ConfigResolver: dict以外は未対応です")
        root = ConfigNode('root', data)
        ConfigNodeLogic.init_matches(root, data)
        que = [(root, data)]
        while que:
            parent, d = que.pop()
            if isinstance(d, dict):
                if "aliases" in d:
                    aliases = d["aliases"]
                    if not isinstance(aliases, list):
                        raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
                    for a in aliases:
                        parent.matches.add(a)
                for k, v in d.items():
                    if k == "aliases":
                        continue
                    node = ConfigNode(k, v)
                    ConfigNodeLogic.init_matches(node, v)
                    ConfigNodeLogic.add_edge(parent, node)
                    que.append((node, v))
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    node = ConfigNode(i, v)
                    ConfigNodeLogic.init_matches(node, v)
                    ConfigNodeLogic.add_edge(parent, node)
                    que.append((node, v))
        return cls(root)

    @lru_cache(maxsize=1000)
    def _resolve_by_match_desc(self, path: tuple) -> list:
        if not path:
            return []
        orig_path = path
        results = []
        que = [(path, 1, self.root)]
        visited = set()
        while que:
            path, match_rank, node = que.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            for next_node in node.next_nodes:
                isok = False
                for i in range(len(path)):
                    if path[i] in next_node.matches:
                        isok = True
                        que.append((path[i+1:], match_rank + (1 << (len(orig_path) - i)), next_node))
                        results.append((match_rank + (1 << (len(orig_path) - i)), next_node))
                if not isok:
                    que.append((path, match_rank, next_node))
        results = list(results)
        results.sort(key=lambda x: x[0], reverse=True)
        results = [x[1] for x in results]
        return results

    def resolve_by_match_desc(self, path: Union[list, tuple]) -> list:
        """
        マッチ度降順でConfigNodeのリストを返す
        """
        if not isinstance(path, (list, tuple)):
            raise TypeError(f"resolve_by_match_desc: pathはlistまたはtupleである必要があります: {path}")
        return self._resolve_by_match_desc(tuple(path))

    def resolve_best(self, path: Union[list, tuple]) -> Optional[ConfigNode]:
        """
        最もマッチ度の高いConfigNodeを1つだけ返す（なければNone）
        """
        results = self.resolve_by_match_desc(path)
        return results[0] if results else None

    def resolve_values(self, path: Union[list, tuple]) -> list:
        return [x.value for x in self.resolve_by_match_desc(path)]
    
if __name__ == "__main__":
    data = {
        "a": {
            "aliases": ["b", "c"],
            "value": "a"
        }
    }

    data = {
        "python": {
            "env_type": {
                "docker": {
                    "aliases": ["container"],
                    "value": 1
                },
            },
            "local": {"value": 2}
        },
        "java": {
            "env_type": {
                "docker": {"value": 3}
            }
        }
    }

    resolver = ConfigResolver.from_dict(data)

    [print(x) for x in resolver.resolve_by_match_desc(["docker"])]