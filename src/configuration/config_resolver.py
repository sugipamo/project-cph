from collections import deque
from typing import Any, Optional, Union

from src.core.configuration.config_node import ConfigNode
from src.core.configuration.config_node_logic import add_edge, init_matches
from src.operations.pure.formatters import format_with_missing_keys


def create_config_root_from_dict(data: Any) -> ConfigNode:
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
    return root

def resolve_by_match_desc(root: ConfigNode, path: Union[list, tuple]) -> list:
    if not isinstance(path, (list, tuple)):
        raise TypeError(f"resolve_by_match_desc: pathはlistまたはtupleである必要があります: {path}")
    return _resolve_by_match_desc(root, tuple(path))

def resolve_best(root: ConfigNode, path: Union[list, tuple]) -> Optional[ConfigNode]:
    """Resolve the best matching config node for given path.

    Args:
        root: Root config node
        path: Path to resolve

    Returns:
        Best matching config node

    Raises:
        ValueError: If no matching config node is found
    """
    results = resolve_by_match_desc(root, path)
    if not results:
        raise ValueError(f"No matching config node found for path: {path}")
    return results[0]

def resolve_values(root: ConfigNode, path: Union[list, tuple]) -> list:
    return [x.value for x in resolve_by_match_desc(root, path)]

def resolve_formatted_string(s: str, root: ConfigNode, initial_values: Optional[dict]) -> str:
    """文字列sの{key}形式の変数をフォーマットする純粋関数。

    Args:
        s: フォーマットする文字列
        root: ConfigNodeのルート
        initial_values: 初期値（ユーザーインプットなど）

    Returns:
        フォーマット済みの文字列
    """
    if initial_values is None:
        raise ValueError("initial_values cannot be None")
    key_values = dict(initial_values)
    formatted, missing_keys = format_with_missing_keys(s, **key_values)

    if not missing_keys:
        return formatted

    # BFSで未解決のキーを探す
    queue = deque([root])
    visited = set()

    while queue and missing_keys:
        current = queue.popleft()
        if id(current) in visited:
            continue
        visited.add(id(current))

        # 現在のノードが未解決のキーに該当するかチェック
        for key in list(missing_keys):
            if key in key_values:
                continue
            if current.key == key:
                v = current.value
                if isinstance(v, dict) and "value" in v:
                    key_values[key] = str(v["value"])
                elif v is not None:
                    key_values[key] = str(v)
                missing_keys.remove(key)

        # 親ノードと子ノードをキューに追加
        if current.parent:
            queue.append(current.parent)
        queue.extend(current.next_nodes)

    formatted, _ = format_with_missing_keys(s, **key_values)
    return formatted

def resolve_format_string(node: 'ConfigNode', initial_values: Optional[dict]) -> str:
    if isinstance(node.value, str):
        s = node.value
    elif isinstance(node.value, dict) and "value" in node.value:
        value = node.value["value"]
        if isinstance(value, str):
            s = value
        else:
            return str(value)
    else:
        return str(node.value)

    if initial_values is None:
        raise ValueError("initial_values cannot be None")
    key_values = dict(initial_values)
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
                elif isinstance(v, (str, int)):
                    key_values[key] = v
                missing_keys.remove(key)

        if current.parent:
            queue.append(current.parent)
        queue.extend(current.next_nodes)

    formatted, still_missing = format_with_missing_keys(s, **key_values)
    return formatted

def _resolve_by_match_desc(root: ConfigNode, path: tuple) -> list:
    if not path:
        return []
    orig_path = path
    results = []
    que = [(path, 1, root)]
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
