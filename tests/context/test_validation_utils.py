import pytest
from src.context.utils.validation_utils import validate_execution_context_data, get_steps_from_resolver


def test_validate_execution_context_data_success():
    """Test successful validation"""
    result, error = validate_execution_context_data(
        command_type="test",
        language="python",
        contest_name="abc123",
        problem_name="a",
        env_json={"python": {"some": "config"}}
    )
    assert result is True
    assert error is None


def test_validate_execution_context_data_missing_command_type():
    """Test validation with missing command_type"""
    result, error = validate_execution_context_data(
        command_type="",
        language="python",
        contest_name="abc123",
        problem_name="a",
        env_json={"python": {"some": "config"}}
    )
    assert result is False
    assert "コマンド" in error


def test_validate_execution_context_data_missing_language():
    """Test validation with missing language"""
    result, error = validate_execution_context_data(
        command_type="test",
        language="",
        contest_name="abc123",
        problem_name="a",
        env_json={"python": {"some": "config"}}
    )
    assert result is False
    assert "言語" in error


def test_validate_execution_context_data_missing_multiple_fields():
    """Test validation with multiple missing fields"""
    result, error = validate_execution_context_data(
        command_type="",
        language="",
        contest_name="abc123",
        problem_name="a",
        env_json={"python": {"some": "config"}}
    )
    assert result is False
    assert "コマンド" in error
    assert "言語" in error


def test_validate_execution_context_data_empty_env_json():
    """Test validation with empty env_json"""
    result, error = validate_execution_context_data(
        command_type="test",
        language="python",
        contest_name="abc123",
        problem_name="a",
        env_json={}
    )
    assert result is False
    assert "環境設定ファイル" in error


def test_validate_execution_context_data_language_not_in_env():
    """Test validation when language is not in env_json"""
    result, error = validate_execution_context_data(
        command_type="test",
        language="cpp",
        contest_name="abc123",
        problem_name="a",
        env_json={"python": {"some": "config"}}
    )
    assert result is False
    assert "cpp" in error
    assert "環境設定ファイルに存在しません" in error


def test_get_steps_from_resolver_success():
    """Test successful steps retrieval"""
    # Mock resolver and related imports
    from unittest.mock import Mock
    from src.context.resolver.config_node import ConfigNode
    
    # Create mock steps
    step1 = ConfigNode(key=0, value={"type": "shell", "cmd": ["echo", "test1"]})
    step2 = ConfigNode(key=1, value={"type": "shell", "cmd": ["echo", "test2"]})
    steps_node = ConfigNode(key="steps", value=None)
    steps_node.next_nodes = [step1, step2]
    
    # Mock resolve_best function
    import src.context.utils.validation_utils as module
    original_resolve = module.resolve_best if hasattr(module, 'resolve_best') else None
    
    def mock_resolve_best(resolver, path):
        if path == ["python", "commands", "test", "steps"]:
            return steps_node
        return None
    
    # Replace the import
    import src.context.resolver.config_resolver as config_module
    original_resolve_best = config_module.resolve_best
    config_module.resolve_best = mock_resolve_best
    
    try:
        mock_resolver = Mock()
        result = get_steps_from_resolver(mock_resolver, "python", "test")
        
        assert len(result) == 2
        assert result[0].key == 0
        assert result[1].key == 1
    finally:
        # Restore original function
        config_module.resolve_best = original_resolve_best


def test_get_steps_from_resolver_no_steps():
    """Test steps retrieval when steps are not found"""
    from unittest.mock import Mock
    
    # Mock resolve_best to return None
    import src.context.resolver.config_resolver as config_module
    original_resolve_best = config_module.resolve_best
    
    def mock_resolve_best(resolver, path):
        return None
    
    config_module.resolve_best = mock_resolve_best
    
    try:
        mock_resolver = Mock()
        
        with pytest.raises(ValueError) as excinfo:
            get_steps_from_resolver(mock_resolver, "python", "test")
        assert "stepsが見つかりません" in str(excinfo.value)
    finally:
        # Restore original function
        config_module.resolve_best = original_resolve_best