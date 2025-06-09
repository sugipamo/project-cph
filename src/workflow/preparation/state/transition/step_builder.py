"""Step builder for creating transition step configurations."""
from typing import List

from ...core.state_definitions import WorkflowState
from ..conditions.condition_evaluator import TransitionStep


class StepBuilder:
    """Builds transition step configurations for different state transitions."""

    @staticmethod
    def build_transition_steps(target_state: WorkflowState) -> List[TransitionStep]:
        """Build transition steps for reaching the target state."""
        if target_state == WorkflowState.WORKING:
            return StepBuilder._build_working_state_steps()

        # IDLE状態への遷移は基本的に使わない（常にworking）
        return []

    @staticmethod
    def _build_working_state_steps() -> List[TransitionStep]:
        """Build steps for transitioning to WORKING state."""
        return [
            TransitionStep(
                name="preserve_current_work",
                condition="current_state=working AND working_area.has_changes",
                action={
                    "type": "archive",
                    "from": "working_area",
                    "to": "archive_area.{current_contest}.{current_problem}",
                    "mode": "move_all"
                },
                description="現在の作業を保存してから切り替え"
            ),
            TransitionStep(
                name="initialize_work_area",
                condition=None,  # Always execute
                action={
                    "type": "restore_or_create",
                    "to": "working_area",
                    "source_priority": [
                        {
                            "from": "archive_area.{contest_name}.{problem_name}",
                            "condition": "exists",
                            "priority": 1,
                            "description": "既存作業を復元"
                        },
                        {
                            "from": "template_area",
                            "condition": "always",
                            "priority": 2,
                            "description": "テンプレートから新規作成"
                        }
                    ]
                },
                description="作業エリアを初期化（既存作業またはテンプレート）"
            ),
            TransitionStep(
                name="setup_test_environment",
                condition="workspace_area.test.exists",
                action={
                    "type": "move",
                    "from": "workspace_area.test",
                    "to": "working_area.test"
                },
                description="テストファイルを作業エリアに移動"
            )
        ]


# Compatibility import for TransitionStep
from ..conditions.condition_evaluator import TransitionStep

__all__ = ["StepBuilder", "TransitionStep"]
