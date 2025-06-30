"""KPI scoring engine implementation."""

import time
from typing import List, Dict, Optional
from pathlib import Path

from src_check.models.kpi import KPIScore, CategoryScore, ScorableItem, KPIConfig
from src_check.models.kpi.kpi_score import KPICategory, Severity
from src_check.models.check_result import CheckResult


class KPIScoreEngine:
    """Engine for calculating KPI scores from check results."""
    
    def __init__(self, config: Optional[KPIConfig] = None):
        """Initialize the scoring engine."""
        self.config = config or KPIConfig()
        self.config.validate()
        
    def calculate_score(self, 
                       check_results: List[CheckResult], 
                       project_path: Optional[str] = None) -> KPIScore:
        """
        Calculate KPI score from check results.
        
        Args:
            check_results: List of check results to score
            project_path: Path to the project being analyzed
            
        Returns:
            KPIScore object with calculated scores
        """
        start_time = time.time()
        
        # Initialize score with base values
        kpi_score = KPIScore(
            total_score=self.config.base_score,
            project_path=project_path or ""
        )
        
        # Initialize category scores with base values
        for category in KPICategory:
            category_score = CategoryScore(
                category=category,
                raw_score=self.config.base_score,
                weighted_score=self.config.base_score * self.config.weights[category.value],
                issues_count=0
            )
            
            if category == KPICategory.CODE_QUALITY:
                kpi_score.code_quality = category_score
            elif category == KPICategory.ARCHITECTURE_QUALITY:
                kpi_score.architecture_quality = category_score
            elif category == KPICategory.TEST_QUALITY:
                kpi_score.test_quality = category_score
            elif category == KPICategory.SECURITY_QUALITY:
                kpi_score.security_quality = category_score
        
        # Process each check result
        files_seen = set()
        for result in check_results:
            # Track files analyzed
            for location in result.failure_locations:
                files_seen.add(location.file_path)
            
            # Convert to scorable items
            scorable_items = self._convert_to_scorable_items(result)
            
            # Apply scores to appropriate categories
            for item in scorable_items:
                self._apply_score_impact(kpi_score, item)
        
        # Update metadata
        kpi_score.files_analyzed = len(files_seen)
        kpi_score.execution_time = time.time() - start_time
        
        # Recalculate final scores
        self._finalize_scores(kpi_score)
        
        return kpi_score
    
    def _convert_to_scorable_items(self, result: CheckResult) -> List[ScorableItem]:
        """Convert a CheckResult to scorable items."""
        items = []
        
        # Determine category and severity from result
        category = self._determine_category(result)
        severity = self._log_level_to_severity(result.log_level)
        impact = self.config.severity_impacts.get(severity.value, -1.0)
        
        # Create a scorable item for each failure location
        if result.failure_locations:
            for location in result.failure_locations:
                item = ScorableItem(
                    category=category,
                    severity=severity,
                    impact_points=impact,
                    description=result.title,
                    file_path=location.file_path,
                    line_number=location.line,
                    rule_id=getattr(result, 'rule_id', None)
                )
                items.append(item)
        else:
            # Create a general item if no specific locations
            item = ScorableItem(
                category=category,
                severity=severity,
                impact_points=impact,
                description=result.title,
                rule_id=getattr(result, 'rule_id', None)
            )
            items.append(item)
        
        return items
    
    def _determine_category(self, result: CheckResult) -> KPICategory:
        """Determine the KPI category for a check result."""
        title_lower = result.title.lower()
        
        # Security quality indicators
        security_keywords = [
            'password', 'secret', 'key', 'token', 'hardcoded', 'security',
            'injection', 'xss', 'csrf', 'vulnerability', 'unsafe', 'insecure',
            'encrypt', 'decrypt', 'hash', 'random', 'weak', 'ssl', 'tls',
            'eval', 'exec', 'input', 'sql', 'shell', 'command'
        ]
        
        # Architecture quality indicators
        architecture_keywords = [
            'circular', 'dependency', 'architecture', 'layer', 'coupling',
            'cohesion', 'module', 'package', 'structure'
        ]
        
        # Test quality indicators
        test_keywords = [
            'test', 'coverage', 'mock', 'assertion', 'fixture',
            'unittest', 'pytest', 'testable'
        ]
        
        # Check for security issues (highest priority)
        if any(keyword in title_lower for keyword in security_keywords):
            return KPICategory.SECURITY_QUALITY
        
        # Check for architecture issues
        if any(keyword in title_lower for keyword in architecture_keywords):
            return KPICategory.ARCHITECTURE_QUALITY
        
        # Check for test issues
        if any(keyword in title_lower for keyword in test_keywords):
            return KPICategory.TEST_QUALITY
        
        # Default to code quality
        return KPICategory.CODE_QUALITY
    
    def _log_level_to_severity(self, log_level) -> Severity:
        """Convert LogLevel to Severity."""
        # Map based on the LogLevel enum from check_result
        level_map = {
            "DEBUG": Severity.INFO,
            "INFO": Severity.LOW,
            "WARNING": Severity.MEDIUM,
            "ERROR": Severity.HIGH,
            "CRITICAL": Severity.CRITICAL
        }
        
        # Get the string representation of log level
        level_str = str(log_level).split('.')[-1] if hasattr(log_level, 'name') else str(log_level)
        
        return level_map.get(level_str, Severity.MEDIUM)
    
    def _apply_score_impact(self, kpi_score: KPIScore, item: ScorableItem):
        """Apply the score impact of an item to the appropriate category."""
        category_scores = kpi_score.get_category_scores()
        category_score = category_scores.get(item.category)
        
        if category_score:
            # Add the issue
            category_score.add_issue(item)
            
            # Apply the score impact
            impact = item.get_score_impact()
            category_score.raw_score = max(0, category_score.raw_score + impact)
    
    def _finalize_scores(self, kpi_score: KPIScore):
        """Finalize scores by applying weights and bounds."""
        # Apply weights to each category
        for category, score in kpi_score.get_category_scores().items():
            weight = self.config.weights[category.value]
            score.weighted_score = score.raw_score * weight
            
            # Ensure scores are within bounds
            score.raw_score = max(0, min(100, score.raw_score))
            score.weighted_score = max(0, min(100 * weight, score.weighted_score))
        
        # Update total score
        kpi_score.update_total_score()
        
        # Ensure total score is within bounds
        kpi_score.total_score = max(0, min(100, kpi_score.total_score))