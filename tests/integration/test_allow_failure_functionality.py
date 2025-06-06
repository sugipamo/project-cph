"""
Test allow_failure functionality with real scenarios
Tests for the issue where allow_failure=true is not working properly for copy operations
"""
import pytest
import json
import os
from unittest.mock import Mock, patch
from tests.base.base_test import BaseTest

from src.context.user_input_parser import parse_user_input
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.composite.composite_request import CompositeRequest
from src.operations.exceptions.composite_step_failure import CompositeStepFailure
from src.env_core.step.workflow import generate_workflow_from_json
from src.env_core.step.step import StepContext


class TestAllowFailureFunctionality(BaseTest):
    """Test allow_failure functionality in various scenarios"""
    
    def setup_test(self):
        """Setup test data"""
        self.operations = self.create_mock_di_container()
        self.mock_file_driver = self.operations.resolve("file_driver")
    
    def test_copy_with_allow_failure_true_file_not_exists(self):
        """Test copy operation with allow_failure=true when source file doesn't exist"""
        # Create a copy request where source file doesn't exist
        request = FileRequest(
            op=FileOpType.COPY,
            path="nonexistent_file.txt",
            dst_path="destination.txt",
            allow_failure=True
        )
        
        # Ensure source file doesn't exist
        self.mock_file_driver.setup_file_not_exists("nonexistent_file.txt")
        
        # Execute should not raise exception due to allow_failure=True
        result = request.execute(driver=self.mock_file_driver)
        
        # Verify the result indicates failure but execution completed
        # This test will help us understand current behavior
        print(f"Result success: {getattr(result, 'success', 'no success attribute')}")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
    
    def test_copy_with_allow_failure_false_file_not_exists(self):
        """Test copy operation with allow_failure=false when source file doesn't exist"""
        # Create a copy request where source file doesn't exist
        request = FileRequest(
            op=FileOpType.COPY,
            path="nonexistent_file.txt",
            dst_path="destination.txt",
            allow_failure=False
        )
        
        # Ensure source file doesn't exist
        self.mock_file_driver.setup_file_not_exists("nonexistent_file.txt")
        
        # Execute should raise exception
        with pytest.raises(Exception):
            request.execute(driver=self.mock_file_driver)
    
    def test_composite_request_with_allow_failure_step(self):
        """Test CompositeRequest with a step that has allow_failure=true"""
        # Create requests with mixed allow_failure settings
        success_request = FileRequest(
            op=FileOpType.TOUCH,
            path="success_file.txt",
            allow_failure=False
        )
        
        failing_request = FileRequest(
            op=FileOpType.COPY,
            path="nonexistent_source.txt",
            dst_path="destination.txt",
            allow_failure=True  # This should allow continuation
        )
        
        final_request = FileRequest(
            op=FileOpType.TOUCH,
            path="final_file.txt",
            allow_failure=False
        )
        
        # Setup file system
        self.mock_file_driver.setup_file_not_exists("nonexistent_source.txt")
        
        # Create composite request
        composite = CompositeRequest([success_request, failing_request, final_request])
        
        # Execute - should complete all steps despite middle failure
        try:
            results = composite.execute(driver=self.mock_file_driver)
            
            # Verify all three requests were executed
            assert len(results) == 3
            print(f"All results completed: {len(results)} steps")
            
            # Check individual results
            for i, result in enumerate(results):
                print(f"Step {i+1} success: {getattr(result, 'success', 'no success attr')}")
        
        except CompositeStepFailure as e:
            pytest.fail(f"CompositeRequest failed unexpectedly with allow_failure=True: {e}")
        except Exception as e:
            print(f"Unexpected exception type: {type(e)}")
            print(f"Exception message: {e}")
            # We want to see what's actually happening
            pass
    
    def test_workflow_execution_with_missing_previous_files(self):
        """Test workflow execution simulating the abc400 open scenario"""
        
        # Create step context with previous contest data
        context = StepContext(
            contest_name="abc400",
            problem_name="a",
            language="python",
            env_type="local",
            command_type="open",
            workspace_path="./workspace",
            contest_current_path="./contest_current",
            contest_stock_path="./contest_stock",
            contest_template_path="./contest_template",
            source_file_name="main.py",
            previous_contest_name="abc399",  # Previous contest
            previous_problem_name="a"        # Previous problem
        )
        
        # Define JSON steps similar to the open command
        json_steps = [
            {
                "type": "copy",
                "allow_failure": True,
                "show_output": False,
                "force_env_type": "local",
                "cmd": [
                    "{contest_current_path}/{source_file_name}",
                    "{contest_stock_path}/{previous_contest_name}/{previous_problem_id}/{source_file_name}"
                ]
            },
            {
                "type": "copy", 
                "allow_failure": True,
                "show_output": False,
                "force_env_type": "local",
                "cmd": [
                    "{contest_template_path}/{language_name}/{source_file_name}",
                    "{contest_current_path}/{source_file_name}"
                ]
            }
        ]
        
        # Setup file system - template exists, but previous contest stock doesn't
        self.mock_file_driver.setup_file_content("./contest_template/python/main.py", "# Template file")
        self.mock_file_driver.setup_file_not_exists("./contest_stock/abc399/a/main.py")  # Previous doesn't exist
        self.mock_file_driver.setup_file_not_exists("./contest_current/main.py")  # Current doesn't exist initially
        
        # Generate and execute workflow
        try:
            composite_request, errors, warnings = generate_workflow_from_json(
                json_steps, context, self.operations
            )
            
            print(f"Generation errors: {errors}")
            print(f"Generation warnings: {warnings}")
            
            if errors:
                pytest.fail(f"Workflow generation failed: {errors}")
            
            # Execute the workflow
            results = composite_request.execute(driver=self.operations)
            
            print(f"Workflow executed successfully with {len(results)} steps")
            
            # Verify both steps were attempted despite first one potentially failing
            # The key test is that execution continues even if first copy fails
            assert len(results) >= 2, "Both copy steps should be attempted"
            
        except CompositeStepFailure as e:
            # This is the bug - allow_failure=True should prevent this exception
            pytest.fail(f"Workflow failed with allow_failure=True: {e}")
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            raise
    
    def test_file_request_error_handling_behavior(self):
        """Test how FileRequest handles errors and success/failure reporting"""
        
        # Test COPY operation with non-existent source
        copy_request = FileRequest(
            op=FileOpType.COPY,
            path="missing_source.txt",
            dst_path="destination.txt",
            allow_failure=True
        )
        
        self.mock_file_driver.setup_file_not_exists("missing_source.txt")
        
        # Execute and examine the result
        try:
            result = copy_request.execute(driver=self.mock_file_driver)
            
            # Debug: Print result attributes
            print(f"FileRequest result type: {type(result)}")
            print(f"FileRequest result: {result}")
            print(f"Has success attr: {hasattr(result, 'success')}")
            if hasattr(result, 'success'):
                print(f"Success value: {result.success}")
            
            # Check if result properly indicates failure
            if hasattr(result, 'success'):
                # If it has success attribute, verify allow_failure logic
                if not result.success:
                    print("✓ FileRequest correctly reported failure")
                else:
                    print("✗ FileRequest incorrectly reported success for missing file")
            else:
                print("✗ FileRequest result missing success attribute")
                
        except Exception as e:
            print(f"FileRequest threw exception despite allow_failure=True: {type(e).__name__}: {e}")
            # This might be the bug - it should not throw exception with allow_failure=True
    
    def test_execution_controller_allow_failure_logic(self):
        """Test ExecutionController._check_failure logic directly"""
        from src.operations.composite.execution_controller import ExecutionController
        
        controller = ExecutionController()
        
        # Create a mock request with allow_failure=True
        mock_request = Mock()
        mock_request.allow_failure = True
        
        # Create a mock result indicating failure
        mock_result = Mock()
        mock_result.success = False
        
        # This should NOT raise an exception
        try:
            controller._check_failure(mock_request, mock_result)
            print("✓ ExecutionController correctly handled allow_failure=True")
        except CompositeStepFailure:
            pytest.fail("ExecutionController raised exception despite allow_failure=True")
        
        # Test with allow_failure=False
        mock_request.allow_failure = False
        
        # This SHOULD raise an exception
        with pytest.raises(CompositeStepFailure):
            controller._check_failure(mock_request, mock_result)
            
        print("✓ ExecutionController correctly raised exception with allow_failure=False")
    
    @patch('src.context.user_input_parser._load_all_env_jsons')
    @patch('src.context.user_input_parser.create_config_root_from_dict')
    def test_real_abc400_open_scenario(self, mock_create_root, mock_load_env_jsons):
        """Test the real abc400 open scenario that's failing"""
        
        # Setup system info with previous contest
        existing_system_info = {
            "command": "open",
            "language": "python",
            "contest_name": "abc399",  # Previous contest
            "problem_name": "a",       # Previous problem
            "env_type": "local",
            "env_json": None
        }
        self.mock_file_driver.setup_file_content("system_info.json", json.dumps(existing_system_info))
        
        # Setup env json with open command including previous backup step
        python_env = {
            "python": {
                "language_name": "Python",
                "source_file_name": "main.py",
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock", 
                "contest_template_path": "./contest_template",
                "commands": {
                    "open": {
                        "description": "コンテストを開く",
                        "steps": [
                            {
                                "type": "copy",
                                "allow_failure": True,
                                "show_output": False,
                                "force_env_type": "local",
                                "cmd": [
                                    "{contest_current_path}/{source_file_name}",
                                    "{contest_stock_path}/{previous_contest_name}/{previous_problem_id}/{source_file_name}"
                                ]
                            },
                            {
                                "type": "copy",
                                "allow_failure": True,
                                "show_output": False,
                                "force_env_type": "local", 
                                "cmd": [
                                    "{contest_template_path}/{language_name}/{source_file_name}",
                                    "{contest_current_path}/{source_file_name}"
                                ]
                            }
                        ]
                    }
                },
                "env_types": {
                    "local": {"aliases": ["local"]}
                }
            }
        }
        mock_load_env_jsons.return_value = [python_env]
        
        # Setup config root
        mock_root = Mock()
        python_node = Mock()
        python_node.key = "python"
        python_node.matches = ["python", "py"]
        mock_root.next_nodes = [python_node]
        mock_create_root.return_value = mock_root
        
        # Setup file system - template exists, previous stock doesn't exist
        self.mock_file_driver.setup_file_content("./contest_template/Python/main.py", "# Template")
        self.mock_file_driver.setup_file_not_exists("./contest_current/main.py")  # No current file
        self.mock_file_driver.setup_file_not_exists("./contest_stock/abc399/a/main.py")  # No previous stock
        
        # Setup shared config (empty)
        shared_path = os.path.join("contest_env", "shared", "env.json")
        self.mock_file_driver.setup_file_not_exists(shared_path)
        
        # Parse user input for new contest
        args = ["py", "local", "open", "abc400", "a"]
        
        with patch('src.context.user_input_parser.ValidationService'):
            try:
                context = parse_user_input(args, self.operations)
                
                # Verify context has previous information
                assert context.previous_contest_name == "abc399"
                assert context.previous_problem_name == "a"
                
                print(f"✓ Context created with previous info: {context.previous_contest_name}/{context.previous_problem_name}")
                
                # Get steps and execute them
                steps = context.get_steps()
                print(f"Found {len(steps)} steps")
                
                # This is where the allow_failure bug should manifest
                # The first copy step should fail but not stop execution
                
            except Exception as e:
                print(f"Real scenario test failed: {type(e).__name__}: {e}")
                raise