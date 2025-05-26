from typing import Any, List, Optional, Union
from functools import lru_cache


class ConfigNode:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.matches, self.value = self._init_matches(name, value)
        self.next_nodes: List['ConfigNode'] = []
        self.parent: Optional['ConfigNode'] = None

    def __lt__(self, other: 'ConfigNode'):
        if not isinstance(other, ConfigNode):
            raise TypeError(f"ConfigNodeとの比較ができません: {other}")
        return self.name < other.name

    def _init_matches(self, name: str, value: Any) -> tuple[set[str], Any]:
        matches = set([name])
        if isinstance(value, dict) and "aliases" in value:
            for alias in value["aliases"]:
                matches.add(alias)
            del value["aliases"]
        return matches, value

    def add_edge(self, to_node: 'ConfigNode'):
        self.next_nodes.append(to_node)
        to_node.next_nodes.append(self)
        to_node.parent = self

    def get_next_nodes(self, name: str) -> List['ConfigNode']:
        results = []
        for node in self.next_nodes:
            if name == "*" or name in node.matches:
                results.append(node)
        return results
                
    def __repr__(self):
        return f"ConfigNode(name={self.name}, matches={self.matches}, next_nodes={self.next_nodes})"

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
                    for a in d["aliases"]:
                        parent.matches.add(a)
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
        """
        設定値ノードを取得する
        与えられたパス（リスト）の末尾に最もよく一致し、かつ最も浅いノードを返す

        Args:
            path (List[str]): 取得したい設定値へのパス

        Returns:
            list: 該当する設定値ノードのリスト

        """

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
        return self._resolve(tuple(path))
