from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque

class DependencyCalculator:
    """
    依存関係計算器
    循環依存検出と深度計算を行う
    """
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.reverse_graph: Dict[str, Set[str]] = {}
        self._build_dependency_graph()
    
    def _build_dependency_graph(self) -> None:
        """依存関係グラフを構築"""
        print("依存関係グラフを構築中...")
        
        self.dependency_graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        
        for file_path, imports in self.analyzer.file_imports.items():
            source_module = self.analyzer.path_to_module_name(file_path)
            
            for imported_module in imports:
                # 自己参照は除外
                if source_module != imported_module:
                    self.dependency_graph[source_module].add(imported_module)
                    self.reverse_graph[imported_module].add(source_module)
        
        print(f"グラフ構築完了: {len(self.dependency_graph)}モジュール")
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """循環依存を検出"""
        print("循環依存を検出中...")
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            """DFSで循環を検出"""
            if node in rec_stack:
                # 循環を発見
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                if dfs(neighbor, path + [neighbor]):
                    pass  # 循環を見つけたが、他の循環も探す
            
            rec_stack.remove(node)
            return False
        
        # すべてのノードから開始
        for module in self.dependency_graph:
            if module not in visited:
                dfs(module, [module])
        
        if cycles:
            print(f"循環依存検出: {len(cycles)}個のサイクル")
            for i, cycle in enumerate(cycles[:3]):  # 最初の3個だけ表示
                print(f"  サイクル{i+1}: {' -> '.join(cycle)}")
        else:
            print("循環依存は検出されませんでした")
        
        return cycles
    
    def calculate_dependency_depths(self, max_depth: int = 4) -> Dict[Path, int]:
        """各ファイルの依存深度を計算"""
        print("依存深度を計算中...")
        
        # モジュール名 -> 深度のマップ
        module_depths: Dict[str, int] = {}
        
        # 循環依存がある場合は処理しない
        cycles = self.detect_circular_dependencies()
        if cycles:
            print("循環依存があるため、深度計算をスキップします")
            return {}
        
        # トポロジカルソートで深度計算
        module_depths = self._calculate_depths_topological(max_depth)
        
        # ファイルパス -> 深度のマップに変換
        file_depths: Dict[Path, int] = {}
        
        for file_path in self.analyzer.file_imports.keys():
            module_name = self.analyzer.path_to_module_name(file_path)
            depth = module_depths.get(module_name, 0)
            file_depths[file_path] = depth
        
        # 深度サマリー表示
        depth_counts = defaultdict(int)
        for depth in file_depths.values():
            depth_counts[depth] += 1
        
        print("深度分布:")
        for depth in sorted(depth_counts.keys()):
            print(f"  深度{depth}: {depth_counts[depth]}ファイル")
        
        return file_depths
    
    def _calculate_depths_topological(self, max_depth: int) -> Dict[str, int]:
        """トポロジカルソートベースの深度計算"""
        # 入次数を計算
        in_degree = defaultdict(int)
        all_modules = set(self.dependency_graph.keys())
        
        # 依存される側のモジュールも含める
        for dependencies in self.dependency_graph.values():
            all_modules.update(dependencies)
        
        # 入次数初期化
        for module in all_modules:
            in_degree[module] = 0
        
        # 入次数計算：moduleがdepに依存している場合、moduleの入次数を増やす
        for module, deps in self.dependency_graph.items():
            in_degree[module] = len(deps)
        
        print(f"デバッグ: 入次数 = {dict(in_degree)}")
        
        # 入次数0のノードをキューに追加
        queue = deque()
        depths = {}
        
        for module in all_modules:
            if in_degree[module] == 0:
                queue.append(module)
                depths[module] = 0
        
        # トポロジカルソート実行
        processed = 0
        
        while queue:
            current = queue.popleft()
            processed += 1
            
            # このモジュールに依存しているモジュール（dependents）の深度を更新
            for dependent in self.reverse_graph.get(current, []):
                # dependent は current に依存している
                # つまり dependent の深度 = current の深度 + 1
                new_depth = min(depths[current] + 1, max_depth)
                
                if dependent not in depths:
                    depths[dependent] = new_depth
                else:
                    depths[dependent] = max(depths[dependent], new_depth)
                
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # すべてのモジュールが処理されたかチェック
        if processed != len(all_modules):
            print(f"警告: 一部のモジュールが処理されませんでした ({processed}/{len(all_modules)})")
        
        return depths
    
    def get_dependency_chain(self, module_name: str, max_length: int = 10) -> List[str]:
        """指定モジュールの依存チェーンを取得"""
        chain = []
        visited = set()
        
        def build_chain(current: str, current_chain: List[str]):
            if len(current_chain) >= max_length or current in visited:
                return
            
            visited.add(current)
            current_chain.append(current)
            
            # 最も深い依存を選択
            dependencies = self.dependency_graph.get(current, [])
            if dependencies:
                # 依存の中で最も多くの依存を持つものを選択
                best_dep = max(dependencies, 
                             key=lambda dep: len(self.dependency_graph.get(dep, [])))
                build_chain(best_dep, current_chain)
        
        build_chain(module_name, chain)
        return chain
    
    def get_statistics(self) -> Dict[str, any]:
        """依存関係の統計情報を取得"""
        total_modules = len(self.dependency_graph)
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        
        # 最も多くの依存を持つモジュール
        max_deps_module = None
        max_deps_count = 0
        
        for module, deps in self.dependency_graph.items():
            if len(deps) > max_deps_count:
                max_deps_count = len(deps)
                max_deps_module = module
        
        # 最も多くのモジュールから依存されているモジュール
        max_dependents_module = None
        max_dependents_count = 0
        
        for module, dependents in self.reverse_graph.items():
            if len(dependents) > max_dependents_count:
                max_dependents_count = len(dependents)
                max_dependents_module = module
        
        return {
            'total_modules': total_modules,
            'total_dependencies': total_dependencies,
            'avg_dependencies_per_module': total_dependencies / total_modules if total_modules > 0 else 0,
            'max_dependencies': {
                'module': max_deps_module,
                'count': max_deps_count
            },
            'most_depended_upon': {
                'module': max_dependents_module,
                'count': max_dependents_count
            }
        }
    
    def debug_print_graph(self, limit: int = 5) -> None:
        """デバッグ用: 依存関係グラフを表示"""
        print(f"\n依存関係グラフ（上位{limit}モジュール）:")
        
        count = 0
        for module, deps in self.dependency_graph.items():
            if count >= limit:
                break
            
            print(f"\n  {module}:")
            if not deps:
                print(f"    依存なし")
            else:
                for dep in sorted(deps):
                    print(f"    -> {dep}")
            
            count += 1
        
        # 統計情報も表示
        stats = self.get_statistics()
        print(f"\n統計情報:")
        print(f"  総モジュール数: {stats['total_modules']}")
        print(f"  総依存関係数: {stats['total_dependencies']}")
        print(f"  平均依存数: {stats['avg_dependencies_per_module']:.1f}")
        
        if stats['max_dependencies']['module']:
            print(f"  最多依存モジュール: {stats['max_dependencies']['module']} ({stats['max_dependencies']['count']}個)")
        
        if stats['most_depended_upon']['module']:
            print(f"  最多被依存モジュール: {stats['most_depended_upon']['module']} ({stats['most_depended_upon']['count']}個)")