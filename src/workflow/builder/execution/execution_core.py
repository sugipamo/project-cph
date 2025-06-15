"""実行グラフのコア機能 - request_execution_graph.pyから分離"""
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from src.domain.requests.base.base_request import OperationRequestFoundation
from src.domain.results.result import OperationResult

from ..debug.debug_logger_adapter import create_workflow_debug_adapter


@dataclass(frozen=True)
class NodeExecutionResult:
    """ノード実行結果（不変データ構造）"""
    result: OperationResult
    should_stop: bool


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
    __slots__ = ('_resource_info', 'id', 'metadata', 'request', 'result', 'status')

    def __init__(self, id: str, request: OperationRequestFoundation,
                 creates_files: Optional[set[str]] = None,
                 creates_dirs: Optional[set[str]] = None,
                 reads_files: Optional[set[str]] = None,
                 requires_dirs: Optional[set[str]] = None,
                 metadata: Optional[dict[str, Any]] = None):
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
    def creates_files(self) -> set[str]:
        return self._resource_info.get('creates_files', set()) if self._resource_info else set()

    @property
    def creates_dirs(self) -> set[str]:
        return self._resource_info.get('creates_dirs', set()) if self._resource_info else set()

    @property
    def reads_files(self) -> set[str]:
        return self._resource_info.get('reads_files', set()) if self._resource_info else set()

    @property
    def requires_dirs(self) -> set[str]:
        return self._resource_info.get('requires_dirs', set()) if self._resource_info else set()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, RequestNode):
            return False
        return self.id == other.id


class DependencyEdge:
    """依存関係エッジ（グラフの辺）"""
    __slots__ = ('dependency_type', 'description', 'from_node', 'resource_path', 'to_node')

    def __init__(self, from_node: str, to_node: str, dependency_type: DependencyType,
                 resource_path: Optional[str] = None, description: str = ""):
        self.from_node = from_node
        self.to_node = to_node
        self.dependency_type = dependency_type
        self.resource_path = resource_path
        self.description = description


class RequestExecutionGraph:
    """リクエスト実行グラフ"""

    def __init__(self, debug_config: Optional[dict[str, Any]] = None):
        # 隣接リストでグラフを表現
        self.adjacency_list: dict[str, set[str]] = defaultdict(set)
        self.reverse_adjacency_list: dict[str, set[str]] = defaultdict(set)
        self.nodes: dict[str, RequestNode] = {}
        self.edges: list[DependencyEdge] = []
        # 実行結果の蓄積用（結果置換機能用）
        self.execution_results: dict[str, OperationResult] = {}
        # デバッグロガー（新しいアダプターを使用）
        self.debug_logger = create_workflow_debug_adapter(debug_config)

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

    def get_dependencies(self, node_id: str) -> list[str]:
        """指定ノードが依存するノードのリストを取得"""
        from ..graph_query import extract_node_dependencies
        return extract_node_dependencies(self.reverse_adjacency_list, node_id)

    def get_dependents(self, node_id: str) -> list[str]:
        """指定ノードに依存するノードのリストを取得"""
        from ..graph_query import extract_node_dependents
        return extract_node_dependents(self.adjacency_list, node_id)

    def detect_cycles(self) -> list[list[str]]:
        """循環依存を検出（DFSベース）"""
        # 訪問状態: 0=未訪問、1=訪問中、2=訪問済み
        visit_state = dict.fromkeys(self.nodes, 0)
        cycles = []

        def dfs(node: str, path: list[str]) -> None:
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

    def analyze_cycles(self) -> dict[str, Any]:
        """循環依存を解析して詳細な情報を取得

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
        """循環依存のエラーメッセージをフォーマット

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

    def get_execution_order(self) -> list[str]:
        """トポロジカルソートによる実行順序を取得（Kahnのアルゴリズム）"""
        cycles = self.detect_cycles()
        if cycles:
            cycle_error = self.format_cycle_error()
            raise ValueError(cycle_error)

        from ..graph_query import calculate_execution_order
        return calculate_execution_order(self.nodes, self.adjacency_list)

    def get_parallel_groups(self) -> list[list[str]]:
        """並行実行可能なノードグループを取得"""
        from ..graph_query import calculate_parallel_groups
        return calculate_parallel_groups(self.nodes, self.adjacency_list, self.reverse_adjacency_list)

    def visualize(self) -> str:
        """グラフの可視化用文字列を生成"""
        from ..graph_visualization import create_graph_visualization

        try:
            execution_groups = self.get_parallel_groups()
        except ValueError:
            execution_groups = None

        return create_graph_visualization(self.nodes, self.edges, execution_groups)

    def substitute_result_placeholders(self, text) -> str:
        """テキスト内の結果プレースホルダーを実際の値で置換

        形式: {{step_X.result.Y}} または {{step_X.Y}}
        例: {{step_0.result.stdout}}, {{step_test.returncode}}

        Args:
            text: 置換対象のテキスト（文字列でない場合はそのまま返す）

        Returns:
            str: 置換済みのテキスト
        """
        from ..result_substitution import substitute_placeholders
        return substitute_placeholders(text, self.execution_results)

    def apply_result_substitution_to_request(self, request, node_id: str) -> None:
        """リクエストのコマンドに結果置換を適用

        Args:
            request: 置換対象のリクエスト
            node_id: リクエストのノードID
        """
        from ..result_substitution import apply_substitution_to_request
        apply_substitution_to_request(request, self.execution_results, node_id)

    def _mark_dependent_nodes_skipped(self, failed_node_id: str) -> None:
        """失敗したノードに依存するすべてのノードをスキップ状態にマーク"""
        dependents = self.get_dependents(failed_node_id)
        for dependent_id in dependents:
            if self.nodes[dependent_id].status == "pending":
                self.nodes[dependent_id].status = "skipped"
                # 再帰的に依存するノードもスキップ
                self._mark_dependent_nodes_skipped(dependent_id)
