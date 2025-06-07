"""
Output display control class
"""
from typing import List, Any, Callable
from src.application.orchestration.output_formatters import (
    extract_output_data, should_show_output, 
    decide_output_action
)


class OutputManager:
    """Responsible for controlling request execution result output"""
    
    @staticmethod
    def handle_request_output(request: Any, result: Any) -> None:
        """
        Process the output of request execution result
        
        Args:
            request: Executed request
            result: Execution result
        """
        # Use pure functions to decide output
        show_output_flag = should_show_output(request)
        output_data = extract_output_data(result)
        should_output, output_text = decide_output_action(show_output_flag, output_data)
        
        # Print only when output is needed (side effect)
        if should_output:
            print(output_text, end="")
    
    @classmethod
    def execute_with_output_handling(cls, requests: List[Any], 
                                   execution_func: Callable[[Any, Any], Any], 
                                   driver: Any) -> List[Any]:
        """
        Execute requests with output handling
        
        Args:
            requests: List of requests to execute
            execution_func: Execution function
            driver: Execution driver
            
        Returns:
            List of execution results
        """
        results = []
        for req in requests:
            result = execution_func(req, driver)
            cls.handle_request_output(req, result)
            results.append(result)
        
        return results