from src.context.resolver.config_resolver import resolve_format_string

class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_step):
        raise NotImplementedError
    
    def create_request_from_node(self, node):
        """ConfigNodeからリクエストを生成"""
        raise NotImplementedError
    
    def format_string(self, value):
        """
        文字列値をフォーマットする（シンプル版）
        
        Args:
            value: フォーマットする値
            
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
        
        # 簡単な置換処理
        result = value
        for key, val in initial_values.items():
            result = result.replace(f"{{{key}}}", str(val))
        
        return result

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
    
    def set_request_attributes(self, request, run_step_or_node):
        """
        requestにallow_failureとshow_outputを設定する共通メソッド
        
        Args:
            request: 設定対象のRequest
            run_step_or_node: RunStepまたはConfigNode
        """
        if hasattr(run_step_or_node, 'allow_failure'):
            # RunStepの場合
            request.allow_failure = getattr(run_step_or_node, 'allow_failure', False)
            request.show_output = getattr(run_step_or_node, 'show_output', False)
        elif hasattr(run_step_or_node, 'value') and isinstance(run_step_or_node.value, dict):
            # ConfigNodeの場合
            request.allow_failure = run_step_or_node.value.get('allow_failure', False)
            request.show_output = run_step_or_node.value.get('show_output', False)
        
        return request 