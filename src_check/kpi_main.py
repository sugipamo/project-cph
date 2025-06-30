#!/usr/bin/env python3
"""
KPI-focused entry point for src_check.
This is the new entry point that prioritizes KPI scoring.
"""

import sys
import argparse
from pathlib import Path
import json
import yaml

# Add src_check to path
sys.path.append(str(Path(__file__).parent))

from orchestrator.check_executor import CheckExecutor
from core.scoring import KPIScoreEngine
from models.kpi import KPIConfig
from compatibility.converters import ResultConverter
from core.database import DatabaseManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="src_check KPI - Code quality scoring system"
    )
    
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to analyze (default: current directory)"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="KPI configuration file path"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show score history"
    )
    
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Save score to history database"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        help="Fail if score is below threshold"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    return parser.parse_args()


def load_config(config_path: str = None) -> KPIConfig:
    """Load KPI configuration."""
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            if config_path.endswith(".json"):
                config_data = json.load(f)
            else:
                config_data = yaml.safe_load(f)
            return KPIConfig.from_dict(config_data)
    
    # Check for default config files
    for config_file in [".src_check_kpi.yaml", ".src_check_kpi.json", "src_check_kpi.yaml"]:
        if Path(config_file).exists():
            return load_config(config_file)
    
    # Return default config
    return KPIConfig()


def format_output(kpi_score, format_type: str) -> str:
    """Format KPI score for output."""
    converter = ResultConverter()
    
    if format_type == "json":
        return converter.kpi_score_to_json_format(kpi_score)
    elif format_type == "markdown":
        return format_markdown_output(kpi_score)
    else:
        return converter.kpi_score_to_text_format(kpi_score)


def format_markdown_output(kpi_score) -> str:
    """Format KPI score as markdown."""
    lines = []
    lines.append("# KPI Score Report")
    lines.append("")
    lines.append(f"**Total Score**: {kpi_score.total_score:.1f}/100")
    lines.append("")
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Score | Issues |")
    lines.append("|----------|-------|--------|")
    lines.append(f"| Code Quality | {kpi_score.code_quality.weighted_score:.1f} | {kpi_score.code_quality.issues_count} |")
    lines.append(f"| Architecture Quality | {kpi_score.architecture_quality.weighted_score:.1f} | {kpi_score.architecture_quality.issues_count} |")
    lines.append(f"| Test Quality | {kpi_score.test_quality.weighted_score:.1f} | {kpi_score.test_quality.issues_count} |")
    lines.append("")
    lines.append("## Issue Summary")
    lines.append("")
    lines.append(f"- **Critical**: {kpi_score.code_quality.critical_issues + kpi_score.architecture_quality.critical_issues + kpi_score.test_quality.critical_issues}")
    lines.append(f"- **High**: {kpi_score.code_quality.high_issues + kpi_score.architecture_quality.high_issues + kpi_score.test_quality.high_issues}")
    lines.append(f"- **Medium**: {kpi_score.code_quality.medium_issues + kpi_score.architecture_quality.medium_issues + kpi_score.test_quality.medium_issues}")
    lines.append(f"- **Low**: {kpi_score.code_quality.low_issues + kpi_score.architecture_quality.low_issues + kpi_score.test_quality.low_issues}")
    
    return "\n".join(lines)


def main():
    """Main entry point for KPI scoring."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Show history if requested
    if args.history:
        # TODO: Implement database manager and history display
        print("History feature not yet implemented")
        return 0
    
    # Initialize components
    executor = CheckExecutor()
    engine = KPIScoreEngine(config)
    
    # Execute checks
    if args.verbose:
        print("Executing code quality checks...")
    
    check_results = executor.execute(args.paths)
    
    # Calculate KPI score
    if args.verbose:
        print("Calculating KPI score...")
    
    kpi_score = engine.calculate_score(check_results, args.paths[0] if args.paths else ".")
    
    # Format output
    output = format_output(kpi_score, args.format)
    
    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        if args.verbose:
            print(f"Results written to {args.output}")
    else:
        print(output)
    
    # Save to history if requested
    if args.save_history:
        # TODO: Implement database save
        if args.verbose:
            print("History saving not yet implemented")
    
    # Check threshold
    if args.threshold:
        if kpi_score.total_score < args.threshold:
            print(f"\n❌ Score {kpi_score.total_score:.1f} is below threshold {args.threshold}")
            return 1
        else:
            print(f"\n✅ Score {kpi_score.total_score:.1f} meets threshold {args.threshold}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())