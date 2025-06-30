"""Unit tests for compatibility layer."""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src_check.models.check_result import CheckResult, LogLevel, FailureLocation
from src_check.models.kpi import KPIScore
from src_check.compatibility import LegacyCompatibilityWrapper, ResultConverter


class TestResultConverter:
    """Test cases for result converter."""
    
    def test_check_result_to_scorable_item(self):
        """Test converting CheckResult to ScorableItem."""
        converter = ResultConverter()
        
        result = CheckResult(
            title="Unused Import",
            log_level=LogLevel.WARNING,
            failure_locations=[FailureLocation("module.py", 5)],
            fix_policy="Remove unused import",
            fix_example_code=None
        )
        
        items = converter.check_result_to_scorable_item(result)
        
        assert len(items) == 1
        item = items[0]
        assert item.description == "Unused Import"
        assert item.file_path == "module.py"
        assert item.line_number == 5
        assert item.impact_points < 0  # Should be negative
    
    def test_kpi_score_to_text_format(self):
        """Test converting KPIScore to text format."""
        converter = ResultConverter()
        
        score = KPIScore(total_score=75.5)
        score.code_quality.issues_count = 5
        score.architecture_quality.issues_count = 2
        score.test_quality.issues_count = 1
        
        text = converter.kpi_score_to_text_format(score)
        
        assert "Total Score: 75.5/100" in text
        assert "Code Quality:" in text
        assert "Architecture Quality:" in text
        assert "Test Quality:" in text
        assert "5 issues" in text
    
    def test_kpi_score_to_json_format(self):
        """Test converting KPIScore to JSON format."""
        converter = ResultConverter()
        
        score = KPIScore(total_score=80.0)
        json_str = converter.kpi_score_to_json_format(score)
        
        import json
        data = json.loads(json_str)
        
        assert data["total_score"] == 80.0
        assert "categories" in data
        assert "metadata" in data


class TestLegacyCompatibilityWrapper:
    """Test cases for legacy compatibility wrapper."""
    
    def test_kpi_mode_detection_env_var(self):
        """Test KPI mode detection via environment variable."""
        with patch.dict(os.environ, {"SRC_CHECK_KPI_MODE": "true"}):
            wrapper = LegacyCompatibilityWrapper()
            assert wrapper.use_kpi is True
        
        with patch.dict(os.environ, {"SRC_CHECK_KPI_MODE": "false"}):
            wrapper = LegacyCompatibilityWrapper()
            assert wrapper.use_kpi is False
    
    def test_kpi_mode_detection_config_file(self):
        """Test KPI mode detection via config file."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            wrapper = LegacyCompatibilityWrapper()
            assert wrapper.use_kpi is True
    
    @patch("src_check.orchestrator.check_executor.CheckExecutor.execute")
    @patch("src_check.core.scoring.KPIScoreEngine.calculate_score")
    def test_execute_with_kpi_enabled(self, mock_calculate, mock_execute):
        """Test execution with KPI mode enabled."""
        # Setup mocks
        mock_results = [
            CheckResult(
                title="Test Issue",
                log_level=LogLevel.WARNING,
                failure_locations=[],
                fix_policy="Fix it",
                fix_example_code=None
            )
        ]
        mock_execute.return_value = mock_results
        
        mock_score = KPIScore(total_score=85.0)
        mock_calculate.return_value = mock_score
        
        # Test with KPI enabled
        with patch.dict(os.environ, {"SRC_CHECK_KPI_MODE": "true"}):
            wrapper = LegacyCompatibilityWrapper()
            results = wrapper.execute()
            
            assert results["legacy_results"] == mock_results
            assert results["kpi_score"] == mock_score
            mock_calculate.assert_called_once()
    
    @patch("src_check.orchestrator.check_executor.CheckExecutor.execute")
    def test_execute_with_kpi_disabled(self, mock_execute):
        """Test execution with KPI mode disabled."""
        mock_results = [
            CheckResult(
                title="Test Issue",
                log_level=LogLevel.WARNING,
                failure_locations=[],
                fix_policy="Fix it",
                fix_example_code=None
            )
        ]
        mock_execute.return_value = mock_results
        
        # Test with KPI disabled
        with patch.dict(os.environ, {"SRC_CHECK_KPI_MODE": "false"}):
            wrapper = LegacyCompatibilityWrapper()
            results = wrapper.execute()
            
            assert results["legacy_results"] == mock_results
            assert results["kpi_score"] is None
    
    def test_create_from_args(self):
        """Test creating wrapper from command line arguments."""
        args = {
            "kpi_config": None,
            "paths": ["/test/path"]
        }
        
        wrapper = LegacyCompatibilityWrapper.create_from_args(args)
        assert isinstance(wrapper, LegacyCompatibilityWrapper)
    
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", create=True)
    @patch("src_check.orchestrator.check_executor.CheckExecutor.execute")
    @patch("src_check.core.scoring.KPIScoreEngine.calculate_score")
    def test_write_kpi_results(self, mock_calculate, mock_execute, mock_open, mock_mkdir):
        """Test writing KPI results to files."""
        # Setup mocks
        mock_execute.return_value = []
        mock_score = KPIScore(total_score=90.0)
        mock_calculate.return_value = mock_score
        
        with patch.dict(os.environ, {
            "SRC_CHECK_KPI_MODE": "true",
            "SRC_CHECK_KPI_OUTPUT": "true"
        }):
            wrapper = LegacyCompatibilityWrapper()
            wrapper.execute()
            
            # Check that files were attempted to be written
            assert mock_open.call_count >= 2  # text and json files