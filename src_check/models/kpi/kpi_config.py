"""KPI configuration model."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class KPIConfig:
    """Configuration for KPI scoring system."""
    
    # Base score (starting point)
    base_score: float = 50.0
    
    # Category weights (must sum to 1.0)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "code_quality": 0.25,
        "architecture_quality": 0.25,
        "test_quality": 0.25,
        "security_quality": 0.25
    })
    
    # Score ranges
    target_min: float = 30.0
    target_max: float = 80.0
    
    # Severity impact points
    severity_impacts: Dict[str, float] = field(default_factory=lambda: {
        "critical": -10.0,
        "high": -5.0,
        "medium": -3.0,
        "low": -1.0,
        "info": -0.5
    })
    
    # Database configuration
    db_path: str = ".src_check_kpi.db"
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Parallel execution
    enable_parallel: bool = True
    max_workers: Optional[int] = None  # None = CPU count
    
    def validate(self) -> bool:
        """Validate configuration."""
        # Check weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Category weights must sum to 1.0, got {weight_sum}")
        
        # Check score ranges
        if self.target_min >= self.target_max:
            raise ValueError("target_min must be less than target_max")
        
        return True
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> "KPIConfig":
        """Create config from dictionary."""
        return cls(**config_dict)