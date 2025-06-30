"""Maps check rules to KPI categories and severities."""

from typing import Dict, Tuple
from src_check.models.kpi.kpi_score import KPICategory, Severity


class CheckResultToKPIMapper:
    """Maps check results to KPI categories and severities."""
    
    # Rule mapping: rule_name -> (category, base_severity)
    RULE_MAPPINGS: Dict[str, Tuple[KPICategory, Severity]] = {
        # Code Quality Rules
        "args_checker": (KPICategory.CODE_QUALITY, Severity.MEDIUM),
        "kwargs_checker": (KPICategory.CODE_QUALITY, Severity.MEDIUM),
        "naming_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        "print_statement_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        "syntax_checker": (KPICategory.CODE_QUALITY, Severity.HIGH),
        "type_checker": (KPICategory.CODE_QUALITY, Severity.MEDIUM),
        "unused_variable_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        "duplicated_code_checker": (KPICategory.CODE_QUALITY, Severity.MEDIUM),
        "complexity_checker": (KPICategory.CODE_QUALITY, Severity.MEDIUM),
        "file_size_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        "line_length_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        "docstring_checker": (KPICategory.CODE_QUALITY, Severity.LOW),
        
        # Architecture Quality Rules
        "circular_import_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.CRITICAL),
        "dependency_injection_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.HIGH),
        "clean_architecture_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.HIGH),
        "import_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.MEDIUM),
        "unused_import_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.LOW),
        "broken_imports_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.CRITICAL),
        "module_structure_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.MEDIUM),
        "layered_architecture_checker": (KPICategory.ARCHITECTURE_QUALITY, Severity.HIGH),
        
        # Test Quality Rules
        "test_coverage_checker": (KPICategory.TEST_QUALITY, Severity.HIGH),
        "test_naming_checker": (KPICategory.TEST_QUALITY, Severity.LOW),
        "mock_usage_checker": (KPICategory.TEST_QUALITY, Severity.MEDIUM),
        "assertion_checker": (KPICategory.TEST_QUALITY, Severity.MEDIUM),
        "testability_checker": (KPICategory.TEST_QUALITY, Severity.HIGH),
        "fixture_checker": (KPICategory.TEST_QUALITY, Severity.LOW),
        
        # Security Quality Rules
        "hardcoded_secrets_checker": (KPICategory.SECURITY_QUALITY, Severity.CRITICAL),
        "sql_injection_checker": (KPICategory.SECURITY_QUALITY, Severity.CRITICAL),
        "unsafe_eval_checker": (KPICategory.SECURITY_QUALITY, Severity.HIGH),
        "weak_random_checker": (KPICategory.SECURITY_QUALITY, Severity.HIGH),
        "insecure_hash_checker": (KPICategory.SECURITY_QUALITY, Severity.MEDIUM),
        "input_validation_checker": (KPICategory.SECURITY_QUALITY, Severity.HIGH),
        "shell_injection_checker": (KPICategory.SECURITY_QUALITY, Severity.CRITICAL),
        "path_traversal_checker": (KPICategory.SECURITY_QUALITY, Severity.HIGH),
        "insecure_transport_checker": (KPICategory.SECURITY_QUALITY, Severity.MEDIUM),
    }
    
    @classmethod
    def get_category_and_severity(cls, rule_name: str) -> Tuple[KPICategory, Severity]:
        """
        Get the KPI category and base severity for a rule.
        
        Args:
            rule_name: Name of the check rule
            
        Returns:
            Tuple of (category, severity)
        """
        return cls.RULE_MAPPINGS.get(
            rule_name, 
            (KPICategory.CODE_QUALITY, Severity.MEDIUM)  # Default
        )
    
    @classmethod
    def adjust_severity_by_context(cls, 
                                  base_severity: Severity, 
                                  error_count: int,
                                  is_critical_path: bool = False) -> Severity:
        """
        Adjust severity based on context.
        
        Args:
            base_severity: Base severity from rule mapping
            error_count: Number of errors found
            is_critical_path: Whether the error is in a critical path
            
        Returns:
            Adjusted severity
        """
        severity_order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, 
                         Severity.HIGH, Severity.CRITICAL]
        current_index = severity_order.index(base_severity)
        
        # Increase severity for multiple errors
        if error_count > 10:
            current_index = min(current_index + 1, len(severity_order) - 1)
        
        # Increase severity for critical paths
        if is_critical_path:
            current_index = min(current_index + 1, len(severity_order) - 1)
        
        return severity_order[current_index]