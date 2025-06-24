"""
型ヒント追加器

ASTを使用して関数に型ヒントを自動追加します。
"""

import ast
from typing import Dict, Optional, List
from pathlib import Path

import sys
from pathlib import Path

# パスを追加してインポート
sys.path.append(str(Path(__file__).parent))
from type_inference import TypeInferenceEngine, FunctionAnalyzer


class TypeHintAdder:
    """型ヒントを追加するクラス"""
    
    def __init__(self):
        self.inference_engine = TypeInferenceEngine()
        self.modified_functions = []
    
    def add_type_hints_to_file(self, file_path: Path) -> bool:
        """
        ファイルに型ヒントを追加
        
        Args:
            file_path: 対象ファイルパス
            
        Returns:
            修正が行われたかどうか
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # return文を分析
            analyzer = FunctionAnalyzer()
            analyzer.visit(tree)
            
            # 型ヒントが必要な関数を検出
            functions_to_modify = self._find_functions_needing_hints(tree)
            
            if not functions_to_modify:
                return False
            
            # 修正されたコードを生成
            modified_content = self._modify_file_content(content, functions_to_modify, file_path)
            
            if modified_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                return True
            
            return False
            
        except (SyntaxError, Exception):
            return False
    
    def _find_functions_needing_hints(self, tree: ast.AST) -> List[ast.FunctionDef]:
        """型ヒントが必要な関数を検出"""
        functions_needing_hints = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._needs_type_hints(node):
                    functions_needing_hints.append(node)
        
        return functions_needing_hints
    
    def _needs_type_hints(self, func_node: ast.FunctionDef) -> bool:
        """関数が型ヒントを必要とするかチェック"""
        # 既に型ヒントがある引数をチェック
        for arg in func_node.args.args:
            if not arg.annotation:
                return True
        
        # 戻り値の型ヒントをチェック
        if not func_node.returns:
            return True
        
        return False
    
    def _modify_file_content(self, content: str, functions: List[ast.FunctionDef], file_path: Path) -> str:
        """ファイル内容を修正"""
        lines = content.split('\n')
        
        # 関数を逆順でソート（行番号の大きい順）
        # これにより、行番号の変更による影響を避ける
        functions = sorted(functions, key=lambda f: f.lineno, reverse=True)
        
        for func in functions:
            lines = self._modify_function_definition(lines, func, content, file_path)
        
        return '\n'.join(lines)
    
    def _modify_function_definition(self, lines: List[str], func_node: ast.FunctionDef, 
                                  full_content: str, file_path: Path) -> List[str]:
        """関数定義を修正"""
        func_line_idx = func_node.lineno - 1
        
        # 関数の使用パターンを分析
        usage_patterns = self.inference_engine.analyze_function_usage(func_node, full_content)
        
        # 引数の型を推論
        param_types = {}
        for arg in func_node.args.args:
            if not arg.annotation:  # 型ヒントがない場合のみ
                inferred_type = self.inference_engine.infer_parameter_type(
                    arg.arg, usage_patterns.get(arg.arg, [])
                )
                if inferred_type:
                    param_types[arg.arg] = inferred_type
        
        # 戻り値の型を推論
        return_type = None
        if not func_node.returns:  # 戻り値の型ヒントがない場合のみ
            return_statements = getattr(func_node, '_return_statements', [])
            return_type = self.inference_engine.infer_return_type(func_node.name, return_statements)
        
        # 関数定義行を修正
        if param_types or return_type:
            modified_line = self._build_modified_function_signature(
                lines[func_line_idx], func_node, param_types, return_type
            )
            if modified_line != lines[func_line_idx]:
                lines[func_line_idx] = modified_line
                self.modified_functions.append({
                    'file': str(file_path),
                    'line': func_node.lineno,
                    'function': func_node.name,
                    'added_types': param_types,
                    'return_type': return_type
                })
        
        return lines
    
    def _build_modified_function_signature(self, original_line: str, func_node: ast.FunctionDef,
                                         param_types: Dict[str, str], return_type: Optional[str]) -> str:
        """修正された関数シグネチャを構築"""
        # 関数定義の解析
        func_name = func_node.name
        
        # 引数リストを構築
        args = []
        for arg in func_node.args.args:
            arg_name = arg.arg
            if arg.annotation:
                # 既存の型ヒントを保持
                args.append(f"{arg_name}: {ast.unparse(arg.annotation)}")
            elif arg_name in param_types:
                # 新しい型ヒントを追加
                args.append(f"{arg_name}: {param_types[arg_name]}")
            else:
                # 型ヒントなし
                args.append(arg_name)
        
        # 関数シグネチャを再構築
        args_str = ', '.join(args)
        
        # インデントを保持
        indent = original_line[:len(original_line) - len(original_line.lstrip())]
        
        # 戻り値の型ヒントを追加
        if return_type and not func_node.returns:
            signature = f"{indent}def {func_name}({args_str}) -> {return_type}:"
        else:
            signature = f"{indent}def {func_name}({args_str}):"
        
        return signature
    
    def get_modification_summary(self) -> List[Dict]:
        """修正内容のサマリを取得"""
        return self.modified_functions.copy()