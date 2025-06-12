"""設定解決機能 - ConfigNodeの新設定システム統合版"""
from collections import deque
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from ..core.execution_configuration import ExecutionConfiguration


@dataclass
class ConfigNode:
    """設定ノード - 階層設定の解決のための軽量版"""
    key: str
    value: Optional[Any] = None
    parent: Optional['ConfigNode'] = None
    next_nodes: List['ConfigNode'] = None
    matches: set = None
    
    def __post_init__(self):
        if self.next_nodes is None:
            self.next_nodes = []
        if self.matches is None:
            self.matches = {self.key, "*"}
    
    def __repr__(self):
        return f"ConfigNode(key={self.key!r}, value={self.value!r}, matches={self.matches!r}, next_nodes={[x.key for x in self.next_nodes]})"
    
    def add_edge(self, to_node: 'ConfigNode'):
        """エッジ（子ノード）を追加"""
        if to_node in self.next_nodes:
            raise ValueError(f"重複したエッジは許可されていません: {to_node}")
        self.next_nodes.append(to_node)
        to_node.parent = self
    
    def next_nodes_with_key(self, key: str) -> List['ConfigNode']:
        """指定キーにマッチする子ノードを取得"""
        return [n for n in self.next_nodes if key in n.matches]
    
    def path(self) -> List[str]:
        """ルートからこのノードまでのパスを取得"""
        path = []
        n = self
        while n.parent:
            path.append(n.key)
            n = n.parent
        return path[::-1]
    
    def find_nearest_key_node(self, key: str) -> List['ConfigNode']:
        """最も近いキーノードを幅優先検索で取得"""
        que = deque([(0, self)])
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


class ConfigurationResolver:
    """新設定システム用の設定解決クラス"""
    
    def __init__(self, config: ExecutionConfiguration):
        self.config = config
        self._root_node: Optional[ConfigNode] = None
    
    def create_config_root_from_dict(self, data: Any) -> ConfigNode:
        """辞書から設定ツリーを構築"""
        if not isinstance(data, dict):
            raise ValueError("ConfigResolver: dict以外は未対応です")
            
        root = ConfigNode('root', data)
        self._init_matches(root, data)
        
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
                    self._init_matches(node, v)
                    parent.add_edge(node)
                    que.append((node, v))
                    
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    node = ConfigNode(str(i), v)
                    self._init_matches(node, v)
                    parent.add_edge(node)
                    que.append((node, v))
                    
        self._root_node = root
        return root
    
    def resolve_by_match_desc(self, path: Union[List, tuple]) -> List[ConfigNode]:
        """パスに基づいてノードを解決（マッチング降順）"""
        if not isinstance(path, (list, tuple)):
            raise TypeError(f"resolve_by_match_desc: pathはlistまたはtupleである必要があります: {path}")
        
        if self._root_node is None:
            raise RuntimeError("設定ツリーが初期化されていません")
            
        return self._resolve_by_match_desc(self._root_node, tuple(path))
    
    def resolve_best(self, path: Union[List, tuple]) -> Optional[ConfigNode]:
        """最適なノードを1つ解決"""
        results = self.resolve_by_match_desc(path)
        return results[0] if results else None
    
    def resolve_values(self, path: Union[List, tuple]) -> List[Any]:
        """パスに対応する値のリストを取得"""
        return [x.value for x in self.resolve_by_match_desc(path)]
    
    def resolve_value(self, path: Union[List, tuple], default: Any = None) -> Any:
        """パスに対応する単一の値を取得"""
        values = self.resolve_values(path)
        return values[0] if values else default
    
    def format_with_resolver(self, template: str) -> str:
        """設定解決と変数展開を統合した文字列フォーマット"""
        from ..expansion.template_expander import TemplateExpander
        
        # 基本的な変数展開
        expander = TemplateExpander(self.config)
        result = expander.expand_all(template)
        
        # ConfigNode からの追加情報があれば統合
        # (この部分は必要に応じて拡張)
        
        return result
    
    def _init_matches(self, node: ConfigNode, value: Any):
        """ノードのマッチング情報を初期化"""
        if isinstance(value, dict) and "aliases" in value:
            aliases = value["aliases"]
            if not isinstance(aliases, list):
                raise TypeError(f"aliasesはlist型である必要があります: {aliases}")
            for alias in aliases:
                node.matches.add(alias)
        node.value = value
    
    def _resolve_by_match_desc(self, root: ConfigNode, path: tuple) -> List[ConfigNode]:
        """内部的なパス解決実装"""
        if not path:
            return [root]
            
        current_key = path[0]
        remaining_path = path[1:]
        
        # 現在のキーにマッチする子ノードを取得
        matching_nodes = root.next_nodes_with_key(current_key)
        
        results = []
        for node in matching_nodes:
            if remaining_path:
                # 再帰的に残りのパスを解決
                sub_results = self._resolve_by_match_desc(node, remaining_path)
                results.extend(sub_results)
            else:
                # パスの終端に到達
                results.append(node)
        
        # マッチング度合いで並び替え（完全一致を優先）
        def match_score(node):
            # より具体的なマッチを高得点にする
            if current_key == node.key:
                return 1000  # 完全一致
            elif current_key in node.matches:
                return 100   # エイリアス一致
            elif "*" in node.matches:
                return 10    # ワイルドカード一致
            else:
                return 0     # 一致なし
        
        results.sort(key=match_score, reverse=True)
        return results


def create_config_resolver(config: ExecutionConfiguration, env_json: Dict[str, Any]) -> ConfigurationResolver:
    """新設定システム用の設定解決クラスを作成
    
    Args:
        config: 実行設定
        env_json: 環境設定JSON
        
    Returns:
        ConfigurationResolver: 設定解決クラス
    """
    resolver = ConfigurationResolver(config)
    
    if env_json:
        # env_json から設定ツリーを構築
        resolver.create_config_root_from_dict(env_json)
    
    return resolver