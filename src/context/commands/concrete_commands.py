"""
Concrete command implementations
"""
from typing import List, Dict, Any, Optional
from .base_command import Command


class OpenCommand(Command):
    """Command to open a contest problem"""
    
    def __init__(self):
        super().__init__()
        self._aliases = ["o"]
        self._description = "コンテストを開く"
    
    @property
    def name(self) -> str:
        return "open"
    
    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        """Validate open command requirements"""
        if not hasattr(context, 'contest_name') or not context.contest_name:
            return False, "Contest name is required for open command"
        if not hasattr(context, 'problem_name') or not context.problem_name:
            return False, "Problem name is required for open command"
        return True, None
    
    def get_steps(self, context: Any) -> List[Dict[str, Any]]:
        """Get steps from context configuration"""
        # This will be refactored to use context's configuration
        # For now, delegate to existing logic
        return []


class TestRunCommand(Command):
    """Command to run tests"""
    
    def __init__(self):
        super().__init__()
        self._aliases = ["t"]
        self._description = "テストを実行する"
    
    @property
    def name(self) -> str:
        return "test"
    
    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        """Validate test command requirements"""
        if not hasattr(context, 'problem_name') or not context.problem_name:
            return False, "Problem name is required for test command"
        return True, None
    
    def get_steps(self, context: Any) -> List[Dict[str, Any]]:
        """Get steps from context configuration"""
        return []


class SubmitCommand(Command):
    """Command to submit a solution"""
    
    def __init__(self):
        super().__init__()
        self._aliases = ["s"]
        self._description = "提出する"
    
    @property
    def name(self) -> str:
        return "submit"
    
    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        """Validate submit command requirements"""
        if not hasattr(context, 'contest_name') or not context.contest_name:
            return False, "Contest name is required for submit command"
        if not hasattr(context, 'problem_name') or not context.problem_name:
            return False, "Problem name is required for submit command"
        return True, None
    
    def get_steps(self, context: Any) -> List[Dict[str, Any]]:
        """Get steps from context configuration"""
        return []


class NewCommand(Command):
    """Command to create a new problem"""
    
    def __init__(self):
        super().__init__()
        self._aliases = ["n"]
        self._description = "新しい問題を作成する"
    
    @property
    def name(self) -> str:
        return "new"
    
    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        """Validate new command requirements"""
        if not hasattr(context, 'contest_name') or not context.contest_name:
            return False, "Contest name is required for new command"
        if not hasattr(context, 'problem_name') or not context.problem_name:
            return False, "Problem name is required for new command"
        return True, None
    
    def get_steps(self, context: Any) -> List[Dict[str, Any]]:
        """Get steps from context configuration"""
        return []