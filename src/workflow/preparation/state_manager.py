"""State manager for coordinating workflow state and transitions."""
import logging
from typing import Any, Dict, List, Tuple

from src.infrastructure.persistence.sqlite.system_config_loader import SystemConfigLoader

from .folder_mapping import FolderMapper, create_folder_mapper_from_env
from .state_definitions import WorkflowContext, WorkflowState, validate_state_transition
from .transition_engine import TransitionEngine, TransitionStep


class StateManager:
    """Manages workflow state and executes transitions."""

    def __init__(self, operations, config_loader: SystemConfigLoader, env_json: Dict[str, Any]):
        """Initialize state manager with DI container."""
        self.operations = operations
        self.config_loader = config_loader
        self.env_json = env_json
        self.logger = logging.getLogger(__name__)
        self._folder_mapper = None
        self._transition_engine = None
        self._file_driver = None

    @property
    def file_driver(self):
        """Lazy loading of file driver from DI container."""
        if self._file_driver is None:
            self._file_driver = self.operations.resolve("file_driver")
        return self._file_driver

    def get_current_state(self) -> Tuple[WorkflowState, WorkflowContext]:
        """Get current workflow state and context."""
        # Load from SQLite
        context_data = self.config_loader.get_current_context()

        context = WorkflowContext(
            contest_name=context_data.get("contest_name"),
            problem_name=context_data.get("problem_name"),  # Note: using problem_name from DB
            language=context_data.get("language")
        )

        # Determine state based on context
        if context.is_valid_working_context():
            return WorkflowState.WORKING, context
        return WorkflowState.IDLE, context

    def execute_transition(
        self,
        target_state: WorkflowState,
        target_context: WorkflowContext,
        dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Execute a state transition."""
        current_state, current_context = self.get_current_state()

        # Validate transition
        valid, message = validate_state_transition(current_state, target_state, target_context)
        if not valid:
            return False, [f"Invalid transition: {message}"]

        # Skip if already in target state with same context
        if current_state == target_state and current_context.matches(target_context):
            return True, [f"Already in {target_state.value} state with same context"]

        # Get transition steps
        transition_steps = self._get_transition_steps(current_state, target_state)

        # Execute transition
        engine = self._get_transition_engine(target_context.language)
        success, results = engine.execute_transition(
            current_state=current_state,
            current_context=current_context,
            target_state=target_state,
            target_context=target_context,
            transition_steps=transition_steps,
            dry_run=dry_run
        )

        # Update state in SQLite if successful and not dry run
        if success and not dry_run:
            self._update_stored_state(target_state, target_context)

        return success, results

    def _get_transition_steps(self, from_state: WorkflowState, to_state: WorkflowState) -> List[TransitionStep]:
        """Get transition steps for a state change."""
        if to_state == WorkflowState.WORKING:
            # 常にworking状態なので、問題切り替えのステップのみ
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

        # IDLE状態への遷移は基本的に使わない（常にworking）
        return []

    def _get_folder_mapper(self, language: str) -> FolderMapper:
        """Get folder mapper for a language."""
        if self._folder_mapper is None or getattr(self._folder_mapper, '_language', None) != language:
            self._folder_mapper = create_folder_mapper_from_env(self.env_json, language)
            self._folder_mapper._language = language  # Store for cache invalidation
        return self._folder_mapper

    def _get_transition_engine(self, language: str) -> TransitionEngine:
        """Get transition engine for a language."""
        if self._transition_engine is None or getattr(self._transition_engine, '_language', None) != language:
            folder_mapper = self._get_folder_mapper(language)
            self._transition_engine = TransitionEngine(folder_mapper, self.file_driver)
            self._transition_engine._language = language  # Store for cache invalidation
        return self._transition_engine

    def _update_stored_state(self, state: WorkflowState, context: WorkflowContext) -> None:
        """Update stored state in SQLite."""
        if state == WorkflowState.WORKING:
            # Store working context
            self.config_loader.update_current_context(
                contest_name=context.contest_name,
                problem_name=context.problem_name,  # Note: using problem_name for DB
                language=context.language
            )
        elif state == WorkflowState.IDLE:
            # Clear context
            self.config_loader.clear_context_value("contest_name")
            self.config_loader.clear_context_value("problem_name")
            self.config_loader.clear_context_value("language")

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state."""
        current_state, current_context = self.get_current_state()

        summary = {
            "current_problem": None,
            "working_directory": None,
            "has_unsaved_changes": False,
            "available_problems": []
        }

        if current_state == WorkflowState.WORKING and current_context.language:
            # 現在作業中の問題
            if current_context.contest_name and current_context.problem_name:
                summary["current_problem"] = f"{current_context.contest_name}/{current_context.problem_name}"

            folder_mapper = self._get_folder_mapper(current_context.language)

            # 作業ディレクトリ
            working_path = folder_mapper.get_area_path("working_area", current_context)
            summary["working_directory"] = str(working_path)

            # 未保存の変更があるか
            summary["has_unsaved_changes"] = folder_mapper.area_has_files("working_area", current_context)

            # 利用可能な問題（アーカイブ）
            archives = folder_mapper.list_archives()
            summary["available_problems"] = [f"{contest}/{problem}" for contest, problem in archives]

        return summary
