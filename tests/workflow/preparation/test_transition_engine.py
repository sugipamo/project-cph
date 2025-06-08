"""Tests for transition engine module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.drivers.file.file_driver import FileDriver
from src.workflow.preparation.folder_mapping import FolderMapper
from src.workflow.preparation.state_definitions import WorkflowContext, WorkflowState
from src.workflow.preparation.transition_engine import TransitionContext, TransitionEngine, TransitionStep


class TestTransitionStep:
    """Test TransitionStep class."""

    def test_should_execute_no_condition(self):
        """Test step execution when no condition is set."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )
        context = MagicMock()

        assert step.should_execute(context) is True

    def test_should_execute_with_condition_true(self):
        """Test step execution when condition evaluates to True."""
        step = TransitionStep(
            name="test_step",
            condition="current_state=working",
            action={"type": "test"}
        )
        context = MagicMock()
        context.evaluate_condition.return_value = True

        assert step.should_execute(context) is True
        context.evaluate_condition.assert_called_once_with("current_state=working")

    def test_should_execute_with_condition_false(self):
        """Test step execution when condition evaluates to False."""
        step = TransitionStep(
            name="test_step",
            condition="current_state=idle",
            action={"type": "test"}
        )
        context = MagicMock()
        context.evaluate_condition.return_value = False

        assert step.should_execute(context) is False


class TestTransitionContext:
    """Test TransitionContext class."""

    def test_evaluate_condition_single_condition_true(self):
        """Test condition evaluation with single true condition."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context.evaluate_condition("current_state=working")
        assert result is True

    def test_evaluate_condition_single_condition_false(self):
        """Test condition evaluation with single false condition."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context.evaluate_condition("current_state=idle")
        assert result is False

    def test_evaluate_condition_multiple_conditions_all_true(self):
        """Test condition evaluation with multiple true conditions."""
        folder_mapper = MagicMock()
        folder_mapper.area_has_files.return_value = True

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context.evaluate_condition("current_state=working AND working_area.has_changes")
        assert result is True

    def test_evaluate_condition_multiple_conditions_one_false(self):
        """Test condition evaluation with one false condition."""
        folder_mapper = MagicMock()
        folder_mapper.area_has_files.return_value = False

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context.evaluate_condition("current_state=working AND working_area.has_changes")
        assert result is False

    def test_evaluate_single_condition_target_state(self):
        """Test single condition evaluation for target state."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("target_state=idle")
        assert result is True

    def test_evaluate_single_condition_working_area_has_files(self):
        """Test condition evaluation for working area files."""
        folder_mapper = MagicMock()
        folder_mapper.area_has_files.return_value = True

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("working_area.has_files")
        assert result is True
        folder_mapper.area_has_files.assert_called_once_with("working_area", context.current_context)

    def test_evaluate_single_condition_archive_area_exists(self):
        """Test condition evaluation for archive area existence."""
        folder_mapper = MagicMock()
        folder_mapper.area_exists.return_value = True

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("archive_area.abc123.a.exists")
        assert result is True

    def test_evaluate_single_condition_workspace_test_exists(self):
        """Test condition evaluation for workspace test directory."""
        folder_mapper = MagicMock()
        test_path = MagicMock()
        test_path.exists.return_value = True

        workspace_path = MagicMock()
        workspace_path.__truediv__ = MagicMock(return_value=test_path)
        folder_mapper.get_area_path.return_value = workspace_path

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("workspace_area.test.exists")
        assert result is True

    def test_evaluate_single_condition_always(self):
        """Test condition evaluation for 'always' condition."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("always")
        assert result is True

    def test_evaluate_single_condition_unknown(self):
        """Test condition evaluation for unknown condition."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = context._evaluate_single_condition("unknown_condition")
        assert result is False


class TestTransitionEngine:
    """Test TransitionEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.folder_mapper = MagicMock(spec=FolderMapper)
        self.file_driver = MagicMock(spec=FileDriver)
        self.engine = TransitionEngine(self.folder_mapper, self.file_driver)

    def test_init(self):
        """Test TransitionEngine initialization."""
        assert self.engine.folder_mapper == self.folder_mapper
        assert self.engine.file_driver == self.file_driver
        assert self.engine.logger is not None

    def test_execute_transition_no_steps(self):
        """Test transition execution with no steps."""
        current_state = WorkflowState.IDLE
        current_context = WorkflowContext("abc123", "a", "python")
        target_state = WorkflowState.WORKING
        target_context = WorkflowContext("abc123", "a", "python")

        success, results = self.engine.execute_transition(
            current_state, current_context, target_state, target_context, []
        )

        assert success is True
        assert results == []

    def test_execute_transition_single_step_success(self):
        """Test transition execution with single successful step."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )

        with patch.object(self.engine, '_execute_step', return_value=(True, "success")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is True
            assert len(results) == 1
            assert "✓ test_step: success" in results[0]

    def test_execute_transition_single_step_failure(self):
        """Test transition execution with single failed step."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )

        with patch.object(self.engine, '_execute_step', return_value=(False, "failed")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is False
            assert len(results) == 1
            assert "✗ test_step: failed" in results[0]

    def test_execute_transition_step_skipped(self):
        """Test transition execution with skipped step."""
        step = TransitionStep(
            name="test_step",
            condition="current_state=idle",
            action={"type": "test"}
        )

        current_state = WorkflowState.WORKING
        current_context = WorkflowContext("abc123", "a", "python")
        target_state = WorkflowState.IDLE
        target_context = WorkflowContext("abc123", "a", "python")

        success, results = self.engine.execute_transition(
            current_state, current_context, target_state, target_context, [step]
        )

        assert success is True
        assert len(results) == 1
        assert "⊘ test_step: skipped (condition not met)" in results[0]

    def test_execute_transition_step_exception(self):
        """Test transition execution with step raising exception."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )

        with patch.object(self.engine, '_execute_step', side_effect=Exception("test error")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is False
            assert len(results) == 1
            assert "✗ test_step: Error in test_step: test error" in results[0]

    def test_execute_step_unknown_action_type(self):
        """Test step execution with unknown action type."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "unknown"}
        )

        context = TransitionContext(
            current_state=WorkflowState.IDLE,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.WORKING,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        success, message = self.engine._execute_step(step, context)

        assert success is False
        assert "Unknown action type: unknown" in message

    def test_execute_step_archive_action(self):
        """Test step execution with archive action."""
        step = TransitionStep(
            name="archive_step",
            condition=None,
            action={"type": "archive", "from": "working_area", "to": "archive_area.{current_contest}.{current_problem}"}
        )

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        with patch.object(self.engine, '_execute_archive', return_value=(True, "archived successfully")):
            success, message = self.engine._execute_step(step, context)

            assert success is True
            assert "archived successfully" in message

    def test_execute_archive_source_not_exists(self):
        """Test archive action when source doesn't exist."""
        action = {
            "from": "working_area",
            "to": "archive_area.abc123.a",
            "mode": "move_all"
        }

        # Mock folder paths
        from_path = MagicMock()
        from_path.exists.return_value = False
        self.folder_mapper.get_area_path.return_value = from_path

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        with patch.object(self.engine, '_resolve_variable', side_effect=lambda x, ctx: x.replace("{current_contest}", "abc123").replace("{current_problem}", "a")):
            success, message = self.engine._execute_archive(action, context)

            assert success is True
            assert "does not exist, nothing to archive" in message

    def test_execute_archive_no_files(self):
        """Test archive action when no files to archive."""
        action = {
            "from": "working_area",
            "to": "archive_area.abc123.a",
            "mode": "move_all"
        }

        # Mock folder paths
        from_path = MagicMock()
        from_path.exists.return_value = True
        self.folder_mapper.get_area_path.return_value = from_path
        self.folder_mapper.area_has_files.return_value = False

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        with patch.object(self.engine, '_resolve_variable', side_effect=lambda x, ctx: x.replace("{current_contest}", "abc123").replace("{current_problem}", "a")):
            success, message = self.engine._execute_archive(action, context)

            assert success is True
            assert "No files to archive" in message

    def test_execute_archive_dry_run(self):
        """Test archive action in dry run mode."""
        action = {
            "from": "working_area",
            "to": "archive_area.abc123.a",
            "mode": "move_all"
        }

        # Mock folder paths
        from_path = MagicMock()
        from_path.exists.return_value = True
        to_path = MagicMock()
        self.folder_mapper.get_area_path.side_effect = [from_path, to_path]
        self.folder_mapper.area_has_files.return_value = True

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper,
            dry_run=True
        )

        with patch.object(self.engine, '_resolve_variable', side_effect=lambda x, ctx: x.replace("{current_contest}", "abc123").replace("{current_problem}", "a")):
            success, message = self.engine._execute_archive(action, context)

            assert success is True
            assert "Would archive" in message

    def test_execute_archive_unknown_from_area(self):
        """Test archive action with unknown from area."""
        action = {
            "from": "unknown_area",
            "to": "archive_area.abc123.a",
            "mode": "move_all"
        }

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        success, message = self.engine._execute_archive(action, context)

        assert success is False
        assert "Unknown from area: unknown_area" in message

    def test_execute_archive_unknown_to_area(self):
        """Test archive action with unknown to area."""
        action = {
            "from": "working_area",
            "to": "unknown_area",
            "mode": "move_all"
        }

        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=self.folder_mapper
        )

        success, message = self.engine._execute_archive(action, context)

        assert success is False
        assert "Unknown to area: unknown_area" in message
