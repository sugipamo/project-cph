#!/usr/bin/env python3
"""クリーンアーキテクチャチェックスクリプト

クリーンアーキテクチャの原則に従い、以下をチェックします：
1. レイヤー間の依存方向の違反
2. ドメイン層の外部依存
3. インターフェース分離の原則
4. 依存関係逆転の原則
"""
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ArchitectureLayer(Enum):
    """アーキテクチャレイヤー"""
    DOMAIN = "domain"
    APPLICATION = "application" 
    INFRASTRUCTURE = "infrastructure"
    INTERFACE = "interface"


@dataclass
class Violation:
    """アーキテクチャ違反"""
    file_path: str
    line_number: int
    violation_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'


class CleanArchitectureChecker:
    """クリーンアーキテクチャチェッカー"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: List[Violation] = []
        
        # レイヤーマッピング
        self.layer_mapping = {
            'operations': ArchitectureLayer.DOMAIN,
            'infrastructure': ArchitectureLayer.INFRASTRUCTURE,
            'context': ArchitectureLayer.APPLICATION,
            'workflow': ArchitectureLayer.APPLICATION
        }
        
        # 許可される依存関係（依存する側 -> 依存される側）
        self.allowed_dependencies = {
            ArchitectureLayer.APPLICATION: [ArchitectureLayer.DOMAIN, ArchitectureLayer.INFRASTRUCTURE],
            ArchitectureLayer.INFRASTRUCTURE: [ArchitectureLayer.DOMAIN],
            ArchitectureLayer.DOMAIN: [],  # ドメイン層は外部依存を持たない
        }
        
        # 外部ライブラリの例外（ドメイン層でも使用可能）
        self.allowed_external_deps = {
            'typing', 'dataclasses', 'enum', 'abc', 'datetime', 'pathlib',
            'collections', 'functools', 'itertools', 'operator'
        }
    
    def check_all(self) -> Dict[str, List[Violation]]:
        """全てのクリーンアーキテクチャチェックを実行"""
        self.violations = []
        
        # 1. レイヤー間依存関係チェック
        self._check_layer_dependencies()
        
        # 2. ドメイン層の純粋性チェック
        self._check_domain_purity()
        
        # 3. インターフェース分離チェック
        self._check_interface_segregation()
        
        # 4. 依存関係逆転チェック
        self._check_dependency_inversion()
        
        # 5. 副作用の配置チェック
        self._check_side_effects()
        
        # 違反を種類別に分類
        results = {}
        for violation in self.violations:
            if violation.violation_type not in results:
                results[violation.violation_type] = []
            results[violation.violation_type].append(violation)
        
        return results
    
    def _check_layer_dependencies(self):
        """レイヤー間の依存関係をチェック"""
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            from_layer = self._get_layer_from_path(py_file)
            if not from_layer:
                continue
            
            imports = self._extract_imports(py_file)
            for import_info in imports:
                to_layer = self._get_layer_from_import(import_info['module'])
                if not to_layer:
                    continue
                
                if not self._is_valid_layer_dependency(from_layer, to_layer):
                    self.violations.append(Violation(
                        file_path=str(py_file),
                        line_number=import_info['line_number'],
                        violation_type="layer_dependency_violation",
                        description=f"不適切なレイヤー依存: {from_layer.value} -> {to_layer.value}",
                        severity="error"
                    ))
    
    def _check_domain_purity(self):
        """ドメイン層の純粋性をチェック"""
        operations_path = self.project_root / 'src' / 'operations'
        if not operations_path.exists():
            return
        
        for py_file in operations_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            imports = self._extract_imports(py_file)
            for import_info in imports:
                module = import_info['module']
                
                # 外部ライブラリの使用チェック
                if not self._is_allowed_external_dependency(module):
                    self.violations.append(Violation(
                        file_path=str(py_file),
                        line_number=import_info['line_number'],
                        violation_type="domain_purity_violation",
                        description=f"ドメイン層での外部依存: {module}",
                        severity="error"
                    ))
            
            # 副作用のチェック
            self._check_file_for_side_effects(py_file, ArchitectureLayer.DOMAIN)
    
    def _check_interface_segregation(self):
        """インターフェース分離の原則をチェック"""
        # インターフェース（プロトコル）の定義を検索
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            content = py_file.read_text(encoding='utf-8')
            
            # プロトコルクラスの検出
            protocol_matches = re.finditer(r'class\s+(\w+)\s*\([^)]*Protocol[^)]*\):', content)
            for match in protocol_matches:
                # プロトコルの詳細分析は将来の拡張で実装
                pass
    
    def _check_dependency_inversion(self):
        """依存関係逆転の原則をチェック"""
        infrastructure_path = self.project_root / 'src' / 'infrastructure'
        if not infrastructure_path.exists():
            return
        
        for py_file in infrastructure_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
            
            content = py_file.read_text(encoding='utf-8')
            
            # 具象クラスへの直接依存をチェック
            imports = self._extract_imports(py_file)
            for import_info in imports:
                module = import_info['module']
                if module.startswith('src.operations'):
                    # operations層への依存があるかチェック
                    if not self._is_interface_import(content, import_info):
                        self.violations.append(Violation(
                            file_path=str(py_file),
                            line_number=import_info['line_number'],
                            violation_type="dependency_inversion_violation",
                            description=f"具象クラスへの直接依存: {module}",
                            severity="warning"
                        ))
    
    def _check_side_effects(self):
        """副作用の適切な配置をチェック"""
        src_path = self.project_root / 'src'
        
        for py_file in src_path.rglob('*.py'):
            layer = self._get_layer_from_path(py_file)
            if layer:
                self._check_file_for_side_effects(py_file, layer)
    
    def _check_file_for_side_effects(self, py_file: Path, layer: ArchitectureLayer):
        """ファイル内の副作用をチェック"""
        # インフラ層以外では副作用は制限される
        if layer == ArchitectureLayer.INFRASTRUCTURE:
            return
        
        content = py_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # 改善されたパターン：コンテキストを考慮した副作用検出
        side_effect_patterns = [
            # ファイルI/O（依存性注入を除外）
            (r'(?<!_provider\.)(?<!provider\.)open\s*\(', 'ファイル操作'),
            (r'\bprint\s*\((?!["\'][^"\']*(debug|test)[^"\'])', 'コンソール出力'),
            (r'subprocess\.(run|call|check_output|Popen)', 'サブプロセス実行'),
            (r'os\.(system|remove|mkdir|rmdir)', 'OS操作'),
            (r'shutil\.(copy|move|rmtree)', 'ファイルシステム操作'),
            # HTTP通信（ローカル変数名を除外）
            (r'\brequests\.(get|post|put|delete|patch|head|options)', 'HTTP通信'),
            (r'socket\.(socket|connect|bind)', 'ネットワーク通信'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            # コメント行をスキップ
            if line.strip().startswith('#'):
                continue
            
            # 文字列リテラル内の誤検知を防ぐ
            cleaned_line = self._remove_string_literals(line)
            
            for pattern, description in side_effect_patterns:
                if re.search(pattern, cleaned_line):
                    # 依存性注入のコンテキストをチェック
                    if self._is_dependency_injection_context(content, line_num, cleaned_line):
                        continue
                    
                    severity = "error" if layer == ArchitectureLayer.DOMAIN else "warning"
                    self.violations.append(Violation(
                        file_path=str(py_file),
                        line_number=line_num,
                        violation_type="side_effect_violation",
                        description=f"{layer.value}層での副作用: {description}",
                        severity=severity
                    ))
    
    def _remove_string_literals(self, line: str) -> str:
        """文字列リテラル内のパターンを除外"""
        import re
        # 文字列リテラル（シングル・ダブルクォート）を空文字に置換
        line = re.sub(r"'[^']*'", "''", line)
        line = re.sub(r'"[^"]*"', '""', line)
        return line
    
    def _is_dependency_injection_context(self, content: str, line_num: int, line: str) -> bool:
        """依存性注入のコンテキストかどうかを判定"""
        import re
        lines = content.split('\n')
        
        # プロバイダーパターンの検出
        provider_patterns = [
            r'.*_provider\.',
            r'self\._.*_provider\.',
            r'provider\.',
            r'self\..*provider\.',
        ]
        
        for pattern in provider_patterns:
            if re.search(pattern, line):
                return True
        
        # 関数/メソッドの引数として注入されているかチェック（前後5行を確認）
        start = max(0, line_num - 6)
        end = min(len(lines), line_num + 5)
        context_lines = lines[start:end]
        
        for context_line in context_lines:
            # 関数定義で provider や _provider を引数として受け取っている
            if re.search(r'def\s+\w+\([^)]*provider[^)]*\):', context_line):
                return True
            # クラスの __init__ で provider を受け取っている
            if re.search(r'def\s+__init__\([^)]*provider[^)]*\):', context_line):
                return True
        
        return False
    
    def _get_layer_from_path(self, path: Path) -> Optional[ArchitectureLayer]:
        """ファイルパスからレイヤーを取得"""
        parts = path.parts
        src_index = None
        
        for i, part in enumerate(parts):
            if part == 'src':
                src_index = i
                break
        
        if src_index is None or src_index + 1 >= len(parts):
            return None
        
        layer_dir = parts[src_index + 1]
        return self.layer_mapping.get(layer_dir)
    
    def _get_layer_from_import(self, import_str: str) -> Optional[ArchitectureLayer]:
        """import文からレイヤーを取得"""
        if not import_str.startswith('src.'):
            return None
        
        parts = import_str.split('.')
        if len(parts) < 2:
            return None
        
        layer_dir = parts[1]
        return self.layer_mapping.get(layer_dir)
    
    def _extract_imports(self, py_file: Path) -> List[Dict]:
        """Pythonファイルからimport文を抽出"""
        imports = []
        content = py_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # from ... import ...
            match = re.match(r'from\s+([\w.]+)\s+import', line)
            if match:
                imports.append({
                    'module': match.group(1),
                    'line_number': line_num,
                    'type': 'from'
                })
            
            # import ...
            match = re.match(r'import\s+([\w.]+)', line)
            if match:
                imports.append({
                    'module': match.group(1),
                    'line_number': line_num,
                    'type': 'import'
                })
        
        return imports
    
    def _is_valid_layer_dependency(self, from_layer: ArchitectureLayer, to_layer: ArchitectureLayer) -> bool:
        """レイヤー間依存が有効かチェック"""
        if from_layer == to_layer:
            return True
        
        allowed = self.allowed_dependencies.get(from_layer, [])
        return to_layer in allowed
    
    def _is_allowed_external_dependency(self, module: str) -> bool:
        """外部依存が許可されているかチェック"""
        if module.startswith('src.'):
            return True
        
        # 標準ライブラリと許可された外部ライブラリをチェック
        base_module = module.split('.')[0]
        return base_module in self.allowed_external_deps
    
    def _is_interface_import(self, content: str, import_info: Dict) -> bool:
        """インターフェース（プロトコル）のimportかチェック"""
        # 簡易的なチェック - 実際にはより詳細な分析が必要
        if 'Protocol' in import_info['module']:
            return True
        if 'Interface' in import_info['module']:
            return True
        if 'interface' in import_info['module'].lower():
            return True
        return False


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    checker = CleanArchitectureChecker(project_root)
    results = checker.check_all()
    
    total_violations = 0
    error_count = 0
    warning_count = 0
    
    for category, violations in results.items():
        if violations:
            print(f"\n=== {category.upper().replace('_', ' ')} ===")
            for violation in violations:
                severity_symbol = "❌" if violation.severity == "error" else "⚠️"
                print(f"  {severity_symbol} {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                
                if violation.severity == "error":
                    error_count += 1
                else:
                    warning_count += 1
            
            total_violations += len(violations)
    
    print(f"\n=== 検査結果 ===")
    print(f"エラー: {error_count}件")
    print(f"警告: {warning_count}件")
    print(f"総違反: {total_violations}件")
    
    if error_count == 0:
        print("✅ クリーンアーキテクチャチェック完了: 重大な違反なし")
        return 0 if warning_count == 0 else 1
    else:
        print("❌ クリーンアーキテクチャチェック完了: 修正が必要な違反があります")
        return 1


if __name__ == "__main__":
    sys.exit(main())