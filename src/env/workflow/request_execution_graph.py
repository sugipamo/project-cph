"""
リクエスト実行グラフ

依存関係を持つリクエストのグラフ構造と実行戦略を提供
"""
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from src.operations.base_request import BaseRequest
from src.operations.result.result import OperationResult


class DependencyType(Enum):
    """依存関係の種類"""
    FILE_CREATION = "file_creation"      # ファイル作成依存
    DIRECTORY_CREATION = "dir_creation"  # ディレクトリ作成依存
    RESOURCE_ACCESS = "resource_access"  # リソースアクセス依存
    EXECUTION_ORDER = "exec_order"       # 実行順序依存


@dataclass
class RequestNode:
    """リクエストノード（グラフの頂点）"""
    id: str
    request: BaseRequest
    
    # 実行情報
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[OperationResult] = None
    
    # リソース情報
    creates_files: Set[str] = field(default_factory=set)
    creates_dirs: Set[str] = field(default_factory=set)
    reads_files: Set[str] = field(default_factory=set)
    requires_dirs: Set[str] = field(default_factory=set)
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, RequestNode):
            return False
        return self.id == other.id


@dataclass
class DependencyEdge:
    """依存関係エッジ（グラフの辺）"""
    from_node: str
    to_node: str
    dependency_type: DependencyType
    resource_path: Optional[str] = None
    description: str = ""


class RequestExecutionGraph:
    """リクエスト実行グラフ"""
    
    def __init__(self):
        # 隣接リストでグラフを表現
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.nodes: Dict[str, RequestNode] = {}
        self.edges: List[DependencyEdge] = []
    
    def add_request_node(self, node: RequestNode) -> None:
        """リクエストノードを追加"""
        self.nodes[node.id] = node
        # 隣接リストにノードを追加（エッジはまだない）
        if node.id not in self.adjacency_list:
            self.adjacency_list[node.id] = set()
        if node.id not in self.reverse_adjacency_list:
            self.reverse_adjacency_list[node.id] = set()
    
    def add_dependency(self, edge: DependencyEdge) -> None:
        """依存関係を追加"""
        self.edges.append(edge)
        # 隣接リストを更新
        self.adjacency_list[edge.from_node].add(edge.to_node)
        self.reverse_adjacency_list[edge.to_node].add(edge.from_node)
    
    def remove_dependency(self, from_node: str, to_node: str) -> None:
        """依存関係を削除"""
        if to_node in self.adjacency_list.get(from_node, set()):
            self.adjacency_list[from_node].remove(to_node)
            self.reverse_adjacency_list[to_node].remove(from_node)
            self.edges = [e for e in self.edges 
                         if not (e.from_node == from_node and e.to_node == to_node)]
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """指定ノードが依存するノードのリストを取得"""
        return list(self.reverse_adjacency_list.get(node_id, set()))
    
    def get_dependents(self, node_id: str) -> List[str]:
        """指定ノードに依存するノードのリストを取得"""
        return list(self.adjacency_list.get(node_id, set()))
    
    def detect_cycles(self) -> List[List[str]]:
        """循環依存を検出（DFSベース）"""
        # 訪問状態: 0=未訪問、1=訪問中、2=訪問済み
        visit_state = {node: 0 for node in self.nodes}
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            """DFSで循環を検出"""
            visit_state[node] = 1
            path.append(node)
            
            for neighbor in self.adjacency_list.get(node, set()):
                if visit_state.get(neighbor, 0) == 1:
                    # 循環を発見
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)
                elif visit_state.get(neighbor, 0) == 0:
                    dfs(neighbor, path.copy())
            
            visit_state[node] = 2
        
        # すべてのノードから開始
        for node in self.nodes:
            if visit_state[node] == 0:
                dfs(node, [])
        
        return cycles
    
    def get_execution_order(self) -> List[str]:
        """トポロジカルソートによる実行順序を取得（Kahnのアルゴリズム）"""
        cycles = self.detect_cycles()
        if cycles:
            raise ValueError(f"Circular dependency detected: {cycles}")
        
        # 入次数を計算
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for neighbor in self.adjacency_list.get(node, set()):
                in_degree[neighbor] += 1
        
        # 入次数が0のノードをキューに追加
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # 隣接ノードの入次数を減らす
            for neighbor in self.adjacency_list.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # すべてのノードが処理されたか確認
        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles or disconnected components")
        
        return result
    
    def get_parallel_groups(self) -> List[List[str]]:
        """並行実行可能なノードグループを取得"""
        execution_order = self.get_execution_order()
        groups = []
        remaining = set(execution_order)
        completed = set()
        
        while remaining:
            # 依存関係が満たされているノードを見つける
            ready_nodes = []
            for node_id in remaining:
                dependencies = set(self.get_dependencies(node_id))
                if dependencies.issubset(completed):
                    ready_nodes.append(node_id)
            
            if not ready_nodes:
                raise ValueError("Unable to find executable nodes - possible deadlock")
            
            groups.append(ready_nodes)
            completed.update(ready_nodes)
            remaining -= set(ready_nodes)
        
        return groups
    
    def execute_sequential(self, driver=None) -> List[OperationResult]:
        """順次実行"""
        execution_order = self.get_execution_order()
        results = []
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            # ステータスを更新
            node.status = "running"
            
            try:
                # リクエストを実行
                result = node.request.execute(driver=driver)
                node.result = result
                node.status = "completed" if result.success else "failed"
                results.append(result)
                
                # 失敗時の処理
                if not result.success and not getattr(node.request, 'allow_failure', False):
                    # 依存するノードをスキップ
                    self._mark_dependent_nodes_skipped(node_id)
                    break
                    
            except Exception as e:
                node.status = "failed"
                # エラー結果を作成
                error_result = OperationResult(success=False, error_message=str(e))
                node.result = error_result
                results.append(error_result)
                
                if not getattr(node.request, 'allow_failure', False):
                    self._mark_dependent_nodes_skipped(node_id)
                    break
        
        return results
    
    def execute_parallel(self, driver=None, max_workers: int = 4) -> List[OperationResult]:
        """並行実行"""
        parallel_groups = self.get_parallel_groups()
        all_results = {}
        failed_nodes = set()
        
        for group in parallel_groups:
            # 失敗したノードに依存するノードをスキップ
            executable_nodes = []
            for node_id in group:
                dependencies = set(self.get_dependencies(node_id))
                if not dependencies.intersection(failed_nodes):
                    executable_nodes.append(node_id)
                else:
                    self.nodes[node_id].status = "skipped"
            
            if not executable_nodes:
                continue
            
            if len(executable_nodes) == 1:
                # 単一ノードは直接実行
                node_id = executable_nodes[0]
                node = self.nodes[node_id]
                node.status = "running"
                
                try:
                    result = node.request.execute(driver=driver)
                    node.result = result
                    node.status = "completed" if result.success else "failed"
                    all_results[node_id] = result
                    
                    if not result.success and not getattr(node.request, 'allow_failure', False):
                        failed_nodes.add(node_id)
                        
                except Exception as e:
                    node.status = "failed"
                    error_result = OperationResult(success=False, error_message=str(e))
                    node.result = error_result
                    all_results[node_id] = error_result
                    
                    if not getattr(node.request, 'allow_failure', False):
                        failed_nodes.add(node_id)
            else:
                # 複数ノードは並行実行
                with ThreadPoolExecutor(max_workers=min(max_workers, len(executable_nodes))) as executor:
                    futures = {}
                    
                    for node_id in executable_nodes:
                        node = self.nodes[node_id]
                        node.status = "running"
                        future = executor.submit(node.request.execute, driver=driver)
                        futures[future] = node_id
                    
                    for future in as_completed(futures):
                        node_id = futures[future]
                        node = self.nodes[node_id]
                        
                        try:
                            result = future.result()
                            node.result = result
                            node.status = "completed" if result.success else "failed"
                            all_results[node_id] = result
                            
                            if not result.success and not getattr(node.request, 'allow_failure', False):
                                failed_nodes.add(node_id)
                                
                        except Exception as e:
                            node.status = "failed"
                            error_result = OperationResult(success=False, error_message=str(e))
                            node.result = error_result
                            all_results[node_id] = error_result
                            
                            if not getattr(node.request, 'allow_failure', False):
                                failed_nodes.add(node_id)
        
        # 実行順序に従って結果を並べ替え
        execution_order = self.get_execution_order()
        results = []
        for node_id in execution_order:
            if node_id in all_results:
                results.append(all_results[node_id])
            elif self.nodes[node_id].status == "skipped":
                # スキップされたノードの結果
                results.append(OperationResult(success=False, error_message="Skipped due to dependency failure"))
        
        return results
    
    def _mark_dependent_nodes_skipped(self, failed_node_id: str) -> None:
        """失敗したノードに依存するすべてのノードをスキップ状態にマーク"""
        dependents = self.get_dependents(failed_node_id)
        for dependent_id in dependents:
            if self.nodes[dependent_id].status == "pending":
                self.nodes[dependent_id].status = "skipped"
                # 再帰的に依存するノードもスキップ
                self._mark_dependent_nodes_skipped(dependent_id)
    
    def visualize(self) -> str:
        """グラフの可視化用文字列を生成"""
        lines = ["Request Execution Graph:"]
        lines.append(f"Nodes: {len(self.nodes)}")
        lines.append(f"Edges: {len(self.edges)}")
        
        # ノード情報
        lines.append("\nNodes:")
        for node_id, node in self.nodes.items():
            lines.append(f"  {node_id}: {node.request.__class__.__name__} (status: {node.status})")
        
        # エッジ情報
        lines.append("\nDependencies:")
        for edge in self.edges:
            lines.append(f"  {edge.from_node} -> {edge.to_node} ({edge.dependency_type.value})")
        
        # 実行グループ
        try:
            groups = self.get_parallel_groups()
            lines.append("\nParallel Execution Groups:")
            for i, group in enumerate(groups):
                lines.append(f"  Group {i+1}: {', '.join(group)}")
        except ValueError as e:
            lines.append(f"\nError: {str(e)}")
        
        return '\n'.join(lines)