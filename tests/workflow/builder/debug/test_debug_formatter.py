"""Tests for debug formatting functions."""
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from src.workflow.builder.debug.debug_context import DebugContext, DebugEvent, create_debug_context
from src.workflow.builder.debug.debug_formatter import (
    format_debug_summary,
    format_debug_timeline,
    format_execution_debug,
    format_graph_debug,
    format_optimization_debug,
    format_validation_debug,
)


class TestFormatExecutionDebug:
    """Test execution debug formatting."""

    def test_format_basic_execution(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug("node1", "BUILD", context)

        assert result == "Executing BUILD [node1]"

    def test_format_with_command(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "BUILD", context,
            cmd=["gcc", "main.c", "-o", "main"]
        )

        assert "cmd: gcc main.c -o main" in result
        assert "Executing BUILD [node1]" in result

    def test_format_with_string_command(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "SHELL", context,
            cmd="echo hello"
        )

        assert "cmd: echo hello" in result

    def test_format_with_path(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "TOUCH", context,
            path="/tmp/file.txt"
        )

        assert "path: /tmp/file.txt" in result

    def test_format_with_copy_operation(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "COPY", context,
            source="src.txt",
            dest="dest.txt"
        )

        assert "copy: src.txt -> dest.txt" in result

    def test_format_with_dest_only(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "MKDIR", context,
            dest="/tmp/newdir"
        )

        assert "dest: /tmp/newdir" in result

    def test_format_with_options(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "TEST", context,
            allow_failure=True,
            show_output=True
        )

        assert "options: allow_failure, show_output" in result

    def test_format_with_single_option(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "TEST", context,
            allow_failure=True
        )

        assert "options: allow_failure" in result

    def test_format_complex_execution(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "build_main", "BUILD", context,
            cmd=["make", "all"],
            path="/workspace/project",
            allow_failure=False,
            show_output=True
        )

        parts = result.split(" | ")
        assert "Executing BUILD [build_main]" in parts
        assert "cmd: make all" in parts
        assert "path: /workspace/project" in parts
        assert "options: show_output" in parts

    def test_disabled_context_returns_empty(self):
        context = create_debug_context(enabled=False)
        result = format_execution_debug(
            "node1", "BUILD", context,
            cmd=["gcc", "main.c"]
        )

        assert result == ""


class TestFormatValidationDebug:
    """Test validation debug formatting."""

    def test_format_valid_result(self):
        context = create_debug_context(enabled=True)

        # Mock validation result
        result = Mock()
        result.is_valid = True
        result.errors = []
        result.warnings = []

        output = format_validation_debug("schema", result, context)

        assert "Validation schema: PASS" in output

    def test_format_invalid_result(self):
        context = create_debug_context(enabled=True)

        result = Mock()
        result.is_valid = False
        result.errors = ["error1", "error2"]
        result.warnings = ["warning1"]

        output = format_validation_debug("schema", result, context)

        assert "Validation schema: FAIL" in output
        assert "errors: 2" in output
        assert "warnings: 1" in output

    def test_format_result_with_errors_only(self):
        context = create_debug_context(enabled=True)

        result = Mock()
        result.is_valid = False
        result.errors = ["critical error"]
        result.warnings = []

        output = format_validation_debug("dependencies", result, context)

        assert "Validation dependencies: FAIL" in output
        assert "errors: 1" in output
        assert "warnings:" not in output

    def test_format_result_with_warnings_only(self):
        context = create_debug_context(enabled=True)

        result = Mock()
        result.is_valid = True
        result.errors = []
        result.warnings = ["minor issue"]

        output = format_validation_debug("style", result, context)

        assert "Validation style: PASS" in output
        assert "warnings: 1" in output
        assert "errors:" not in output

    def test_format_simple_result_without_attributes(self):
        context = create_debug_context(enabled=True)

        # Simple result without is_valid attribute
        result = True

        output = format_validation_debug("basic", result, context)

        assert output == "Validation basic: completed"

    def test_disabled_context_returns_empty(self):
        context = create_debug_context(enabled=False)

        result = Mock()
        result.is_valid = True

        output = format_validation_debug("schema", result, context)

        assert output == ""


class TestFormatGraphDebug:
    """Test graph debug formatting."""

    def test_format_basic_graph_operation(self):
        context = create_debug_context(enabled=True)
        graph_info = {}

        result = format_graph_debug("construction", graph_info, context)

        assert result == "Graph construction"

    def test_format_graph_with_node_count(self):
        context = create_debug_context(enabled=True)
        graph_info = {"node_count": 15}

        result = format_graph_debug("analysis", graph_info, context)

        assert "Graph analysis" in result
        assert "nodes: 15" in result

    def test_format_graph_with_edge_count(self):
        context = create_debug_context(enabled=True)
        graph_info = {"edge_count": 22}

        result = format_graph_debug("optimization", graph_info, context)

        assert "edges: 22" in result

    def test_format_graph_with_parallel_info(self):
        context = create_debug_context(enabled=True)
        graph_info = {
            "parallel_groups": 3,
            "max_parallelism": 8
        }

        result = format_graph_debug("execution", graph_info, context)

        assert "groups: 3" in result
        assert "max_parallel: 8" in result

    def test_format_complete_graph_info(self):
        context = create_debug_context(enabled=True)
        graph_info = {
            "node_count": 12,
            "edge_count": 18,
            "parallel_groups": 4,
            "max_parallelism": 6
        }

        result = format_graph_debug("complete", graph_info, context)

        parts = result.split(" | ")
        assert "Graph complete" in parts
        assert "nodes: 12" in parts
        assert "edges: 18" in parts
        assert "groups: 4" in parts
        assert "max_parallel: 6" in parts

    def test_disabled_context_returns_empty(self):
        context = create_debug_context(enabled=False)
        graph_info = {"node_count": 10}

        result = format_graph_debug("test", graph_info, context)

        assert result == ""


class TestFormatOptimizationDebug:
    """Test optimization debug formatting."""

    def test_format_basic_optimization(self):
        context = create_debug_context(enabled=True)
        stats = {}

        result = format_optimization_debug("dependency", stats, context)

        assert result == "Optimization dependency"

    def test_format_edge_reduction(self):
        context = create_debug_context(enabled=True)
        stats = {
            "original_edges": 100,
            "optimized_edges": 75
        }

        result = format_optimization_debug("redundancy", stats, context)

        assert "Optimization redundancy" in result
        assert "edges: 100 -> 75 (-25, -25.0%)" in result

    def test_format_edge_reduction_no_original(self):
        context = create_debug_context(enabled=True)
        stats = {
            "original_edges": 0,
            "optimized_edges": 0
        }

        result = format_optimization_debug("empty", stats, context)

        assert "edges: 0 -> 0 (-0, -0.0%)" in result

    def test_format_with_redundant_removal(self):
        context = create_debug_context(enabled=True)
        stats = {"removed_redundant": 12}

        result = format_optimization_debug("cleanup", stats, context)

        assert "redundant_removed: 12" in result

    def test_format_with_execution_time(self):
        context = create_debug_context(enabled=True)
        stats = {"execution_time_ms": 245}

        result = format_optimization_debug("performance", stats, context)

        assert "time: 245ms" in result

    def test_format_complete_optimization_stats(self):
        context = create_debug_context(enabled=True)
        stats = {
            "original_edges": 150,
            "optimized_edges": 90,
            "removed_redundant": 35,
            "execution_time_ms": 380
        }

        result = format_optimization_debug("full", stats, context)

        parts = result.split(" | ")
        assert "Optimization full" in parts
        assert "edges: 150 -> 90 (-60, -40.0%)" in parts
        assert "redundant_removed: 35" in parts
        assert "time: 380ms" in parts

    def test_disabled_context_returns_empty(self):
        context = create_debug_context(enabled=False)
        stats = {"original_edges": 50, "optimized_edges": 30}

        result = format_optimization_debug("test", stats, context)

        assert result == ""


class TestFormatDebugSummary:
    """Test debug summary formatting."""

    def test_format_empty_events(self):
        result = format_debug_summary([])

        assert result == "No debug events recorded"

    def test_format_debug_summary_basic(self):
        context = create_debug_context(enabled=True)
        events = [
            DebugEvent(
                timestamp=datetime.now(timezone.utc),
                level="info",
                component="builder",
                event_type="start",
                message="Starting build",
                data={},
                context=context
            ),
            DebugEvent(
                timestamp=datetime.now(timezone.utc),
                level="debug",
                component="validator",
                event_type="check",
                message="Checking dependencies",
                data={},
                context=context
            )
        ]

        result = format_debug_summary(events)

        assert "Debug Session Summary" in result
        assert "Total Events: 2" in result
        assert "Duration:" in result
        assert "Events by Level:" in result
        assert "Events by Component:" in result
        assert "Events by Type:" in result


class TestFormatDebugTimeline:
    """Test debug timeline formatting."""

    def test_format_empty_timeline(self):
        result = format_debug_timeline([])

        assert result == "No events in timeline"

    def test_format_single_event_timeline(self):
        context = create_debug_context(enabled=True)
        event = DebugEvent(
            timestamp=datetime(2024, 1, 1, 12, 30, 45, 123000, timezone.utc),
            level="info",
            component="builder",
            event_type="start",
            message="Process started",
            data={},
            context=context
        )

        result = format_debug_timeline([event])

        assert "Debug Timeline (most recent)" in result
        assert "12:30:45.123" in result
        assert "ℹ️" in result  # info level marker
        assert "builder.start: Process started" in result

    def test_format_multiple_events_timeline(self):
        context = create_debug_context(enabled=True)
        events = [
            DebugEvent(
                timestamp=datetime(2024, 1, 1, 12, 30, 45, 0, timezone.utc),
                level="debug",
                component="validator",
                event_type="check",
                message="Checking schema",
                data={},
                context=context
            ),
            DebugEvent(
                timestamp=datetime(2024, 1, 1, 12, 30, 46, 0, timezone.utc),
                level="warning",
                component="optimizer",
                event_type="optimize",
                message="Minor optimization issue",
                data={},
                context=context
            ),
            DebugEvent(
                timestamp=datetime(2024, 1, 1, 12, 30, 47, 0, timezone.utc),
                level="error",
                component="executor",
                event_type="execute",
                message="Execution failed",
                data={},
                context=context
            )
        ]

        result = format_debug_timeline(events)

        lines = result.split("\n")
        assert len(lines) >= 5  # Header + separator + 3 events
        assert "🔍" in result  # debug marker
        assert "⚠️" in result   # warning marker
        assert "❌" in result  # error marker
        assert "validator.check: Checking schema" in result
        assert "optimizer.optimize: Minor optimization issue" in result
        assert "executor.execute: Execution failed" in result

    def test_format_timeline_with_max_events_limit(self):
        # Create 25 events
        context = create_debug_context(enabled=True)
        events = []
        for i in range(25):
            events.append(DebugEvent(
                timestamp=datetime(2024, 1, 1, 12, 30, i, 0, timezone.utc),
                level="info",
                component="test",
                event_type="event",
                message=f"Event {i}",
                data={},
                context=context
            ))

        result = format_debug_timeline(events, max_events=5)

        lines = result.split("\n")
        # Should only show last 5 events (plus header lines)
        event_lines = [line for line in lines if "Event" in line]
        assert len(event_lines) == 5
        assert "Event 24" in result  # Latest event
        assert "Event 20" in result  # 5th from last
        assert "Event 19" not in result  # Should be excluded

    def test_timeline_level_markers(self):
        levels_and_markers = [
            ("error", "❌"),
            ("warning", "⚠️"),
            ("info", "ℹ️"),
            ("debug", "🔍"),
            ("unknown", "📝")  # Default marker
        ]

        context = create_debug_context(enabled=True)
        for level, expected_marker in levels_and_markers:
            event = DebugEvent(
                timestamp=datetime.now(timezone.utc),
                level=level,
                component="test",
                event_type="test",
                message="Test message",
                data={},
                context=context
            )

            result = format_debug_timeline([event])
            assert expected_marker in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_execution_with_none_values(self):
        context = create_debug_context(enabled=True)
        result = format_execution_debug(
            "node1", "BUILD", context,
            cmd=None,
            path=None,
            dest=None
        )

        # Should not crash and should show basic execution info
        assert "Executing BUILD [node1]" in result

    def test_format_validation_with_partial_attributes(self):
        context = create_debug_context(enabled=True)

        result = Mock()
        result.is_valid = True
        # getattr will return Mock objects for missing attributes, which can cause issues
        # We need to make sure the mock has the right behavior
        delattr(result, 'errors')  # Remove the attribute completely
        delattr(result, 'warnings')  # Remove the attribute completely

        output = format_validation_debug("partial", result, context)

        assert "Validation partial: PASS" in output
        # Should handle missing attributes gracefully by using default empty lists

    def test_format_graph_with_invalid_info_types(self):
        context = create_debug_context(enabled=True)
        graph_info = {
            "node_count": "invalid",  # Should be int
            "edge_count": None,
            "parallel_groups": [],
            "max_parallelism": {}
        }

        # Should not crash
        result = format_graph_debug("test", graph_info, context)
        assert "Graph test" in result

    def test_format_optimization_with_division_by_zero_risk(self):
        context = create_debug_context(enabled=True)
        stats = {
            "original_edges": 0,
            "optimized_edges": 5  # Edge case: more optimized than original
        }

        result = format_optimization_debug("test", stats, context)

        # Should handle edge case gracefully
        assert "edges: 0 -> 5" in result
