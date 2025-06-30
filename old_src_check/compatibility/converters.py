"""Converters for compatibility between legacy and KPI systems."""

from typing import List, Optional
import json

from src_check.models.check_result import CheckResult, LogLevel, FailureLocation
from src_check.models.kpi import KPIScore, ScorableItem
from src_check.models.kpi.kpi_score import Severity
from src_check.core.scoring.rule_mapper import CheckResultToKPIMapper


class ResultConverter:
    """Convert between CheckResult and KPI formats."""
    
    @staticmethod
    def check_result_to_scorable_item(result: CheckResult) -> List[ScorableItem]:
        """
        Convert a CheckResult to ScorableItems.
        
        Args:
            result: CheckResult to convert
            
        Returns:
            List of ScorableItems
        """
        # Get category and severity from rule mapper
        rule_name = getattr(result, 'rule_name', 'unknown')
        category, base_severity = CheckResultToKPIMapper.get_category_and_severity(rule_name)
        
        # Adjust severity based on log level
        severity = ResultConverter._adjust_severity_by_log_level(base_severity, result.log_level)
        
        # Calculate impact points
        impact_points = ResultConverter._calculate_impact_points(severity)
        
        # Create scorable items
        items = []
        if result.failure_locations:
            for location in result.failure_locations:
                item = ScorableItem(
                    category=category,
                    severity=severity,
                    impact_points=impact_points,
                    description=result.title,
                    file_path=location.file_path,
                    line_number=location.line,
                    rule_id=rule_name
                )
                items.append(item)
        else:
            # Create a general item if no specific locations
            item = ScorableItem(
                category=category,
                severity=severity,
                impact_points=impact_points,
                description=result.title,
                rule_id=rule_name
            )
            items.append(item)
        
        return items
    
    @staticmethod
    def kpi_score_to_text_format(kpi_score: KPIScore) -> str:
        """
        Convert KPIScore to legacy text format.
        
        Args:
            kpi_score: KPIScore to convert
            
        Returns:
            Text representation similar to legacy format
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"KPI Score Report - Total Score: {kpi_score.total_score:.1f}/100")
        lines.append("=" * 80)
        lines.append("")
        
        # Category breakdown
        lines.append("Category Breakdown:")
        lines.append(f"  Code Quality:         {kpi_score.code_quality.weighted_score:.1f} "
                    f"({kpi_score.code_quality.issues_count} issues)")
        lines.append(f"  Architecture Quality: {kpi_score.architecture_quality.weighted_score:.1f} "
                    f"({kpi_score.architecture_quality.issues_count} issues)")
        lines.append(f"  Test Quality:         {kpi_score.test_quality.weighted_score:.1f} "
                    f"({kpi_score.test_quality.issues_count} issues)")
        lines.append("")
        
        # Issue summary
        lines.append("Issue Summary:")
        total_critical = (kpi_score.code_quality.critical_issues + 
                         kpi_score.architecture_quality.critical_issues +
                         kpi_score.test_quality.critical_issues)
        total_high = (kpi_score.code_quality.high_issues + 
                     kpi_score.architecture_quality.high_issues +
                     kpi_score.test_quality.high_issues)
        total_medium = (kpi_score.code_quality.medium_issues + 
                       kpi_score.architecture_quality.medium_issues +
                       kpi_score.test_quality.medium_issues)
        total_low = (kpi_score.code_quality.low_issues + 
                    kpi_score.architecture_quality.low_issues +
                    kpi_score.test_quality.low_issues)
        
        lines.append(f"  Critical: {total_critical}")
        lines.append(f"  High:     {total_high}")
        lines.append(f"  Medium:   {total_medium}")
        lines.append(f"  Low:      {total_low}")
        lines.append("")
        
        # Metadata
        lines.append("Metadata:")
        lines.append(f"  Files Analyzed:  {kpi_score.files_analyzed}")
        lines.append(f"  Execution Time:  {kpi_score.execution_time:.2f}s")
        lines.append(f"  Total Issues:    {kpi_score.total_issues}")
        
        return "\n".join(lines)
    
    @staticmethod
    def kpi_score_to_json_format(kpi_score: KPIScore) -> str:
        """
        Convert KPIScore to JSON format.
        
        Args:
            kpi_score: KPIScore to convert
            
        Returns:
            JSON representation
        """
        return json.dumps(kpi_score.to_dict(), indent=2)
    
    @staticmethod
    def _adjust_severity_by_log_level(base_severity: Severity, log_level: LogLevel) -> Severity:
        """Adjust severity based on log level."""
        # If log level is CRITICAL or ERROR, upgrade severity
        if log_level == LogLevel.CRITICAL:
            return Severity.CRITICAL
        elif log_level == LogLevel.ERROR and base_severity in [Severity.LOW, Severity.MEDIUM]:
            return Severity.HIGH
        
        return base_severity
    
    @staticmethod
    def _calculate_impact_points(severity: Severity) -> float:
        """Calculate impact points based on severity."""
        impact_map = {
            Severity.CRITICAL: -10.0,
            Severity.HIGH: -5.0,
            Severity.MEDIUM: -3.0,
            Severity.LOW: -1.0,
            Severity.INFO: -0.5
        }
        return impact_map.get(severity, -1.0)