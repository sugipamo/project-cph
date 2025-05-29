from src.context.resolver.config_resolver import resolve_format_string

class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_step):
        raise NotImplementedError
    
    def create_request_from_node(self, node):
        """ConfigNodeからリクエストを生成"""
        raise NotImplementedError
    
    def format_value(self, value, node):
        """
        値をフォーマットする。文字列の場合はresolve_format_stringを使用。
        
        Args:
            value: フォーマットする値
            node: 値を持つConfigNode
            
        Returns:
            フォーマット済みの値
        """
        if not isinstance(value, str):
            return value
            
        # ユーザーインプットの初期値
        initial_values = {
            "contest_name": self.controller.env_context.contest_name,
            "problem_id": self.controller.env_context.problem_name,
            "problem_name": self.controller.env_context.problem_name,
            "language": self.controller.env_context.language,
            "language_name": self.controller.env_context.language,
            "env_type": self.controller.env_context.env_type,
            "command_type": self.controller.env_context.command_type
        }
        
        # 値を持つnodeを起点にresolve_format_stringでフォーマット
        # 一時的にnodeの値を設定
        original_value = node.value
        node.value = value
        result = resolve_format_string(node, initial_values)
        node.value = original_value
        
        return result 