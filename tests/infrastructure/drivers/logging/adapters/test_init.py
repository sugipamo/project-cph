"""Tests for logging adapters __init__ module"""

import pytest

from src.infrastructure.drivers.logging.adapters import (
    ApplicationLoggerAdapter,
    WorkflowLoggerAdapter,
)


class TestAdaptersInit:
    """Tests for the adapters module initialization"""

    def test_imports_available(self):
        """Test that all expected classes are available for import"""
        # Test that classes can be imported
        assert ApplicationLoggerAdapter is not None
        assert WorkflowLoggerAdapter is not None

    def test_all_exports(self):
        """Test that __all__ contains expected exports"""
        from src.infrastructure.drivers.logging.adapters import __all__

        expected_exports = [
            'ApplicationLoggerAdapter',
            'WorkflowLoggerAdapter',
        ]

        assert set(__all__) == set(expected_exports)
        assert len(__all__) == len(expected_exports)  # No duplicates

    def test_classes_are_classes(self):
        """Test that exported items are actually classes"""
        assert isinstance(ApplicationLoggerAdapter, type)
        assert isinstance(WorkflowLoggerAdapter, type)

    def test_classes_can_be_instantiated(self):
        """Test that classes can be instantiated (basic smoke test)"""
        from unittest.mock import Mock

        mock_output_manager = Mock()

        # Test ApplicationLoggerAdapter instantiation
        app_adapter = ApplicationLoggerAdapter(mock_output_manager)
        assert app_adapter is not None
        assert app_adapter.output_manager == mock_output_manager

        # Test WorkflowLoggerAdapter instantiation with minimal config
        workflow_config = {
            "enabled": True,
            "format": {
                "icons": {}
            }
        }
        workflow_adapter = WorkflowLoggerAdapter(mock_output_manager, workflow_config)
        assert workflow_adapter is not None
        assert workflow_adapter.output_manager == mock_output_manager
