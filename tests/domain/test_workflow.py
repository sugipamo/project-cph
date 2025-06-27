"""Tests for workflow module - core business logic"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestWorkflow:
    """Test suite for workflow generation and management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Import here to avoid import errors
        from src.domain.step import StepContext
        self.mock_context = StepContext(
            contest_name="ABC100",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            contest_temp_path="/contest/temp",
            source_file_name="main.py",
            language_id="py",
            file_patterns=[]
        )
        self.mock_operations = Mock()
        self.mock_composite_factory = Mock()
    
    @patch('src.domain.services.step_generation_service.generate_steps_from_json')
    def test_generate_workflow_from_json_success(self, mock_generate):
        """Test successful workflow generation from JSON"""
        from src.domain.workflow import generate_workflow_from_json
        
        # Mock successful step generation
        mock_result = Mock()
        mock_result.is_success = True
        mock_result.steps = [Mock(name="step1"), Mock(name="step2")]
        mock_result.errors = []
        mock_result.warnings = []
        mock_generate.return_value = mock_result
        
        # Mock composite request
        mock_composite = Mock()
        self.mock_composite_factory.return_value = mock_composite
        
        json_steps = [{"name": "step1"}, {"name": "step2"}]
        
        with patch('src.domain.workflow.validate_step_sequence', return_value=[]):
            with patch('src.domain.workflow.resolve_dependencies') as mock_resolve:
                mock_resolve.return_value = mock_result.steps
                with patch('src.domain.workflow.optimize_workflow_steps') as mock_optimize:
                    mock_optimize.return_value = mock_result.steps
                    with patch('src.domain.workflow.steps_to_requests') as mock_to_requests:
                        mock_to_requests.return_value = mock_composite
                        
                        result, errors, warnings = generate_workflow_from_json(
                            json_steps, 
                            self.mock_context, 
                            self.mock_operations,
                            self.mock_composite_factory
                        )
        
        assert result == mock_composite
        assert errors == []
        assert warnings == []
    
    @patch('src.domain.workflow.generate_steps_from_json')
    def test_generate_workflow_from_json_with_errors(self, mock_generate):
        """Test workflow generation with generation errors"""
        from src.domain.workflow import generate_workflow_from_json
        
        # Mock failed step generation
        mock_result = Mock()
        mock_result.is_success = False
        mock_result.errors = ["Error in step generation"]
        mock_result.warnings = ["Warning about step"]
        mock_generate.return_value = mock_result
        
        # Mock empty composite request
        mock_empty = Mock()
        self.mock_composite_factory.return_value = mock_empty
        
        json_steps = [{"name": "invalid_step"}]
        
        result, errors, warnings = generate_workflow_from_json(
            json_steps, 
            self.mock_context, 
            self.mock_operations,
            self.mock_composite_factory
        )
        
        assert result == mock_empty
        assert "Error in step generation" in errors
        assert "Warning about step" in warnings
    
    def test_optimize_workflow_steps(self):
        """Test workflow step optimization"""
        from src.domain.workflow import optimize_workflow_steps
        
        # Create mock steps
        mock_steps = [Mock(name="step1"), Mock(name="step2")]
        
        with patch('src.domain.workflow.optimize_step_sequence') as mock_seq:
            mock_seq.return_value = mock_steps
            with patch('src.domain.workflow.optimize_mkdir_steps') as mock_mkdir:
                mock_mkdir.return_value = mock_steps
                with patch('src.domain.workflow.optimize_copy_steps') as mock_copy:
                    mock_copy.return_value = mock_steps
                    
                    result = optimize_workflow_steps(mock_steps)
        
        assert result == mock_steps
        mock_seq.assert_called_once_with(mock_steps)
        mock_mkdir.assert_called_once_with(mock_steps)
        mock_copy.assert_called_once_with(mock_steps)
    
    def test_validate_workflow_execution_no_errors(self):
        """Test workflow execution validation with no errors"""
        from src.domain.workflow import validate_workflow_execution
        
        mock_composite = Mock()
        mock_composite.requests = [Mock(), Mock()]
        
        is_valid, validation_messages = validate_workflow_execution(
            mock_composite, [], []
        )
        
        assert is_valid is True
        assert len(validation_messages) == 1
        assert "Generated 2 executable requests" in validation_messages[0]
    
    def test_validate_workflow_execution_with_errors(self):
        """Test workflow execution validation with existing errors"""
        from src.domain.workflow import validate_workflow_execution
        
        mock_composite = Mock()
        mock_composite.requests = []
        
        is_valid, validation_messages = validate_workflow_execution(
            mock_composite, ["Previous error"], []
        )
        
        assert is_valid is False
        assert "Found 1 errors:" in validation_messages[0]
        assert "  - Previous error" in validation_messages[1]
    
    def test_steps_to_requests(self):
        """Test conversion of steps to requests"""
        from src.domain.workflow import steps_to_requests
        from src.domain.step import Step
        
        # Create mock steps
        mock_step1 = Mock(spec=Step)
        mock_step2 = Mock(spec=Step)
        steps = [mock_step1, mock_step2]
        
        # Mock request factory
        mock_factory = Mock()
        mock_request1 = Mock()
        mock_request2 = Mock()
        mock_factory.create_request_from_step.side_effect = [
            mock_request1, mock_request2
        ]
        
        self.mock_operations.get_request_factory.return_value = mock_factory
        
        # Mock composite request
        mock_composite = Mock()
        self.mock_composite_factory.return_value = mock_composite
        
        result = steps_to_requests(
            steps, 
            self.mock_context, 
            self.mock_operations,
            self.mock_composite_factory
        )
        
        assert result == mock_composite
        assert mock_factory.create_request_from_step.call_count == 2
        self.mock_composite_factory.assert_called_once_with(
            [mock_request1, mock_request2],
            debug_tag='workflow',
            name=None,
            execution_controller=None
        )
    
    def test_create_step_context_from_env_context(self):
        """Test creating StepContext from environment context"""
        from src.domain.workflow import create_step_context_from_env_context
        
        # Create mock env context with all attributes
        mock_env = Mock()
        mock_env.contest_name = "ABC200"
        mock_env.problem_name = "B"
        mock_env.language = "python"
        mock_env.env_type = "docker"
        mock_env.command_type = "test"
        mock_env.local_workspace_path = "/local/workspace"
        mock_env.contest_current_path = "/contest/current"
        mock_env.contest_stock_path = "/contest/stock"
        mock_env.contest_template_path = "/contest/template"
        mock_env.contest_temp_path = "/contest/temp"
        mock_env.source_file_name = "solution.py"
        mock_env.language_id = "py"
        mock_env.file_patterns = ["*.py", "*.txt"]
        
        result = create_step_context_from_env_context(mock_env)
        
        assert result.contest_name == "ABC200"
        assert result.problem_name == "B"
        assert result.language == "python"
        assert result.env_type == "docker"
        assert result.command_type == "test"
        assert result.local_workspace_path == "/local/workspace"