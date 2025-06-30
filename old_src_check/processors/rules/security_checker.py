#!/usr/bin/env python3
"""
セキュリティチェッカー - セキュリティ問題を検出
"""

import ast
import re
from pathlib import Path
from typing import List, Pattern

from src_check.models.check_result import CheckResult, LogLevel, FailureLocation


class SecurityChecker(ast.NodeVisitor):
    """セキュリティ問題を検出するチェッカー"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []
        
        # セキュリティパターンの定義
        self.hardcoded_patterns = [
            re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
            re.compile(r'secret\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
            re.compile(r'api_key\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
            re.compile(r'token\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        ]
        
        self.dangerous_functions = [
            'eval', 'exec', 'compile', '__import__',
            'os.system', 'subprocess.call', 'subprocess.run'
        ]
    
    def visit_Str(self, node):
        """文字列リテラルをチェック"""
        if hasattr(node, 's'):
            self._check_hardcoded_secrets(node, node.s)
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """定数をチェック（Python 3.8+）"""
        if isinstance(node.value, str):
            self._check_hardcoded_secrets(node, node.value)
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """関数呼び出しをチェック"""
        func_name = self._get_function_name(node)
        
        # 危険な関数の使用をチェック
        if func_name in self.dangerous_functions:
            self.violations.append({
                'type': 'unsafe_function',
                'line': node.lineno,
                'message': f"危険な関数 '{func_name}' の使用を検出",
                'severity': 'HIGH'
            })
        
        # SQLインジェクションの可能性をチェック
        if func_name in ['execute', 'cursor.execute'] and node.args:
            if self._has_string_concatenation(node.args[0]):
                self.violations.append({
                    'type': 'sql_injection',
                    'line': node.lineno,
                    'message': "SQLインジェクションの可能性があるクエリを検出",
                    'severity': 'CRITICAL'
                })
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """import文をチェック"""
        for alias in node.names:
            if alias.name in ['pickle', 'cPickle']:
                self.violations.append({
                    'type': 'insecure_deserialization',
                    'line': node.lineno,
                    'message': "安全でないデシリアライゼーション（pickle）の使用",
                    'severity': 'MEDIUM'
                })
        self.generic_visit(node)
    
    def _check_hardcoded_secrets(self, node, string_value):
        """ハードコードされたシークレットをチェック"""
        for pattern in self.hardcoded_patterns:
            if pattern.search(string_value):
                self.violations.append({
                    'type': 'hardcoded_secret',
                    'line': node.lineno,
                    'message': "ハードコードされたシークレット（パスワード、APIキーなど）を検出",
                    'severity': 'CRITICAL'
                })
                break
    
    def _get_function_name(self, node):
        """関数名を取得"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            else:
                return node.func.attr
        return ""
    
    def _has_string_concatenation(self, node):
        """文字列連結があるかチェック"""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return True
        elif isinstance(node, ast.JoinedStr):  # f-string
            return True
        return False


def main():
    """メイン実行関数"""
    try:
        # カレントディレクトリ内のPythonファイルをチェック
        python_files = list(Path.cwd().rglob("*.py"))
        
        if not python_files:
            return CheckResult(
                title="security_check",
                log_level=LogLevel.INFO,
                failure_locations=[],
                fix_policy="Python ファイルが見つかりませんでした",
                fix_example_code=None
            )
        
        all_violations = []
        
        for file_path in python_files:
            # __pycache__ などを除外
            if "__pycache__" in str(file_path) or ".git" in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ASTパース
                tree = ast.parse(content, filename=str(file_path))
                
                # セキュリティチェック実行
                checker = SecurityChecker(str(file_path))
                checker.visit(tree)
                
                # 違反を記録
                for violation in checker.violations:
                    all_violations.append(
                        FailureLocation(str(file_path), violation['line'])
                    )
            
            except (SyntaxError, UnicodeDecodeError):
                # 構文エラーやエンコードエラーは無視
                continue
            except Exception as e:
                # その他のエラーは記録
                all_violations.append(
                    FailureLocation(str(file_path), 1)
                )
        
        # 結果の作成
        if all_violations:
            severity_counts = {}
            violation_details = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                    checker = SecurityChecker(str(file_path))
                    checker.visit(tree)
                    
                    for violation in checker.violations:
                        severity = violation['severity']
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        violation_details.append(f"  {file_path}:{violation['line']} - {violation['message']}")
                
                except:
                    continue
            
            # 最高重要度を決定
            if severity_counts.get('CRITICAL', 0) > 0:
                log_level = LogLevel.CRITICAL
            elif severity_counts.get('HIGH', 0) > 0:
                log_level = LogLevel.ERROR
            else:
                log_level = LogLevel.WARNING
            
            fix_example = "セキュリティ問題の詳細:\n" + "\n".join(violation_details[:10])
            if len(violation_details) > 10:
                fix_example += f"\n... 他 {len(violation_details) - 10} 件"
            
            return CheckResult(
                title="Security Issues Detected",
                log_level=log_level,
                failure_locations=all_violations,
                fix_policy=f"{len(all_violations)}件のセキュリティ問題を検出しました",
                fix_example_code=fix_example
            )
        else:
            return CheckResult(
                title="security_check",
                log_level=LogLevel.INFO,
                failure_locations=[],
                fix_policy="セキュリティ問題は検出されませんでした",
                fix_example_code=None
            )
    
    except Exception as e:
        return CheckResult(
            title="security_check_ERROR",
            log_level=LogLevel.ERROR,
            failure_locations=[],
            fix_policy=f"セキュリティチェック実行エラー: {str(e)}",
            fix_example_code=None
        )


if __name__ == "__main__":
    result = main()
    print(f"セキュリティチェック結果: {result.fix_policy}")