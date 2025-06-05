"""
Command line input parser
"""
from typing import List, Tuple
from ..execution_context import ExecutionContext
from src.context.resolver.config_resolver import resolve_by_match_desc


class InputParser:
    """コマンドライン引数の解析を担当"""
    
    @staticmethod
    def parse_command_line(args: List[str], context: ExecutionContext, root) -> Tuple[List[str], ExecutionContext]:
        """
        コマンドライン引数を解析してコンテキストを更新
        
        Args:
            args: コマンドライン引数
            context: 実行コンテキスト
            root: 設定ルート
            
        Returns:
            Tuple[List[str], ExecutionContext]: (残りの引数, 更新されたコンテキスト)
        """
        # 順次処理を適用
        args, context = InputParser._apply_language(args, context, root)
        args, context = InputParser._apply_env_type(args, context, root)
        args, context = InputParser._apply_command(args, context, root)
        args, context = InputParser._apply_contest_name(args, context)
        args, context = InputParser._apply_problem_name(args, context)
        
        return args, context
    
    @staticmethod
    def _apply_language(args, context, root):
        """言語の適用"""
        for idx, arg in enumerate(args):
            # 第1レベルのノード（言語）のみをチェック
            for lang_node in root.next_nodes:
                if arg in lang_node.matches:
                    context.language = lang_node.key
                    new_args = args[:idx] + args[idx+1:]
                    return new_args, context
        
        return args, context
    
    @staticmethod
    def _apply_env_type(args, context, root):
        """環境タイプの適用"""
        if context.language:
            env_type_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
            for idx, arg in enumerate(args):
                for env_type_node in env_type_nodes:
                    for node in env_type_node.next_nodes:
                        if arg in node.matches:
                            context.env_type = node.key
                            new_args = args[:idx] + args[idx+1:]
                            return new_args, context
        
        return args, context
    
    @staticmethod
    def _apply_command(args, context, root):
        """コマンドの適用"""
        if context.language:
            command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
            for idx, arg in enumerate(args):
                for command_node in command_nodes:
                    for node in command_node.next_nodes:
                        if arg in node.matches:
                            context.command_type = node.key
                            new_args = args[:idx] + args[idx+1:]
                            return new_args, context
        
        return args, context
    
    @staticmethod
    def _apply_problem_name(args, context):
        """問題名の適用"""
        if args:
            context.problem_name = args.pop()
        
        return args, context
    
    @staticmethod
    def _apply_contest_name(args, context):
        """コンテスト名の適用"""
        if args:
            context.contest_name = args.pop()
        
        return args, context