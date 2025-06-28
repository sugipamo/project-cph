"""Tests for output config"""
import pytest
from src.configuration.output_config import OutputConfig


class TestOutputConfig:
    """Test OutputConfig dataclass"""
    
    def test_creation(self):
        """Test creating OutputConfig"""
        config = OutputConfig(
            show_workflow_summary=True,
            show_step_details=False,
            show_execution_completion=True,
            format_preset="default"
        )
        
        assert config.show_workflow_summary is True
        assert config.show_step_details is False
        assert config.show_execution_completion is True
        assert config.format_preset == "default"
    
    def test_frozen_dataclass(self):
        """Test that OutputConfig is frozen"""
        config = OutputConfig(
            show_workflow_summary=True,
            show_step_details=True,
            show_execution_completion=True,
            format_preset="verbose"
        )
        
        with pytest.raises(AttributeError):
            config.show_workflow_summary = False
    
    def test_equality(self):
        """Test OutputConfig equality"""
        config1 = OutputConfig(
            show_workflow_summary=True,
            show_step_details=False,
            show_execution_completion=True,
            format_preset="default"
        )
        
        config2 = OutputConfig(
            show_workflow_summary=True,
            show_step_details=False,
            show_execution_completion=True,
            format_preset="default"
        )
        
        config3 = OutputConfig(
            show_workflow_summary=False,
            show_step_details=False,
            show_execution_completion=True,
            format_preset="default"
        )
        
        assert config1 == config2
        assert config1 != config3
    
    def test_different_format_presets(self):
        """Test OutputConfig with different format presets"""
        config_minimal = OutputConfig(
            show_workflow_summary=False,
            show_step_details=False,
            show_execution_completion=False,
            format_preset="minimal"
        )
        
        config_verbose = OutputConfig(
            show_workflow_summary=True,
            show_step_details=True,
            show_execution_completion=True,
            format_preset="verbose"
        )
        
        assert config_minimal.format_preset == "minimal"
        assert config_verbose.format_preset == "verbose"
        assert config_minimal != config_verbose