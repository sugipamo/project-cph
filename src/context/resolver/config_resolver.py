from typing import Any, List, Optional, Union
from collections import deque
from src.context.resolver.config_node import ConfigNode
from src.context.resolver.config_node_logic import init_matches, add_edge
from src.context.utils.format_utils import format_with_missing_keys

class ConfigResolver:
    def __init__(self, root: ConfigNode):
        self.root = root

    @classmethod
    def from_dict(cls, data: Any) -> 'ConfigResolver':
        if not isinstance(data, dict):
            raise ValueError("ConfigResolver: dict以外は未対応です")
        root = ConfigNode('root', data)
        init_matches(root, data)
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
                    init_matches(node, v)
                    add_edge(parent, node)
                    que.append((node, v))
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    node = ConfigNode(i, v)
                    init_matches(node, v)
                    add_edge(parent, node)
                    que.append((node, v))
        return cls(root)

    def resolve_by_match_desc(self, path: Union[list, tuple]) -> list:
        if not isinstance(path, (list, tuple)):
            raise TypeError(f"resolve_by_match_desc: pathはlistまたはtupleである必要があります: {path}")
        return self._resolve_by_match_desc(tuple(path))

    def resolve_best(self, path: Union[list, tuple]) -> Optional[ConfigNode]:
        results = self.resolve_by_match_desc(path)
        return results[0] if results else None

    def resolve_values(self, path: Union[list, tuple]) -> list:
        return [x.value for x in self.resolve_by_match_desc(path)]

    def resolve_format_string(self, node: 'ConfigNode', initial_values: dict = None) -> str:
        if isinstance(node.value, str):
            s = node.value
        elif isinstance(node.value, dict) and "value" in node.value:
            s = node.value["value"]
        else:
            return str(node.value)

        key_values = dict(initial_values) if initial_values else {}
        formatted, missing_keys = format_with_missing_keys(s, **key_values)
        if not missing_keys:
            return formatted

        queue = deque([node])
        visited = set()
        while queue and missing_keys:
            current = queue.popleft()
            if id(current) in visited:
                continue
            visited.add(id(current))

            for key in list(missing_keys):
                if key in key_values:
                    continue
                if current.key == key:
                    v = current.value
                    if isinstance(v, dict) and "value" in v:
                        key_values[key] = v["value"]
                    elif isinstance(v, str) or isinstance(v, int):
                        key_values[key] = v
                    missing_keys.remove(key)

            if current.parent:
                queue.append(current.parent)
            queue.extend(current.next_nodes)

        formatted, still_missing = format_with_missing_keys(s, **key_values)
        return formatted

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