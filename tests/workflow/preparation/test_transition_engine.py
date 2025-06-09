"""Tests for transition engine module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.drivers.file.file_driver import FileDriver
from src.workflow.preparation.core.state_definitions import WorkflowContext, WorkflowState
from src.workflow.preparation.file.folder_mapping import FolderMapper
from src.workflow.preparation.state.conditions.condition_evaluator import (
    ConditionEvaluator,
    TransitionContext,
    TransitionStep,
)
from src.workflow.preparation.state.transition.transition_engine import TransitionEngine


class TestTransitionStep:
    """Test TransitionStep class."""

    def test_step_creation(self):
        """Test TransitionStep creation."""
        step = TransitionStep(
            name="test_step",
            condition="current_state=working",
            action={"type": "test"},
            description="Test step"
        )
        assert step.name == "test_step"
        assert step.condition == "current_state=working"
        assert step.action == {"type": "test"}
        assert step.description == "Test step"

    def test_step_creation_minimal(self):
        """Test TransitionStep creation with minimal parameters."""
        step = TransitionStep(
            name="minimal_step",
            condition=None,
            action={"type": "test"}
        )
        assert step.name == "minimal_step"
        assert step.condition is None
        assert step.action == {"type": "test"}
        assert step.description is None


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
        """Test condition evaluation with multiple all-true conditions."""
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
        """Test condition evaluation with multiple conditions where one is false."""
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
        """Test condition evaluation for target state."""
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
        """Test condition evaluation for working area has files."""
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
        """Test condition evaluation for archive area exists."""
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
        """Test condition evaluation for workspace test exists."""
        folder_mapper = MagicMock()
        test_path = MagicMock()
        test_path.exists.return_value = True
        workspace_path = MagicMock()
        workspace_path.__truediv__.return_value = test_path
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
        """Test condition evaluation for always true condition."""
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


class TestConditionEvaluator:
    """Test ConditionEvaluator class."""

    def test_create_context(self):
        """Test creating transition context."""
        folder_mapper = MagicMock()
        current_state = WorkflowState.WORKING
        current_context = WorkflowContext("abc123", "a", "python")
        target_state = WorkflowState.IDLE
        target_context = WorkflowContext("abc123", "a", "python")

        context = ConditionEvaluator.create_context(
            current_state=current_state,
            current_context=current_context,
            target_state=target_state,
            target_context=target_context,
            folder_mapper=folder_mapper,
            dry_run=True
        )

        assert context.current_state == current_state
        assert context.current_context == current_context
        assert context.target_state == target_state
        assert context.target_context == target_context
        assert context.folder_mapper == folder_mapper
        assert context.dry_run is True

    def test_evaluate(self):
        """Test condition evaluation."""
        folder_mapper = MagicMock()
        context = TransitionContext(
            current_state=WorkflowState.WORKING,
            current_context=WorkflowContext("abc123", "a", "python"),
            target_state=WorkflowState.IDLE,
            target_context=WorkflowContext("abc123", "a", "python"),
            folder_mapper=folder_mapper
        )

        result = ConditionEvaluator.evaluate(context, "current_state=working")
        assert result is True


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
        assert self.engine.action_executor is not None
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

        with patch.object(self.engine.action_executor, 'execute_action', return_value=(True, "success")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is True
            assert len(results) == 1
            assert "✅ test_step: success" in results[0]

    def test_execute_transition_single_step_failure(self):
        """Test transition execution with single failed step."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )

        with patch.object(self.engine.action_executor, 'execute_action', return_value=(False, "failed")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is False
            assert len(results) == 1
            assert "❌ test_step failed: failed" in results[0]

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
        assert "⏭️  スキップ: test_step (current_state=idle)" in results[0]

    def test_execute_transition_step_exception(self):
        """Test transition execution with step raising exception."""
        step = TransitionStep(
            name="test_step",
            condition=None,
            action={"type": "test"}
        )

        with patch.object(self.engine.action_executor, 'execute_action', side_effect=Exception("test error")):
            current_state = WorkflowState.IDLE
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.WORKING
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step]
            )

            assert success is False
            assert len(results) == 1
            assert "❌ test_step error: test error" in results[0]

    def test_execute_transition_multiple_steps(self):
        """Test transition execution with multiple steps."""
        step1 = TransitionStep(name="step1", condition=None, action={"type": "test1"})
        step2 = TransitionStep(name="step2", condition="current_state=idle", action={"type": "test2"})
        step3 = TransitionStep(name="step3", condition=None, action={"type": "test3"})

        # Mock action executor to return success for step1 and step3
        def mock_execute_action(action, context):
            if action["type"] == "test1":
                return True, "step1 success"
            if action["type"] == "test3":
                return True, "step3 success"
            return False, "unexpected action"

        with patch.object(self.engine.action_executor, 'execute_action', side_effect=mock_execute_action):
            current_state = WorkflowState.WORKING  # This will cause step2 to be skipped
            current_context = WorkflowContext("abc123", "a", "python")
            target_state = WorkflowState.IDLE
            target_context = WorkflowContext("abc123", "a", "python")

            success, results = self.engine.execute_transition(
                current_state, current_context, target_state, target_context, [step1, step2, step3]
            )

            assert success is True
            assert len(results) == 3
            assert "✅ step1: step1 success" in results[0]
            assert "⏭️  スキップ: step2 (current_state=idle)" in results[1]
            assert "✅ step3: step3 success" in results[2]
