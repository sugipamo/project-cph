#!/usr/bin/env python3
"""
Debug script to test TEST step type processing
"""
import json
from src.env_core.step.step import Step, StepType
from src.env_core.step.core import create_step_from_json
from src.operations.factory.unified_request_factory import ComplexRequestStrategy, create_request
from src.operations.environment.environment_manager import EnvironmentManager

class MockStepContext:
    """Mock context for testing step creation"""
    def __init__(self):
        self.contest_name = "abc300"
        self.problem_name = "a"
        self.language = "python"
        self.env_type = "local"
        self.command_type = "test"
        self.workspace_path = "./workspace"
        self.contest_current_path = "./contest_current"
        self.contest_stock_path = "./contest_stock"
        self.contest_template_path = "./contest_template"
        self.contest_temp_path = "./.temp"
        self.source_file_name = "main.py"
        self.language_id = "5078"
    
    def to_format_dict(self):
        return {
            'contest_name': self.contest_name,
            'problem_id': self.problem_name,
            'problem_name': self.problem_name,
            'language': self.language,
            'language_name': self.language,
            'env_type': self.env_type,
            'command_type': self.command_type,
            'workspace_path': self.workspace_path,
            'contest_current_path': self.contest_current_path,
            'contest_stock_path': self.contest_stock_path,
            'contest_template_path': self.contest_template_path,
            'contest_temp_path': self.contest_temp_path,
            'source_file_name': self.source_file_name,
            'language_id': self.language_id,
        }

class MockExecutionContext:
    """Mock execution context for testing request creation"""
    def __init__(self):
        self.env_type = "local"
        self.language = "python"
        self.contest_name = "abc300"
        self.problem_name = "a"
        self.command_type = "test"
    
    def format_string(self, template: str) -> str:
        """Simple formatting for testing"""
        replacements = {
            '{contest_name}': self.contest_name,
            '{problem_name}': self.problem_name,
            '{workspace_path}': './workspace',
            '{source_file_name}': 'main.py'
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        return result

def test_step_type_enum():
    """Test StepType enum values"""
    print("1. Testing StepType enum:")
    print(f"   StepType.TEST = {StepType.TEST}")
    print(f"   StepType.TEST.value = {StepType.TEST.value}")
    
    # Test creating StepType from string
    try:
        test_type = StepType("test")
        print(f"   StepType('test') = {test_type}")
        print(f"   StepType('test') == StepType.TEST: {test_type == StepType.TEST}")
    except ValueError as e:
        print(f"   ERROR creating StepType from 'test': {e}")
    
    print()

def test_json_step_creation():
    """Test creating Step from JSON data"""
    print("2. Testing Step creation from JSON:")
    
    # Test JSON data from system_info.json
    json_step = {
        "type": "test",
        "allow_failure": True,
        "show_output": True,
        "cmd": [
            "python3",
            "{workspace_path}/{source_file_name}"
        ]
    }
    
    print(f"   JSON step: {json.dumps(json_step, indent=2)}")
    
    context = MockStepContext()
    
    try:
        step = create_step_from_json(json_step, context)
        print(f"   Created Step:")
        print(f"     type: {step.type}")
        print(f"     type.value: {step.type.value}")
        print(f"     cmd: {step.cmd}")
        print(f"     allow_failure: {step.allow_failure}")
        print(f"     show_output: {step.show_output}")
        return step
    except Exception as e:
        print(f"   ERROR creating Step: {e}")
        return None
    
    print()

def test_complex_request_strategy(step):
    """Test ComplexRequestStrategy handling of TEST step"""
    print("3. Testing ComplexRequestStrategy:")
    
    strategy = ComplexRequestStrategy()
    
    print(f"   Can handle StepType.TEST: {strategy.can_handle(StepType.TEST)}")
    print(f"   Can handle step.type: {strategy.can_handle(step.type)}")
    
    context = MockExecutionContext()
    env_manager = EnvironmentManager("local")
    
    try:
        request = strategy.create_request(step, context, env_manager)
        print(f"   Created request: {request}")
        if request:
            print(f"     request type: {type(request).__name__}")
            print(f"     request.cmd: {request.cmd}")
            print(f"     request.allow_failure: {getattr(request, 'allow_failure', 'N/A')}")
        return request
    except Exception as e:
        print(f"   ERROR creating request: {e}")
        return None
    
    print()

def test_unified_factory(step):
    """Test unified factory request creation"""
    print("4. Testing unified factory:")
    
    context = MockExecutionContext()
    env_manager = EnvironmentManager("local")
    
    try:
        request = create_request(step, context, env_manager)
        print(f"   Created request: {request}")
        if request:
            print(f"     request type: {type(request).__name__}")
            print(f"     request.cmd: {request.cmd}")
            print(f"     request.allow_failure: {getattr(request, 'allow_failure', 'N/A')}")
        return request
    except Exception as e:
        print(f"   ERROR creating request: {e}")
        return None
    
    print()

def main():
    """Main debug function"""
    print("=== Debugging TEST step type processing ===\n")
    
    test_step_type_enum()
    step = test_json_step_creation()
    
    if step:
        test_complex_request_strategy(step)
        test_unified_factory(step)
    
    print("=== Debug complete ===")

if __name__ == "__main__":
    main()