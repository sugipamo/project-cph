"""
型推論エンジン

コードの使用パターンから変数や関数の型を推測します。
"""

import ast
from typing import Dict, Optional, Set, List
from pathlib import Path


class TypeInferenceEngine:
    """型推論を行うクラス"""
    
    def __init__(self):
        # 一般的な型マッピング
        self.common_types = {
            'str': {'string', 'text', 'name', 'path', 'url', 'message', 'content'},
            'int': {'count', 'size', 'length', 'number', 'port', 'timeout'},
            'bool': {'flag', 'enabled', 'disabled', 'active', 'valid'},
            'List': {'list', 'items', 'values', 'entries'},
            'Dict': {'config', 'settings', 'params', 'options'},
        }
        
        # 戻り値型の推論
        self.return_patterns = {
            'get_': 'Optional',
            'is_': 'bool',
            'has_': 'bool',
            'count_': 'int',
            'find_': 'Optional',
            'create_': None,  # 作成されるオブジェクトの型
            'build_': None,
        }
    
    def infer_parameter_type(self, param_name: str, usage_context: List[str]) -> Optional[str]:
        """
        引数名と使用コンテキストから型を推論
        
        Args:
            param_name: 引数名
            usage_context: 使用パターンのリスト
            
        Returns:
            推論された型名
        """
        # 引数名からの推論
        param_lower = param_name.lower()
        
        for type_name, keywords in self.common_types.items():
            if any(keyword in param_lower for keyword in keywords):
                return type_name
        
        # 使用パターンからの推論
        for context in usage_context:
            if '.append(' in context or '.extend(' in context:
                return 'List'
            elif '.get(' in context or '[' in context and ']' in context:
                return 'Dict'
            elif '.startswith(' in context or '.endswith(' in context:
                return 'str'
            elif ' + ' in context and 'str' not in context:
                return 'int'
        
        return None
    
    def infer_return_type(self, func_name: str, return_statements: List[str]) -> Optional[str]:
        """
        関数名と戻り値から戻り値型を推論
        
        Args:
            func_name: 関数名
            return_statements: return文のリスト
            
        Returns:
            推論された戻り値型
        """
        # 関数名からの推論
        for pattern, return_type in self.return_patterns.items():
            if func_name.startswith(pattern):
                return return_type
        
        # return文からの推論
        if not return_statements:
            return 'None'
        
        # すべてのreturn文を分析
        inferred_types = set()
        for stmt in return_statements:
            if stmt.strip() == 'None':
                inferred_types.add('None')
            elif stmt.strip().startswith('"') or stmt.strip().startswith("'"):
                inferred_types.add('str')
            elif stmt.strip().isdigit():
                inferred_types.add('int')
            elif stmt.strip() in ['True', 'False']:
                inferred_types.add('bool')
            elif stmt.strip().startswith('['):
                inferred_types.add('List')
            elif stmt.strip().startswith('{'):
                inferred_types.add('Dict')
        
        # 複数の型がある場合はUnionか最も一般的な型を返す
        if len(inferred_types) == 1:
            return inferred_types.pop()
        elif 'None' in inferred_types:
            inferred_types.remove('None')
            if len(inferred_types) == 1:
                return f'Optional[{inferred_types.pop()}]'
        
        return None
    
    def analyze_function_usage(self, func_node: ast.FunctionDef, file_content: str) -> Dict[str, List[str]]:
        """
        関数内での引数の使用パターンを分析
        
        Args:
            func_node: 関数のASTノード
            file_content: ファイル全体の内容
            
        Returns:
            引数名をキーとした使用パターンのリスト
        """
        usage_patterns = {}
        
        # 関数の引数名を取得
        param_names = [arg.arg for arg in func_node.args.args]
        
        # 関数本体を文字列として取得
        lines = file_content.split('\n')
        func_start = func_node.lineno - 1
        func_end = func_node.end_lineno if hasattr(func_node, 'end_lineno') else len(lines)
        
        func_body = '\n'.join(lines[func_start:func_end])
        
        for param in param_names:
            patterns = []
            # パラメータの使用箇所を検索
            for line in func_body.split('\n'):
                if param in line and not line.strip().startswith('def '):
                    patterns.append(line.strip())
            usage_patterns[param] = patterns
        
        return usage_patterns


class FunctionAnalyzer(ast.NodeVisitor):
    """関数を分析してreturn文を収集"""
    
    def __init__(self):
        self.return_statements = []
        self.current_function = None
    
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        old_returns = self.return_statements
        
        self.current_function = node.name
        self.return_statements = []
        
        self.generic_visit(node)
        
        # 結果を保存
        node._return_statements = self.return_statements.copy()
        
        self.current_function = old_function
        self.return_statements = old_returns
    
    def visit_Return(self, node):
        if node.value:
            # return文の値を文字列として取得
            if isinstance(node.value, ast.Constant):
                self.return_statements.append(repr(node.value.value))
            elif isinstance(node.value, ast.Name):
                self.return_statements.append(node.value.id)
            elif isinstance(node.value, ast.List):
                self.return_statements.append('[]')
            elif isinstance(node.value, ast.Dict):
                self.return_statements.append('{}')
            else:
                self.return_statements.append('unknown')
        else:
            self.return_statements.append('None')