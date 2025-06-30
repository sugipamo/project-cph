"""Unit tests for KPI scoring engine."""

import pytest
from datetime import datetime

from src_check.models.check_result import CheckResult, LogLevel, FailureLocation
from src_check.models.kpi import KPIScore, KPIConfig, ScorableItem
from src_check.models.kpi.kpi_score import KPICategory, Severity
from src_check.core.scoring import KPIScoreEngine


class TestKPIScoreEngine:
    """Test cases for KPI scoring engine."""
    
    def test_base_score_calculation(self):
        """Test that base score is correctly initialized."""
        engine = KPIScoreEngine()
        assert engine.config.base_score == 50.0
        
        # Test with custom config
        config = KPIConfig(base_score=60.0)
        engine = KPIScoreEngine(config)
        assert engine.config.base_score == 60.0
    
    def test_empty_results_score(self):
        """Test scoring with no issues (should return base score)."""
        engine = KPIScoreEngine()
        score = engine.calculate_score([])
        
        assert score.total_score == 50.0
        assert score.code_quality.raw_score == 50.0
        assert score.architecture_quality.raw_score == 50.0
        assert score.test_quality.raw_score == 50.0
        assert score.total_issues == 0
    
    def test_single_error_deduction(self):
        """Test that a single error properly deducts points."""
        engine = KPIScoreEngine()
        
        # Create a check result with an error
        result = CheckResult(
            title="Syntax Error",
            log_level=LogLevel.ERROR,
            failure_locations=[FailureLocation("test.py", 10)],
            fix_policy="Fix the syntax error",
            fix_example_code=None
        )
        
        score = engine.calculate_score([result])
        
        # Score should be less than base score
        assert score.total_score < 50.0
        assert score.total_issues == 1
        assert score.files_analyzed == 1
    
    def test_category_classification(self):
        """Test that issues are correctly classified into categories."""
        engine = KPIScoreEngine()
        
        # Architecture issue
        arch_result = CheckResult(
            title="Circular Import Detected",
            log_level=LogLevel.ERROR,
            failure_locations=[FailureLocation("module.py", 1)],
            fix_policy="Remove circular dependency",
            fix_example_code=None
        )
        
        # Test issue
        test_result = CheckResult(
            title="Low Test Coverage",
            log_level=LogLevel.WARNING,
            failure_locations=[FailureLocation("tests/test_module.py", 1)],
            fix_policy="Add more tests",
            fix_example_code=None
        )
        
        # Code quality issue (default)
        code_result = CheckResult(
            title="Unused Variable",
            log_level=LogLevel.WARNING,
            failure_locations=[FailureLocation("main.py", 50)],
            fix_policy="Remove unused variable",
            fix_example_code=None
        )
        
        score = engine.calculate_score([arch_result, test_result, code_result])
        
        assert score.architecture_quality.issues_count >= 1
        assert score.test_quality.issues_count >= 1
        assert score.code_quality.issues_count >= 1
    
    @pytest.mark.parametrize("log_level,expected_severity", [
        (LogLevel.DEBUG, Severity.INFO),
        (LogLevel.INFO, Severity.LOW),
        (LogLevel.WARNING, Severity.MEDIUM),
        (LogLevel.ERROR, Severity.HIGH),
        (LogLevel.CRITICAL, Severity.CRITICAL),
    ])
    def test_log_level_to_severity_mapping(self, log_level, expected_severity):
        """Test log level to severity conversion."""
        engine = KPIScoreEngine()
        severity = engine._log_level_to_severity(log_level)
        assert severity == expected_severity
    
    def test_score_bounds(self):
        """Test that scores stay within valid bounds (0-100)."""
        engine = KPIScoreEngine()
        
        # Create many critical errors
        results = []
        for i in range(20):
            result = CheckResult(
                title=f"Critical Error {i}",
                log_level=LogLevel.CRITICAL,
                failure_locations=[FailureLocation(f"file{i}.py", i)],
                fix_policy="Fix critical error",
                fix_example_code=None
            )
            results.append(result)
        
        score = engine.calculate_score(results)
        
        # Score should not go below 0
        assert score.total_score >= 0
        assert score.code_quality.raw_score >= 0
        
        # Score should not exceed 100
        assert score.total_score <= 100
    
    def test_weighted_scores(self):
        """Test that category weights are correctly applied."""
        config = KPIConfig(
            weights={
                "code_quality": 0.5,
                "architecture_quality": 0.3,
                "test_quality": 0.2
            }
        )
        engine = KPIScoreEngine(config)
        
        score = engine.calculate_score([])
        
        # Check weighted scores match raw score * weight
        assert abs(score.code_quality.weighted_score - (50.0 * 0.5)) < 0.01
        assert abs(score.architecture_quality.weighted_score - (50.0 * 0.3)) < 0.01
        assert abs(score.test_quality.weighted_score - (50.0 * 0.2)) < 0.01
        
        # Total should equal sum of weighted scores
        expected_total = (50.0 * 0.5) + (50.0 * 0.3) + (50.0 * 0.2)
        assert abs(score.total_score - expected_total) < 0.01
    
    def test_multiple_failures_same_file(self):
        """Test handling multiple failures in the same file."""
        engine = KPIScoreEngine()
        
        result = CheckResult(
            title="Multiple Issues",
            log_level=LogLevel.WARNING,
            failure_locations=[
                FailureLocation("problem.py", 10),
                FailureLocation("problem.py", 20),
                FailureLocation("problem.py", 30),
            ],
            fix_policy="Fix all issues",
            fix_example_code=None
        )
        
        score = engine.calculate_score([result])
        
        # Should count as 1 file but multiple issues
        assert score.files_analyzed == 1
        assert score.total_issues >= 3
    
    def test_execution_time_tracking(self):
        """Test that execution time is tracked."""
        engine = KPIScoreEngine()
        
        score = engine.calculate_score([])
        
        assert score.execution_time > 0
        assert isinstance(score.execution_time, float)
    
    def test_kpi_score_to_dict(self):
        """Test KPIScore serialization to dictionary."""
        score = KPIScore(
            total_score=75.5,
            project_path="/test/project"
        )
        
        score_dict = score.to_dict()
        
        assert score_dict["total_score"] == 75.5
        assert score_dict["project_path"] == "/test/project"
        assert "categories" in score_dict
        assert "metadata" in score_dict
        assert isinstance(score_dict["timestamp"], str)