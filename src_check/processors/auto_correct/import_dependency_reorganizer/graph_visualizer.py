"""
依存関係グラフ可視化
グラフ構造を様々な形式で出力
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import textwrap

class DependencyGraphVisualizer:
    """依存関係グラフの可視化クラス"""
    
    def __init__(self, analyzer, calculator):
        """
        Args:
            analyzer: SimpleImportAnalyzer インスタンス
            calculator: DependencyCalculator インスタンス
        """
        self.analyzer = analyzer
        self.calculator = calculator
        
    def generate_dot(self, output_path: Path, 
                    depth_map: Optional[Dict[Path, int]] = None,
                    include_external: bool = False) -> None:
        """
        Graphviz DOT形式でグラフを生成
        
        Args:
            output_path: 出力ファイルパス
            depth_map: ファイルの深度マップ（色分け用）
            include_external: 外部モジュールを含めるか
        """
        lines = ['digraph DependencyGraph {']
        lines.append('  rankdir=TB;')
        lines.append('  node [shape=box, style=rounded];')
        lines.append('  ')
        
        # 深度ごとの色定義
        depth_colors = {
            0: '#e8f5e9',  # 薄緑
            1: '#c8e6c9',  # 緑
            2: '#a5d6a7',  # 中緑
            3: '#81c784',  # 濃緑
            4: '#66bb6a',  # より濃い緑
            5: '#4caf50'   # 最も濃い緑
        }
        
        # ノードの定義
        processed_modules = set()
        for file_path, imports in self.analyzer.file_imports.items():
            module_name = self.analyzer.path_to_module_name(file_path)
            
            if module_name and module_name not in processed_modules:
                processed_modules.add(module_name)
                
                # ノードの属性を設定
                label = self._format_module_name(module_name)
                color = '#ffffff'
                
                if depth_map and file_path in depth_map:
                    depth = depth_map[file_path]
                    color = depth_colors.get(depth, '#ffffff')
                    label += f'\\n(深度: {depth})'
                
                lines.append(f'  "{module_name}" [label="{label}", fillcolor="{color}", style=filled];')
        
        lines.append('  ')
        
        # エッジの定義
        for source_module, target_modules in self.calculator.dependency_graph.items():
            for target_module in target_modules:
                # 外部モジュールのフィルタリング
                if not include_external:
                    if not self._is_internal_module(target_module):
                        continue
                
                lines.append(f'  "{source_module}" -> "{target_module}";')
        
        # 循環依存の強調
        circular_deps = self.calculator.detect_circular_dependencies()
        if circular_deps:
            lines.append('  ')
            lines.append('  // 循環依存')
            lines.append('  edge [color=red, style=bold];')
            
            for cycle in circular_deps:
                for i in range(len(cycle) - 1):
                    lines.append(f'  "{cycle[i]}" -> "{cycle[i+1]}" [color=red];')
        
        lines.append('}')
        
        # ファイルに書き込み
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(lines))
        
    def generate_mermaid(self, output_path: Path,
                        depth_map: Optional[Dict[Path, int]] = None,
                        max_nodes: int = 50) -> None:
        """
        Mermaid形式でグラフを生成（Markdown埋め込み用）
        
        Args:
            output_path: 出力ファイルパス
            depth_map: ファイルの深度マップ
            max_nodes: 最大ノード数（大きすぎるグラフを防ぐ）
        """
        lines = ['```mermaid', 'graph TD']
        
        # ノード数を制限
        all_modules = set(self.calculator.dependency_graph.keys())
        all_modules.update(*self.calculator.dependency_graph.values())
        
        if len(all_modules) > max_nodes:
            # 最も依存関係の多いモジュールを優先
            module_importance = {}
            for module in all_modules:
                importance = len(self.calculator.dependency_graph.get(module, []))
                importance += len(self.calculator.reverse_graph.get(module, []))
                module_importance[module] = importance
            
            # 重要度でソートして上位を選択
            important_modules = sorted(
                module_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_nodes]
            selected_modules = {m[0] for m in important_modules}
        else:
            selected_modules = all_modules
        
        # ノード定義
        node_id_map = {}
        for i, module in enumerate(selected_modules):
            node_id = f'N{i}'
            node_id_map[module] = node_id
            
            label = self._format_module_name(module)
            
            # 深度情報を追加
            if depth_map:
                for file_path, depth in depth_map.items():
                    if self.analyzer.path_to_module_name(file_path) == module:
                        label += f'<br/>深度: {depth}'
                        break
            
            # スタイルクラスを設定
            style_class = self._get_mermaid_style_class(module, depth_map)
            lines.append(f'    {node_id}["{label}"]:::{style_class}')
        
        lines.append('    ')
        
        # エッジ定義
        for source_module, target_modules in self.calculator.dependency_graph.items():
            if source_module not in selected_modules:
                continue
                
            source_id = node_id_map[source_module]
            
            for target_module in target_modules:
                if target_module not in selected_modules:
                    continue
                    
                target_id = node_id_map[target_module]
                lines.append(f'    {source_id} --> {target_id}')
        
        # スタイル定義
        lines.extend([
            '    ',
            '    classDef depth0 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;',
            '    classDef depth1 fill:#c8e6c9,stroke:#4caf50,stroke-width:2px;',
            '    classDef depth2 fill:#a5d6a7,stroke:#4caf50,stroke-width:2px;',
            '    classDef depth3 fill:#81c784,stroke:#4caf50,stroke-width:2px;',
            '    classDef depth4 fill:#66bb6a,stroke:#4caf50,stroke-width:2px;',
            '    classDef circular fill:#ffcdd2,stroke:#f44336,stroke-width:3px;'
        ])
        
        lines.append('```')
        
        # ファイルに書き込み
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(lines))
    
    def generate_json_graph(self, output_path: Path,
                           depth_map: Optional[Dict[Path, int]] = None) -> None:
        """
        JSON形式でグラフデータを出力（D3.js等での利用用）
        
        Args:
            output_path: 出力ファイルパス
            depth_map: ファイルの深度マップ
        """
        # ノードとエッジのデータを構築
        nodes = []
        edges = []
        node_index_map = {}
        
        # すべてのモジュールを収集
        all_modules = set(self.calculator.dependency_graph.keys())
        all_modules.update(*self.calculator.dependency_graph.values())
        
        # ノードデータを作成
        for i, module in enumerate(sorted(all_modules)):
            node_index_map[module] = i
            
            node_data = {
                'id': i,
                'name': module,
                'label': self._format_module_name(module),
                'dependencies': len(self.calculator.dependency_graph.get(module, [])),
                'dependents': len(self.calculator.reverse_graph.get(module, []))
            }
            
            # 深度情報を追加
            if depth_map:
                for file_path, depth in depth_map.items():
                    if self.analyzer.path_to_module_name(file_path) == module:
                        node_data['depth'] = depth
                        break
            
            # ファイルパスを追加
            for file_path in self.analyzer.file_imports:
                if self.analyzer.path_to_module_name(file_path) == module:
                    node_data['file_path'] = str(file_path)
                    break
            
            nodes.append(node_data)
        
        # エッジデータを作成
        for source_module, target_modules in self.calculator.dependency_graph.items():
            source_idx = node_index_map.get(source_module)
            if source_idx is None:
                continue
                
            for target_module in target_modules:
                target_idx = node_index_map.get(target_module)
                if target_idx is None:
                    continue
                    
                edges.append({
                    'source': source_idx,
                    'target': target_idx,
                    'source_name': source_module,
                    'target_name': target_module
                })
        
        # 循環依存情報を追加
        circular_deps = self.calculator.detect_circular_dependencies()
        
        # グラフデータをまとめる
        graph_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'circular_dependencies': len(circular_deps),
                'max_depth': max((n.get('depth', 0) for n in nodes), default=0)
            },
            'nodes': nodes,
            'edges': edges,
            'circular_dependencies': circular_deps
        }
        
        # ファイルに書き込み
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    def generate_ascii_tree(self, output_path: Path,
                           root_modules: Optional[List[str]] = None,
                           max_depth: int = 5) -> None:
        """
        ASCIIアートでツリー構造を生成
        
        Args:
            output_path: 出力ファイルパス
            root_modules: ルートとするモジュール（Noneの場合は深度0のモジュール）
            max_depth: 表示する最大深度
        """
        lines = ['依存関係ツリー', '=' * 50, '']
        
        # ルートモジュールを決定
        if root_modules is None:
            # 深度0のモジュールまたは依存されていないモジュールを探す
            root_modules = []
            for module in self.calculator.dependency_graph:
                if module not in self.calculator.reverse_graph or \
                   len(self.calculator.reverse_graph[module]) == 0:
                    root_modules.append(module)
        
        # 各ルートからツリーを生成
        for root in sorted(root_modules):
            if self._is_internal_module(root):
                lines.extend(self._build_ascii_tree(root, max_depth))
                lines.append('')
        
        # 統計情報を追加
        lines.extend([
            '',
            '統計情報',
            '-' * 50,
            f'総モジュール数: {len(self.calculator.dependency_graph)}',
            f'総依存関係数: {sum(len(deps) for deps in self.calculator.dependency_graph.values())}',
            f'循環依存数: {len(self.calculator.detect_circular_dependencies())}'
        ])
        
        # ファイルに書き込み
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(lines))
    
    def _build_ascii_tree(self, module: str, max_depth: int,
                         current_depth: int = 0,
                         visited: Optional[Set[str]] = None,
                         prefix: str = '') -> List[str]:
        """ASCIIツリーを再帰的に構築"""
        if visited is None:
            visited = set()
        
        if module in visited or current_depth > max_depth:
            return []
        
        visited.add(module)
        lines = []
        
        # 現在のノードを追加
        display_name = self._format_module_name(module)
        deps = self.calculator.dependency_graph.get(module, [])
        dep_count = len(deps)
        
        if current_depth == 0:
            lines.append(f'📦 {display_name} ({dep_count} deps)')
        else:
            lines.append(f'{prefix}├── {display_name} ({dep_count} deps)')
        
        # 依存関係を追加
        internal_deps = [d for d in deps if self._is_internal_module(d)]
        
        for i, dep in enumerate(sorted(internal_deps)):
            is_last = i == len(internal_deps) - 1
            
            if current_depth == 0:
                new_prefix = '    '
            else:
                new_prefix = prefix + ('    ' if is_last else '│   ')
            
            sub_lines = self._build_ascii_tree(
                dep, max_depth, current_depth + 1, visited, new_prefix
            )
            lines.extend(sub_lines)
        
        return lines
    
    def _format_module_name(self, module_name: str) -> str:
        """モジュール名を表示用にフォーマット"""
        parts = module_name.split('.')
        if len(parts) > 3:
            # 長すぎる場合は省略
            return f"{parts[0]}.../...{parts[-1]}"
        return module_name
    
    def _is_internal_module(self, module_name: str) -> bool:
        """内部モジュールかどうかを判定"""
        # プロジェクト内のモジュールかチェック
        for file_path in self.analyzer.file_imports:
            if self.analyzer.path_to_module_name(file_path) == module_name:
                return True
        return False
    
    def _get_mermaid_style_class(self, module: str,
                                depth_map: Optional[Dict[Path, int]]) -> str:
        """Mermaidのスタイルクラスを決定"""
        # 循環依存チェック
        circular_deps = self.calculator.detect_circular_dependencies()
        for cycle in circular_deps:
            if module in cycle:
                return 'circular'
        
        # 深度によるスタイル
        if depth_map:
            for file_path, depth in depth_map.items():
                if self.analyzer.path_to_module_name(file_path) == module:
                    return f'depth{min(depth, 4)}'
        
        return 'depth0'
    
    def generate_summary_report(self, output_path: Path) -> None:
        """依存関係の要約レポートを生成"""
        lines = [
            '# 依存関係分析レポート',
            f'生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '',
            '## 概要',
            ''
        ]
        
        stats = self.calculator.get_statistics()
        lines.extend([
            f'- 総モジュール数: {stats["total_modules"]}',
            f'- 総依存関係数: {stats["total_dependencies"]}',
            f'- 平均依存数: {stats["avg_dependencies_per_module"]:.1f}',
            ''
        ])
        
        # 最も依存関係の多いモジュール
        if stats['max_dependencies']['module']:
            lines.extend([
                '## 最も多くの依存を持つモジュール',
                f'- {stats["max_dependencies"]["module"]} ({stats["max_dependencies"]["count"]}個の依存)',
                ''
            ])
        
        # 最も依存されているモジュール
        if stats['most_depended_upon']['module']:
            lines.extend([
                '## 最も多く依存されているモジュール',
                f'- {stats["most_depended_upon"]["module"]} ({stats["most_depended_upon"]["count"]}個のモジュールから依存)',
                ''
            ])
        
        # 循環依存
        circular_deps = self.calculator.detect_circular_dependencies()
        if circular_deps:
            lines.extend([
                '## 循環依存',
                f'検出された循環依存: {len(circular_deps)}個',
                ''
            ])
            
            for i, cycle in enumerate(circular_deps[:5], 1):
                lines.append(f'{i}. {" → ".join(cycle)}')
            
            if len(circular_deps) > 5:
                lines.append(f'... 他 {len(circular_deps) - 5}個')
        
        # ファイルに書き込み
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(lines))