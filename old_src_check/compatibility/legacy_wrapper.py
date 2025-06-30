"""Legacy compatibility wrapper for seamless migration."""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from src_check.orchestrator.check_executor import CheckExecutor
from src_check.core.scoring import KPIScoreEngine
from src_check.models.kpi import KPIConfig
from src_check.compatibility.converters import ResultConverter
from src_check.core.result_writer import ResultWriter


class LegacyCompatibilityWrapper:
    """
    Wrapper to maintain backward compatibility while introducing KPI scoring.
    
    This wrapper allows the existing src_check to work unchanged while
    optionally enabling KPI scoring behind the scenes.
    """
    
    def __init__(self, kpi_config: Optional[KPIConfig] = None):
        """Initialize the compatibility wrapper."""
        self.legacy_executor = CheckExecutor()
        self.kpi_engine = KPIScoreEngine(kpi_config or KPIConfig())
        self.result_converter = ResultConverter()
        self.use_kpi = self._detect_kpi_mode()
        
    def execute(self, target_paths: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute checks with optional KPI scoring.
        
        Args:
            target_paths: Paths to check
            **kwargs: Additional arguments
            
        Returns:
            Results in legacy format
        """
        # Execute legacy checks
        legacy_results = self.legacy_executor.execute(target_paths)
        
        # If KPI mode is not enabled, return legacy results as-is
        if not self.use_kpi:
            return {"legacy_results": legacy_results, "kpi_score": None}
        
        # Calculate KPI score
        project_path = str(Path.cwd()) if not target_paths else target_paths[0]
        kpi_score = self.kpi_engine.calculate_score(legacy_results, project_path)
        
        # Optionally write KPI results
        if self._should_write_kpi_results():
            self._write_kpi_results(kpi_score)
        
        return {
            "legacy_results": legacy_results,
            "kpi_score": kpi_score
        }
    
    def _detect_kpi_mode(self) -> bool:
        """Detect if KPI mode should be enabled."""
        # Check environment variable
        if os.environ.get("SRC_CHECK_KPI_MODE", "").lower() in ["true", "1", "yes"]:
            return True
        
        # Check for KPI config file
        if Path(".src_check_kpi.yaml").exists():
            return True
        
        # Check for experimental flag
        if os.environ.get("SRC_CHECK_EXPERIMENTAL_KPI", "").lower() in ["true", "1", "yes"]:
            return True
        
        return False
    
    def _should_write_kpi_results(self) -> bool:
        """Check if KPI results should be written."""
        return os.environ.get("SRC_CHECK_KPI_OUTPUT", "").lower() in ["true", "1", "yes"]
    
    def _write_kpi_results(self, kpi_score):
        """Write KPI results to file."""
        output_dir = Path("check_result")
        output_dir.mkdir(exist_ok=True)
        
        # Write text format
        text_output = self.result_converter.kpi_score_to_text_format(kpi_score)
        with open(output_dir / "kpi_score.txt", "w", encoding="utf-8") as f:
            f.write(text_output)
        
        # Write JSON format
        json_output = self.result_converter.kpi_score_to_json_format(kpi_score)
        with open(output_dir / "kpi_score.json", "w", encoding="utf-8") as f:
            f.write(json_output)
    
    @classmethod
    def create_from_args(cls, args: Dict[str, Any]) -> "LegacyCompatibilityWrapper":
        """
        Create wrapper from command line arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Configured wrapper instance
        """
        # Load KPI config if specified
        kpi_config = None
        config_path = args.get("kpi_config")
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
                kpi_config = KPIConfig.from_dict(config_data)
        
        return cls(kpi_config)