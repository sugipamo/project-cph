from typing import Any, List, Optional, Union
from functools import lru_cache


class ConfigNode:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.matches, self.value = self._init_matches(name, value)
        self.next_nodes: List['ConfigNode'] = []
        self.parent: Optional['ConfigNode'] = None

    def _init_matches(self, name: str, value: Any):
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
        
        start_node = self.root
        for p in path:
            next_node = start_node.get_next_node(p)
            if next_node is None:
                break
            start_node = next_node


        if start_node is None:
            raise ValueError(f"ConfigResolver: {path}は存在しません")
        
        que = [(0, start_node)]
        visited = set()
        results = []
        while que:
            depth, node = que.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            if path[-1] in node.matches:
                match_rank = 1
                nnode = node
                while nnode.parent is not None and path[-match_rank] in nnode.parent.matches:
                    nnode = nnode.parent
                    match_rank += 1
                results.append((node, depth, match_rank))
            for next_nodes in node.next_nodes:
                que.append((depth + 1, next_nodes))

        if not results:
            return []

        max_match_rank = max(result[2] for result in results)
        results = [result for result in results if result[2] == max_match_rank]

        min_depth = min(result[1] for result in results)
        results = [result[0] for result in results if result[1] == min_depth]

        return results
# TODO 必須要素、必須ではないが一致度が高いものという形式で引数にいれられるようにする
    def resolve(self, path: Union[list, tuple]) -> list:
        return self._resolve(tuple(path))
