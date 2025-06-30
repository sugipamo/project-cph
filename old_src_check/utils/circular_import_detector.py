from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import logging

from old_src.domain.models.broken_import import BrokenImport
from old_src.domain.models.module_info import ModuleInfo


class CircularImportDetector:
    """循環インポートを検知するサービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._import_graph: Dict[Path, Set[Path]] = defaultdict(set)
        self._module_to_path: Dict[str, Path] = {}
        
    def build_import_graph(
        self,
        modules: List[ModuleInfo],
        broken_imports: List[BrokenImport]
    ) -> None:
        """インポートグラフを構築"""
        self._import_graph.clear()
        self._module_to_path.clear()
        
        # モジュール名からパスへのマッピングを作成
        for module in modules:
            self._module_to_path[module.module_path] = module.file_path
            
        # 正常なインポートをグラフに追加
        for module in modules:
            # imported_modules からインポート情報を取得
            for imported_module in module.imported_modules:
                target_path = self._module_to_path.get(imported_module)
                if target_path and target_path != module.file_path:
                    self._import_graph[module.file_path].add(target_path)
                    
    def detect_circular_imports(self) -> List[List[Path]]:
        """循環インポートを検知"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: Path, path: List[Path]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self._import_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # 循環を検出
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    
            rec_stack.remove(node)
            
        for node in self._import_graph:
            if node not in visited:
                dfs(node, [])
                
        # 重複する循環を除去
        unique_cycles = []
        seen_cycles = set()
        
        for cycle in cycles:
            # 循環を正規化（最小のパスから開始）
            min_idx = cycle.index(min(cycle))
            normalized = tuple(cycle[min_idx:] + cycle[:min_idx])
            
            if normalized not in seen_cycles:
                seen_cycles.add(normalized)
                unique_cycles.append(list(normalized)[:-1])  # 最後の重複要素を除去
                
        return unique_cycles
    
    def _resolve_import_to_path(self, import_str: str, from_file: Path) -> Optional[Path]:
        """インポート文字列をファイルパスに解決"""
        # "from X import Y" 形式の処理
        if " import " in import_str:
            module_path = import_str.split(" import ")[0].replace("from ", "").strip()
        else:
            # "import X" 形式の処理
            module_path = import_str.replace("import ", "").strip()
            
        # 相対インポートの処理
        if module_path.startswith("."):
            level = len(module_path) - len(module_path.lstrip("."))
            relative_part = module_path.lstrip(".")
            
            # 親ディレクトリを遡る
            parent = from_file.parent
            for _ in range(level):
                parent = parent.parent
                
            if relative_part:
                # 相対パスを絶対パスに変換
                parts = list(parent.parts) + relative_part.split(".")
                module_path = ".".join(parts)
            else:
                module_path = ".".join(parent.parts)
                
        # モジュールパスからファイルパスを取得
        return self._module_to_path.get(module_path)
    
    def check_would_create_circular_import(
        self,
        from_file: Path,
        to_module: str,
        modules: List[ModuleInfo]
    ) -> bool:
        """特定のインポートが循環を作成するかチェック"""
        # 一時的にインポートを追加
        self.build_import_graph(modules, [])
        
        target_path = self._module_to_path.get(to_module)
        if not target_path:
            return False
            
        # 既に循環が存在するかチェック
        if target_path in self._import_graph.get(from_file, set()):
            return False  # 既存のインポート
            
        # 逆方向のパスが存在するかチェック（簡易的な循環検出）
        return self._has_path(target_path, from_file)
    
    def _has_path(self, start: Path, end: Path) -> bool:
        """startからendへのパスが存在するかチェック"""
        if start == end:
            return True
            
        visited = set()
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
                
            if current in visited:
                continue
                
            visited.add(current)
            queue.extend(self._import_graph.get(current, set()))
            
        return False