"""ビルダーバリデーション

グラフとワークフローの検証機能のメインエントリーポイント
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# 新しいバリデーションモジュールからインポート
from .validation.structural_validator import validate_graph_structure
from .validation.feasibility_checker import validate_execution_feasibility  
from .validation.connectivity_analyzer import check_graph_connectivity


@dataclass(frozen=True)
class ValidationResult:
    """検証結果を表現する不変データ構造"""
    is_valid: bool
    errors: List[str]
    warnings: List[str] 
    suggestions: List[str]
    statistics: Dict[str, Any]
    
    @classmethod
    def success(cls, warnings: List[str] = None, suggestions: List[str] = None, 
                statistics: Dict[str, Any] = None) -> 'ValidationResult':
        """成功結果を作成"""
        return cls(
            is_valid=True,
            errors=[],
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )
    
    @classmethod
    def failure(cls, errors: List[str], warnings: List[str] = None, 
                suggestions: List[str] = None, statistics: Dict[str, Any] = None) -> 'ValidationResult':
        """失敗結果を作成"""
        return cls(
            is_valid=False,
            errors=errors,
            warnings=warnings or [],
            suggestions=suggestions or [],
            statistics=statistics or {}
        )


def create_validation_report(validation_results: List[ValidationResult]) -> str:
    """複数の検証結果からレポートを生成する純粋関数
    
    Args:
        validation_results: 検証結果のリスト
        
    Returns:
        検証レポート文字列
    """
    if not validation_results:
        return "No validation results provided"
    
    report_lines = ["=== Validation Report ==="]
    
    total_errors = 0
    total_warnings = 0
    
    for i, result in enumerate(validation_results):
        report_lines.append(f"\n--- Validation {i+1} ---")
        report_lines.append(f"Status: {'PASS' if result.is_valid else 'FAIL'}")
        
        if result.errors:
            total_errors += len(result.errors)
            report_lines.append("Errors:")
            for error in result.errors:
                report_lines.append(f"  - {error}")
        
        if result.warnings:
            total_warnings += len(result.warnings)
            report_lines.append("Warnings:")
            for warning in result.warnings:
                report_lines.append(f"  - {warning}")
        
        if result.suggestions:
            report_lines.append("Suggestions:")
            for suggestion in result.suggestions:
                report_lines.append(f"  - {suggestion}")
        
        if result.statistics:
            report_lines.append("Statistics:")
            for key, value in result.statistics.items():
                report_lines.append(f"  {key}: {value}")
    
    # サマリー
    report_lines.append(f"\n=== Summary ===")
    report_lines.append(f"Total validations: {len(validation_results)}")
    report_lines.append(f"Passed: {sum(1 for r in validation_results if r.is_valid)}")
    report_lines.append(f"Failed: {sum(1 for r in validation_results if not r.is_valid)}")
    report_lines.append(f"Total errors: {total_errors}")
    report_lines.append(f"Total warnings: {total_warnings}")
    
    return "\n".join(report_lines)


# 後方互換性のため、メインの関数群を再エクスポート
__all__ = [
    'ValidationResult',
    'validate_graph_structure',
    'validate_execution_feasibility',
    'check_graph_connectivity',
    'create_validation_report'
]