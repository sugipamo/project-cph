"""
リクエスト実行グラフ

依存関係を持つリクエストのグラフ構造と実行戦略を提供
"""
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import re
import os
import traceback
from src.domain.requests.base.base_request import BaseRequest
from src.domain.results.result import OperationResult
from src.utils.debug_logger import DebugLogger


class DependencyType(Enum):
    """依存関係の種類"""
    FILE_CREATION = "file_creation"      # ファイル作成依存
    DIRECTORY_CREATION = "dir_creation"  # ディレクトリ作成依存
    RESOURCE_ACCESS = "resource_access"  # リソースアクセス依存
    EXECUTION_ORDER = "exec_order"       # 実行順序依存


class RequestNode:
    """リクエストノード（グラフの頂点）
    
    メモリ効率を考慮して、必要最小限の情報のみ保持
    """
    __slots__ = ('id', 'request', 'status', 'result', '_resource_info', 'metadata')
    
    def __init__(self, id: str, request: BaseRequest,
                 creates_files: Optional[Set[str]] = None,
                 creates_dirs: Optional[Set[str]] = None,
                 reads_files: Optional[Set[str]] = None,
                 requires_dirs: Optional[Set[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.request = request
        self.status = "pending"
        self.result = None
        
        # リソース情報をコンパクトに保存
        self._resource_info = None
        if creates_files or creates_dirs or reads_files or requires_dirs:
            self._resource_info = {
                'creates_files': creates_files or set(),
                'creates_dirs': creates_dirs or set(),
                'reads_files': reads_files or set(),
                'requires_dirs': requires_dirs or set()
            }
        
        self.metadata = metadata or {}
    
    @property
    def creates_files(self) -> Set[str]:
        return self._resource_info.get('creates_files', set()) if self._resource_info else set()
    
    @property
    def creates_dirs(self) -> Set[str]:
        return self._resource_info.get('creates_dirs', set()) if self._resource_info else set()
    
    @property
    def reads_files(self) -> Set[str]:
        return self._resource_info.get('reads_files', set()) if self._resource_info else set()
    
    @property
    def requires_dirs(self) -> Set[str]:
        return self._resource_info.get('requires_dirs', set()) if self._resource_info else set()
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, RequestNode):
            return False
        return self.id == other.id


class DependencyEdge:
    """依存関係エッジ（グラフの辺）"""
    __slots__ = ('from_node', 'to_node', 'dependency_type', 'resource_path', 'description')
    
    def __init__(self, from_node: str, to_node: str, dependency_type: DependencyType,
                 resource_path: Optional[str] = None, description: str = ""):
        self.from_node = from_node
        self.to_node = to_node
        self.dependency_type = dependency_type
        self.resource_path = resource_path
        self.description = description


class RequestExecutionGraph:
    """リクエスト実行グラフ"""
    
    def __init__(self, debug_config: Optional[Dict[str, Any]] = None):
        # 隣接リストでグラフを表現
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.nodes: Dict[str, RequestNode] = {}
        self.edges: List[DependencyEdge] = []
        # 実行結果の蓄積用（結果置換機能用）
        self.execution_results: Dict[str, OperationResult] = {}
        # デバッグロガー
        self.debug_logger = DebugLogger(debug_config)
    
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
    
    def analyze_cycles(self) -> Dict[str, Any]:
        """
        循環依存を解析して詳細な情報を取得
        
        Returns:
            Dict[str, Any]: 循環の詳細情報
        """
        cycles = self.detect_cycles()
        if not cycles:
            return {'has_cycles': False, 'cycles': []}
        
        cycle_analysis = []
        for cycle in cycles:
            # 循環の詳細情報を収集
            cycle_info = {
                'nodes': cycle,
                'length': len(cycle),
                'dependencies': []
            }
            
            # 循環内の依存関係を調査
            for i, from_node in enumerate(cycle):
                to_node = cycle[(i + 1) % len(cycle)]
                
                # このエッジを探す
                edge_info = None
                for edge in self.edges:
                    if edge.from_node == from_node and edge.to_node == to_node:
                        edge_info = {
                            'from': from_node,
                            'to': to_node,
                            'type': edge.dependency_type.value,
                            'resource': edge.resource_path,
                            'description': edge.description
                        }
                        break
                
                if edge_info:
                    cycle_info['dependencies'].append(edge_info)
            
            cycle_analysis.append(cycle_info)
        
        return {
            'has_cycles': True,
            'cycle_count': len(cycles),
            'cycles': cycle_analysis
        }
    
    def format_cycle_error(self) -> str:
        """
        循環依存のエラーメッセージをフォーマット
        
        Returns:
            str: ユーザーに優しいエラーメッセージ
        """
        analysis = self.analyze_cycles()
        if not analysis['has_cycles']:
            return ""
        
        lines = [
            "Circular dependency detected in the workflow graph!",
            "",
            f"Found {analysis['cycle_count']} circular dependency chain(s):",
            ""
        ]
        
        for i, cycle in enumerate(analysis['cycles'], 1):
            lines.append(f"Cycle {i} ({cycle['length']} nodes):")
            
            # ノードの循環を表示
            node_names = []
            for node_id in cycle['nodes']:
                node = self.nodes.get(node_id)
                if node and hasattr(node.request, '__class__'):
                    node_names.append(f"{node_id} ({node.request.__class__.__name__})") 
                else:
                    node_names.append(node_id)
            
            cycle_chain = " -> ".join(node_names) + f" -> {node_names[0]}"
            lines.append(f"  {cycle_chain}")
            lines.append("")
            
            # 依存関係の詳細
            if cycle['dependencies']:
                lines.append("  Dependencies in this cycle:")
                for dep in cycle['dependencies']:
                    dep_desc = f"    {dep['from']} -> {dep['to']} ({dep['type']})"
                    if dep['resource']:
                        dep_desc += f" [resource: {dep['resource']}]"
                    if dep['description']:
                        dep_desc += f" - {dep['description']}"
                    lines.append(dep_desc)
                lines.append("")
        
        lines.extend([
            "Resolution suggestions:",
            "1. Remove or modify one of the dependencies in each cycle",
            "2. Check if the dependencies are actually necessary",
            "3. Consider using conditional execution or different resources",
            "4. Review the workflow logic for potential design issues"
        ])
        
        return "\n".join(lines)
    
    def get_execution_order(self) -> List[str]:
        """トポロジカルソートによる実行順序を取得（Kahnのアルゴリズム）"""
        cycles = self.detect_cycles()
        if cycles:
            cycle_error = self.format_cycle_error()
            raise ValueError(cycle_error)
        
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
        
        # ワークフロー開始ログ
        self.debug_logger.log_workflow_start(len(execution_order), parallel=False)
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            # 結果置換を適用
            self.apply_result_substitution_to_request(node.request, node_id)
            
            # リクエスト実行前のデバッグ出力
            self._debug_request_before_execution(node, node_id)
            
            # ステータスを更新
            node.status = "running"
            
            try:
                # リクエストを実行
                result = node.request.execute(driver=driver)
                node.result = result
                node.status = "completed" if result.success else "failed"
                results.append(result)
                
                # 実行結果を蓄積
                self.execution_results[node_id] = result
                
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
                
                # エラー結果も蓄積
                self.execution_results[node_id] = error_result
                
                if not getattr(node.request, 'allow_failure', False):
                    self._mark_dependent_nodes_skipped(node_id)
                    break
        
        return results
    
    def execute_parallel(self, driver=None, max_workers: int = 4, 
                        executor_class: type = ThreadPoolExecutor) -> List[OperationResult]:
        """
        並行実行（最適化版）
        
        Args:
            driver: 実行に使用するドライバー
            max_workers: 最大ワーカー数（CPUコア数に基づいて自動調整）
            executor_class: 使用するExecutorクラス（テスト用）
        
        Returns:
            List[OperationResult]: 実行結果のリスト
        """
        
        # CPUコア数に基づいてmax_workersを調整
        cpu_count = os.cpu_count() or 1
        optimal_workers = min(max_workers, cpu_count * 2)  # CPUコア数の2倍まで
        
        parallel_groups = self.get_parallel_groups()
        all_results = {}
        failed_nodes = set()
        
        # グローバルスレッドプールを使用
        with executor_class(max_workers=optimal_workers) as executor:
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
                
                # バッチ処理で効率化
                futures_batch = self._submit_batch(executor, executable_nodes, driver)
                
                # 結果を収集
                for future, node_id in futures_batch:
                    node = self.nodes[node_id]
                    
                    try:
                        result = future.result(timeout=300)  # 5分のタイムアウト
                        node.result = result
                        node.status = "completed" if result.success else "failed"
                        all_results[node_id] = result
                        
                        # 実行結果を蓄積
                        self.execution_results[node_id] = result
                        
                        if not result.success and not getattr(node.request, 'allow_failure', False):
                            failed_nodes.add(node_id)
                            
                    except Exception as e:
                        node.status = "failed"
                        error_result = OperationResult(success=False, error_message=str(e))
                        node.result = error_result
                        all_results[node_id] = error_result
                        
                        # エラー結果も蓄積
                        self.execution_results[node_id] = error_result
                        
                        if not getattr(node.request, 'allow_failure', False):
                            failed_nodes.add(node_id)
        
        # 結果を実行順序に従って並べ替え
        return self._collect_results(all_results)
    
    def _submit_batch(self, executor, node_ids: List[str], driver) -> List[Tuple]:
        """
        ノードをバッチでスレッドプールに送信
        
        Args:
            executor: ThreadPoolExecutor
            node_ids: 実行するノードIDのリスト
            driver: 実行ドライバー
        
        Returns:
            List[Tuple[Future, str]]: (Future, node_id)のリスト
        """
        futures = []
        
        for node_id in node_ids:
            node = self.nodes[node_id]
            
            # 結果置換を適用
            self.apply_result_substitution_to_request(node.request, node_id)
            
            # リクエスト実行前のデバッグ出力
            self._debug_request_before_execution(node, node_id)
            
            node.status = "running"
            
            # タスクを送信
            future = executor.submit(self._execute_node_safe, node, driver)
            futures.append((future, node_id))
        
        return futures
    
    def _execute_node_safe(self, node: RequestNode, driver) -> OperationResult:
        """
        ノードを安全に実行（例外ハンドリング付き）
        
        Args:
            node: 実行するノード
            driver: 実行ドライバー
        
        Returns:
            OperationResult: 実行結果
        """
        try:
            return node.request.execute(driver=driver)
        except Exception as e:
            # 例外をキャッチしてエラー結果を返す
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            return OperationResult(success=False, error_message=error_msg)
    
    def _collect_results(self, all_results: Dict[str, OperationResult]) -> List[OperationResult]:
        """
        結果を実行順序に従って収集
        
        Args:
            all_results: ノードIDと結果の辞書
        
        Returns:
            List[OperationResult]: 順序付けされた結果のリスト
        """
        execution_order = self.get_execution_order()
        results = []
        
        for node_id in execution_order:
            if node_id in all_results:
                results.append(all_results[node_id])
            elif self.nodes[node_id].status == "skipped":
                # スキップされたノードの結果
                results.append(OperationResult(
                    success=False, 
                    error_message="Skipped due to dependency failure"
                ))
        
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
    
    def _debug_request_before_execution(self, node: RequestNode, node_id: str):
        """
        リクエスト実行前のデバッグ出力
        
        Args:
            node: 実行するリクエストノード
            node_id: ノードID
        """
        if not self.debug_logger.is_enabled():
            return
            
        req = node.request
        
        # リクエストタイプを取得
        step_type = "unknown"
        if hasattr(req, 'operation_type'):
            if str(req.operation_type) == "OperationType.FILE" and hasattr(req, 'op'):
                step_type = f"FILE.{req.op.name}"
            else:
                step_type = str(req.operation_type)
        
        # デバッグ情報を収集
        debug_kwargs = {}
        
        # コマンド情報
        if hasattr(req, 'cmd') and req.cmd:
            debug_kwargs['cmd'] = req.cmd
        
        # パス情報
        if hasattr(req, 'path') and req.path:
            debug_kwargs['path'] = req.path
        if hasattr(req, 'dst_path') and req.dst_path:
            debug_kwargs['dest'] = req.dst_path
            debug_kwargs['source'] = getattr(req, 'path', '')
        
        # オプション情報
        if hasattr(req, 'allow_failure'):
            debug_kwargs['allow_failure'] = req.allow_failure
        if hasattr(req, 'show_output'):
            debug_kwargs['show_output'] = req.show_output
        
        # デバッグログ出力
        self.debug_logger.log_step_start(node_id, step_type, **debug_kwargs)
    
    def substitute_result_placeholders(self, text) -> str:
        """
        テキスト内の結果プレースホルダーを実際の値で置換
        
        形式: {{step_X.result.Y}} または {{step_X.Y}}
        例: {{step_0.result.stdout}}, {{step_test.returncode}}
        
        Args:
            text: 置換対象のテキスト（文字列でない場合はそのまま返す）
            
        Returns:
            str: 置換済みのテキスト
        """
        # 文字列でない場合はそのまま返す（テスト用のMockオブジェクト等）
        if not isinstance(text, str):
            return text
            
        # {{step_X.result.Y}}形式のパターンを検索
        pattern1 = r'\{\{step_(\w+)\.result\.(\w+)\}\}'
        # {{step_X.Y}}形式のパターンも対応
        pattern2 = r'\{\{step_(\w+)\.(\w+)\}\}'
        
        def replacer(match):
            step_id = match.group(1)
            field_name = match.group(2)
            
            if step_id in self.execution_results:
                result = self.execution_results[step_id]
                if hasattr(result, field_name):
                    value = getattr(result, field_name)
                    return str(value) if value is not None else ""
            
            # 置換できない場合は元のまま
            return match.group(0)
        
        # 両方のパターンを置換
        text = re.sub(pattern1, replacer, text)
        text = re.sub(pattern2, replacer, text)
        
        return text
    
    def apply_result_substitution_to_request(self, request, node_id: str) -> None:
        """
        リクエストのコマンドに結果置換を適用
        
        Args:
            request: 置換対象のリクエスト
            node_id: リクエストのノードID
        """
        # ShellRequestのcmdを置換
        if hasattr(request, 'cmd') and request.cmd:
            if isinstance(request.cmd, list):
                # リスト内の各要素が文字列の場合のみ置換
                new_cmd = []
                for cmd in request.cmd:
                    new_cmd.append(self.substitute_result_placeholders(cmd))
                request.cmd = new_cmd
            else:
                request.cmd = self.substitute_result_placeholders(request.cmd)
        
        # DockerRequestのcommandを置換
        if hasattr(request, 'command') and request.command:
            request.command = self.substitute_result_placeholders(request.command)
        
        # その他のテキストフィールドも置換
        if hasattr(request, 'path') and request.path:
            request.path = self.substitute_result_placeholders(request.path)
        if hasattr(request, 'dst_path') and request.dst_path:
            request.dst_path = self.substitute_result_placeholders(request.dst_path)