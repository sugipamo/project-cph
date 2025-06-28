"""Tests for execution config"""
import pytest
from pathlib import Path
from src.configuration.execution_config import ExecutionPaths


class TestExecutionPaths:
    """Test ExecutionPaths dataclass"""
    
    def test_creation(self):
        """Test creating ExecutionPaths"""
        paths = ExecutionPaths(
            local_workspace=Path("/workspace"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        assert paths.local_workspace == Path("/workspace")
        assert paths.contest_current == Path("/current")
        assert paths.contest_stock == Path("/stock")
        assert paths.contest_template == Path("/template")
        assert paths.contest_temp == Path("/temp")
    
    def test_frozen_dataclass(self):
        """Test that ExecutionPaths is frozen"""
        paths = ExecutionPaths(
            local_workspace=Path("/workspace"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        with pytest.raises(AttributeError):
            paths.local_workspace = Path("/modified")
    
    def test_equality(self):
        """Test ExecutionPaths equality"""
        paths1 = ExecutionPaths(
            local_workspace=Path("/workspace"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        paths2 = ExecutionPaths(
            local_workspace=Path("/workspace"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        paths3 = ExecutionPaths(
            local_workspace=Path("/different"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        assert paths1 == paths2
        assert paths1 != paths3
    
    def test_with_string_paths(self):
        """Test creating ExecutionPaths with string paths"""
        paths = ExecutionPaths(
            local_workspace=Path("/workspace"),
            contest_current=Path("/current"),
            contest_stock=Path("/stock"),
            contest_template=Path("/template"),
            contest_temp=Path("/temp")
        )
        
        # All paths should be Path objects
        assert isinstance(paths.local_workspace, Path)
        assert isinstance(paths.contest_current, Path)
        assert isinstance(paths.contest_stock, Path)
        assert isinstance(paths.contest_template, Path)
        assert isinstance(paths.contest_temp, Path)