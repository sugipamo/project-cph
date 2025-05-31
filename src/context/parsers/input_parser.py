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
        args, context = InputParser._apply_problem_name(args, context)
        args, context = InputParser._apply_contest_name(args, context)
        
        return args, context
    
    @staticmethod
    def _apply_language(args, context, root):
        """言語の適用"""
        print(f"[DEBUG] _apply_language: in args={args} context.language={context.language}")
        
        for idx, arg in enumerate(args):
            langs = resolve_by_match_desc(root, [arg])
            if langs:
                context.language = langs[0].key
                new_args = args[:idx] + args[idx+1:]
                print(f"[DEBUG] _apply_language: out args={new_args} context.language={context.language}")
                return new_args, context
        
        print(f"[DEBUG] _apply_language: out args={args} context.language={context.language}")
        return args, context
    
    @staticmethod
    def _apply_env_type(args, context, root):
        """環境タイプの適用"""
        print(f"[DEBUG] _apply_env_type: in args={args} context.env_type={context.env_type}")
        
        if context.language:
            env_type_nodes = resolve_by_match_desc(root, [context.language, "env_types"])
            for idx, arg in enumerate(args):
                for env_type_node in env_type_nodes:
                    for node in env_type_node.next_nodes:
                        if arg in node.matches:
                            context.env_type = node.key
                            new_args = args[:idx] + args[idx+1:]
                            print(f"[DEBUG] _apply_env_type: out args={new_args} context.env_type={context.env_type}")
                            return new_args, context
        
        print(f"[DEBUG] _apply_env_type: out args={args} context.env_type={context.env_type}")
        return args, context
    
    @staticmethod
    def _apply_command(args, context, root):
        """コマンドの適用"""
        print(f"[DEBUG] _apply_command: in args={args} context.command_type={context.command_type}")
        
        if context.language:
            command_nodes = resolve_by_match_desc(root, [context.language, "commands"])
            for idx, arg in enumerate(args):
                for command_node in command_nodes:
                    for node in command_node.next_nodes:
                        if arg in node.matches:
                            context.command_type = node.key
                            new_args = args[:idx] + args[idx+1:]
                            print(f"[DEBUG] _apply_command: out args={new_args} context.command_type={context.command_type}")
                            return new_args, context
        
        print(f"[DEBUG] _apply_command: out args={args} context.command_type={context.command_type}")
        return args, context
    
    @staticmethod
    def _apply_problem_name(args, context):
        """問題名の適用"""
        print(f"[DEBUG] _apply_problem_name: in args={args} context.problem_name={context.problem_name}")
        
        if args:
            context.problem_name = args.pop()
        
        print(f"[DEBUG] _apply_problem_name: out args={args} context.problem_name={context.problem_name}")
        return args, context
    
    @staticmethod
    def _apply_contest_name(args, context):
        """コンテスト名の適用"""
        print(f"[DEBUG] _apply_contest_name: in args={args} context.contest_name={context.contest_name}")
        
        if args:
            context.contest_name = args.pop()
        
        print(f"[DEBUG] _apply_contest_name: out args={args} context.contest_name={context.contest_name}")
        return args, context