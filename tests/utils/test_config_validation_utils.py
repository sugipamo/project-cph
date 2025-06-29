"""Tests for config validation utilities module."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.utils.config_validation_utils import get_steps_from_resolver


class TestConfigValidationUtils:
    """Test cases for config validation utilities."""

    def test_get_steps_from_resolver_success(self):
        """Test getting steps from resolver successfully."""
        # Create mock resolver
        resolver = Mock()
        
        # Create mock ConfigNodes for steps
        step1 = Mock()
        step1.key = 0
        step1.value = {"type": "shell", "cmd": ["echo", "step1"]}
        
        step2 = Mock()
        step2.key = 1
        step2.value = {"type": "shell", "cmd": ["echo", "step2"]}
        
        step3 = Mock()
        step3.key = 2
        step3.value = {"type": "shell", "cmd": ["echo", "step3"]}
        
        # Create mock steps node
        steps_node = Mock()
        steps_node.next_nodes = [step2, step1, step3]  # Intentionally out of order
        
        # Mock resolve_best to return steps_node
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.return_value = steps_node
            
            # Execute
            result = get_steps_from_resolver(resolver, "python", "run")
            
            # Verify
            assert len(result) == 3
            assert result[0] == step1  # Should be sorted by key
            assert result[1] == step2
            assert result[2] == step3
            mock_resolve.assert_called_once_with(
                resolver, 
                ["python", "commands", "run", "steps"]
            )

    def test_get_steps_from_resolver_no_steps_found(self):
        """Test getting steps when no steps are found."""
        # Create mock resolver
        resolver = Mock()
        
        # Mock resolve_best to return None
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.return_value = None
            
            # Execute and expect exception
            with pytest.raises(ValueError, match="stepsが見つかりません"):
                get_steps_from_resolver(resolver, "python", "test")

    def test_get_steps_from_resolver_empty_steps(self):
        """Test getting steps when steps node has no children."""
        # Create mock resolver
        resolver = Mock()
        
        # Create mock steps node with no children
        steps_node = Mock()
        steps_node.next_nodes = []
        
        # Mock resolve_best to return empty steps_node
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.return_value = steps_node
            
            # Execute
            result = get_steps_from_resolver(resolver, "cpp", "build")
            
            # Verify
            assert result == []

    def test_get_steps_from_resolver_mixed_keys(self):
        """Test getting steps with mixed key types (only integer keys should be included)."""
        # Create mock resolver
        resolver = Mock()
        
        # Create mock ConfigNodes with mixed keys
        step1 = Mock()
        step1.key = 0
        step1.value = {"type": "shell", "cmd": ["echo", "step1"]}
        
        step2 = Mock()
        step2.key = 1
        step2.value = {"type": "shell", "cmd": ["echo", "step2"]}
        
        non_step = Mock()
        non_step.key = "metadata"  # Non-integer key
        non_step.value = {"info": "not a step"}
        
        # Create mock steps node
        steps_node = Mock()
        steps_node.next_nodes = [step1, non_step, step2]
        
        # Mock resolve_best to return steps_node
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.return_value = steps_node
            
            # Execute
            result = get_steps_from_resolver(resolver, "rust", "run")
            
            # Verify - only integer-keyed nodes should be returned
            assert len(result) == 2
            assert result[0] == step1
            assert result[1] == step2

    def test_get_steps_from_resolver_exception_handling(self):
        """Test exception handling in get_steps_from_resolver."""
        # Create mock resolver
        resolver = Mock()
        
        # Mock resolve_best to raise an exception
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.side_effect = Exception("Resolver error")
            
            # Execute and expect wrapped exception
            with pytest.raises(ValueError, match="stepsの取得に失敗しました: Resolver error"):
                get_steps_from_resolver(resolver, "java", "compile")

    def test_get_steps_from_resolver_large_index_gap(self):
        """Test getting steps with large gaps in indices."""
        # Create mock resolver
        resolver = Mock()
        
        # Create mock ConfigNodes with gaps in indices
        step1 = Mock()
        step1.key = 0
        step1.value = {"type": "shell", "cmd": ["echo", "first"]}
        
        step2 = Mock()
        step2.key = 10  # Large gap
        step2.value = {"type": "shell", "cmd": ["echo", "second"]}
        
        step3 = Mock()
        step3.key = 5  # Between 0 and 10
        step3.value = {"type": "shell", "cmd": ["echo", "middle"]}
        
        # Create mock steps node
        steps_node = Mock()
        steps_node.next_nodes = [step2, step1, step3]
        
        # Mock resolve_best to return steps_node
        with patch('src.utils.config_validation_utils.resolve_best') as mock_resolve:
            mock_resolve.return_value = steps_node
            
            # Execute
            result = get_steps_from_resolver(resolver, "python", "debug")
            
            # Verify - should be sorted by key regardless of gaps
            assert len(result) == 3
            assert result[0] == step1  # key=0
            assert result[1] == step3  # key=5
            assert result[2] == step2  # key=10