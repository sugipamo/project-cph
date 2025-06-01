"""
Simple integration test for main.py to verify basic functionality
"""
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os
import json

from src.main import main
from src.context.execution_context import ExecutionContext


class TestSimpleMainIntegration:
    """Simple integration test for main.py"""
    
    def test_main_with_mock_operations(self, tmp_path):
        """Test main() with fully mocked operations"""
        # Create a simple test workflow
        test_env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [
                            {
                                "type": "touch",
                                "cmd": [str(tmp_path / "test.txt")]
                            }
                        ]
                    }
                }
            }
        }
        
        # Create mock context
        mock_context = MagicMock()
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.contest_name = "test"
        mock_context.problem_name = "a"
        mock_context.env_type = "local"
        mock_context.env_json = test_env_json
        mock_context.get_docker_names.return_value = {
            "image_name": "test",
            "container_name": "test",
            "oj_image_name": "test",
            "oj_container_name": "test"
        }
        mock_context.to_format_dict.return_value = {
            "workspace_path": str(tmp_path),
            "contest_current_path": str(tmp_path)
        }
        
        # Mock dockerfile resolver
        mock_context.dockerfile_resolver = MagicMock()
        mock_context.dockerfile_resolver.dockerfile = None
        
        # Create mock operations that uses dummy drivers
        from src.operations.mock.dummy_file_driver import DummyFileDriver
        mock_operations = MagicMock()
        mock_operations.resolve.return_value = DummyFileDriver()
        
        # Execute main
        result = main(mock_context, mock_operations)
        
        # Verify result
        assert result is not None
        assert result.success is True
        # Should have 2 results: mkdir (from fitting) and touch (from workflow)
        assert len(result.results) == 2
        assert all(r.success for r in result.results)
    
    def test_main_execution_flow(self, capsys):
        """Test the execution flow of main()"""
        # Create minimal context
        mock_context = MagicMock()
        mock_context.command_type = "test"
        mock_context.language = "python"
        mock_context.env_json = {
            "python": {
                "commands": {
                    "test": {
                        "steps": []  # Empty workflow
                    }
                }
            }
        }
        
        # Create mock operations
        mock_operations = MagicMock()
        
        # Test that empty workflow is handled
        with pytest.raises(Exception) as exc_info:
            main(mock_context, mock_operations)
        
        assert "ワークフロー実行に失敗しました" in str(exc_info.value)
        
        # Check output
        captured = capsys.readouterr()
        assert "No workflow steps found" in captured.out