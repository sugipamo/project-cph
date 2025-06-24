#!/usr/bin/env python3
"""
Infrastructure層からOperations層への不適切な依存関係を検出するチェッカー

CLAUDE.mdルール:
- 副作用はsrc/infrastructure scripts/infrastructure のみとする
- すべてmain.pyから注入する
- Infrastructure層がOperations層に直接依存することは適切だが、
  特定のパターンは設計上問題がある可能性がある
"""

import os
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class InfrastructureOperationsChecker:
    def __init__(self, file_handler, logger, issues: List[str], verbose: bool = False):
        self.file_handler = file_handler
        self.logger = logger
        self.issues = issues
        self.verbose = verbose
        
        # 検出対象パターン
        self.import_patterns = [
            r'from\s+src\.operations\.([^.\s]+)\.([^.\s]+)\s+import\s+(.+)',
            r'import\s+src\.operations\.([^.\s]+)\.([^.\s]+)',
        ]
        
        # 高頻度パターン（要注意）
        self.high_frequency_imports = {
            'interfaces.logger_interface': 'LoggerInterface',
            'results.shell_result': 'ShellResult', 
            'results.docker_result': 'DockerResult',
            'results.result': 'OperationResult',
            'requests.file.file_op_type': 'FileOpType',
            'requests.base.base_request': 'OperationRequestFoundation',
        }
        
        # 許可されるパターン（適切な依存関係）
        self.allowed_patterns = {
            'interfaces',  # インターフェース実装は適切
            'results',     # 結果型使用は適切
            'exceptions',  # 例外処理は適切
            'constants',   # 定数使用は適切
            'types',       # 型定義使用は適切
        }
        
        # 要注意パターン（設計要検討）
        self.warning_patterns = {
            'requests',    # リクエスト型の直接使用
            'factories',   # ファクトリーの直接使用
        }

    def check_infrastructure_operations_dependencies(self):
        """Infrastructure層からOperations層への依存関係をチェック"""
        if self.verbose:
            self.logger.info("Infrastructure->Operations依存関係チェック開始")
        
        violations = []
        pattern_stats = defaultdict(int)
        file_violations = defaultdict(list)
        
        # src/infrastructure配下の全Pythonファイルを検査
        infrastructure_files = self._get_infrastructure_files()
        
        for file_path in infrastructure_files:
            try:
                content = self.file_handler.read_file(file_path)
                file_violations_found = self._check_file_operations_imports(
                    file_path, content, pattern_stats
                )
                if file_violations_found:
                    file_violations[file_path].extend(file_violations_found)
                    violations.extend(file_violations_found)
                    
            except Exception as e:
                if self.verbose:
                    self.logger.error(f"ファイル読み込みエラー: {file_path}: {e}")
                continue
        
        # 結果の分析と報告
        self._analyze_and_report_violations(violations, pattern_stats, file_violations)
        
        if self.verbose:
            self.logger.info("Infrastructure->Operations依存関係チェック完了")

    def _get_infrastructure_files(self) -> List[str]:
        """Infrastructure配下のPythonファイル一覧を取得"""
        infrastructure_files = []
        infrastructure_path = "src/infrastructure"
        
        if not os.path.exists(infrastructure_path):
            return infrastructure_files
            
        for root, dirs, files in os.walk(infrastructure_path):
            for file in files:
                if file.endswith('.py'):
                    infrastructure_files.append(os.path.join(root, file))
                    
        return infrastructure_files

    def _check_file_operations_imports(self, file_path: str, content: str, pattern_stats: Dict) -> List[str]:
        """ファイル内のoperationsインポートをチェック"""
        violations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # operationsインポートパターンを検出
            for pattern in self.import_patterns:
                match = re.search(pattern, line)
                if match:
                    violation = self._analyze_import_violation(
                        file_path, line_num, line, match, pattern_stats
                    )
                    if violation:
                        violations.append(violation)
                        
        return violations

    def _analyze_import_violation(self, file_path: str, line_num: int, line: str, 
                                match: re.Match, pattern_stats: Dict) -> str:
        """インポート違反を分析"""
        if len(match.groups()) >= 2:
            module_category = match.group(1)  # interfaces, results, requests, etc.
            module_name = match.group(2)      # logger_interface, shell_result, etc.
            
            # 統計情報を更新
            full_module_path = f"{module_category}.{module_name}"
            pattern_stats[full_module_path] += 1
            
            # 違反の種類を判定
            violation_type = self._classify_violation(module_category, full_module_path)
            
            if violation_type:
                return self._format_violation_message(
                    file_path, line_num, line, module_category, 
                    module_name, violation_type
                )
                
        return None

    def _classify_violation(self, module_category: str, full_module_path: str) -> str:
        """違反の種類を分類"""
        # 高頻度パターンのチェック
        if full_module_path in self.high_frequency_imports:
            return "high_frequency"
            
        # 要注意パターンのチェック
        if module_category in self.warning_patterns:
            return "warning"
            
        # 許可されるパターンは違反として扱わない
        if module_category in self.allowed_patterns:
            return None
            
        # その他の不明なパターン
        return "unknown"

    def _format_violation_message(self, file_path: str, line_num: int, line: str,
                                 module_category: str, module_name: str, 
                                 violation_type: str) -> str:
        """違反メッセージをフォーマット"""
        relative_path = file_path.replace("src/infrastructure/", "")
        
        if violation_type == "high_frequency":
            return (f"高頻度Operations依存検出: {relative_path}:{line_num}\n"
                   f"  パターン: {module_category}.{module_name}\n"
                   f"  インポート: {line}\n"
                   f"  推奨: このパターンが頻繁に使用されています。設計を見直してください")
                   
        elif violation_type == "warning":
            return (f"要注意Operations依存検出: {relative_path}:{line_num}\n"
                   f"  パターン: {module_category}.{module_name}\n"
                   f"  インポート: {line}\n"
                   f"  推奨: {module_category}の直接使用は設計を見直してください")
                   
        elif violation_type == "unknown":
            return (f"未知のOperations依存検出: {relative_path}:{line_num}\n"
                   f"  パターン: {module_category}.{module_name}\n"
                   f"  インポート: {line}\n"
                   f"  推奨: このパターンを分析し、適切性を確認してください")
                   
        return ""

    def _analyze_and_report_violations(self, violations: List[str], 
                                     pattern_stats: Dict, 
                                     file_violations: Dict):
        """違反を分析してレポート"""
        if not violations:
            if self.verbose:
                self.logger.info("Infrastructure->Operations依存関係: 問題なし")
            return
            
        # 統計情報の生成
        total_violations = len(violations)
        affected_files = len(file_violations)
        
        # 最も頻繁なパターンの特定
        top_patterns = sorted(pattern_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 違反レポートの生成
        violation_report = self._generate_violation_report(
            total_violations, affected_files, top_patterns, violations
        )
        
        self.issues.append(f"Infrastructure->Operations依存関係違反: {violation_report}")

    def _generate_violation_report(self, total_violations: int, affected_files: int,
                                 top_patterns: List[Tuple[str, int]], 
                                 violations: List[str]) -> str:
        """違反レポートを生成"""
        report_lines = [
            f"検出された違反: {total_violations}件（{affected_files}ファイル）",
            "",
            "最頻出パターン:",
        ]
        
        for pattern, count in top_patterns:
            report_lines.append(f"  {pattern}: {count}件")
            
        report_lines.extend([
            "",
            "修正推奨:",
            "  1. 高頻度パターンは共通インターフェースに抽出",
            "  2. requests層の直接使用は設計見直し",
            "  3. main.pyからの依存性注入を強化",
            "",
            "詳細な違反箇所:",
        ])
        
        # 最初の5件の詳細を表示
        for violation in violations[:5]:
            report_lines.append(f"  {violation}")
            
        if len(violations) > 5:
            report_lines.append(f"  ... 他{len(violations) - 5}件")
            
        return "\n".join(report_lines)