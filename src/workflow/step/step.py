"""純粋関数ベースのステップ生成のための核となるデータ構造
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class StepType(Enum):
    """ステップの種類"""
    SHELL = "shell"
    PYTHON = "python"
    COPY = "copy"
    COPYTREE = "copytree"
    MOVE = "move"
    MOVETREE = "movetree"
    MKDIR = "mkdir"
    TOUCH = "touch"
    REMOVE = "remove"
    RMTREE = "rmtree"
    OJ = "oj"
    TEST = "test"
    BUILD = "build"
    RESULT = "result"
    DOCKER_EXEC = "docker_exec"
    DOCKER_CP = "docker_cp"
    DOCKER_RUN = "docker_run"
    DOCKER_BUILD = "docker_build"
    DOCKER_COMMIT = "docker_commit"
    DOCKER_RM = "docker_rm"
    DOCKER_RMI = "docker_rmi"
    CHMOD = "chmod"
    RUN = "run"


@dataclass(frozen=True)
class StepContext:
    """ステップ生成に必要な全ての情報を含む不変データクラス"""
    # ユーザー入力
    contest_name: str
    problem_name: str
    language: str
    env_type: str
    command_type: str

    # 環境設定
    local_workspace_path: str
    contest_current_path: str
    contest_stock_path: Optional[str] = None
    contest_template_path: Optional[str] = None
    contest_temp_path: Optional[str] = None
    source_file_name: Optional[str] = None
    language_id: Optional[str] = None
    file_patterns: Optional[dict[str, list[str]]] = None

    def _get_required_path(self, path_value, name):
        """Get required path value.

        Args:
            path_value: Path value to check
            name: Name of the path for error messages

        Returns:
            Path as string

        Raises:
            ValueError: If path is None or empty
        """
        if path_value is None or str(path_value).strip() == '':
            raise ValueError(f"Required path '{name}' is None or empty")
        return str(path_value)

    def _get_required_filename(self, filename_value, name):
        """Get required filename value.

        Args:
            filename_value: Filename value to check
            name: Name of the filename for error messages

        Returns:
            Filename as string

        Raises:
            ValueError: If filename is None or empty
        """
        if filename_value is None or str(filename_value).strip() == '':
            raise ValueError(f"Required filename '{name}' is None or empty")
        return str(filename_value)

    def _get_required_identifier(self, identifier_value, name):
        """Get required identifier value.

        Args:
            identifier_value: Identifier value to check
            name: Name of the identifier for error messages

        Returns:
            Identifier as string

        Raises:
            ValueError: If identifier is None or empty
        """
        if identifier_value is None or str(identifier_value).strip() == '':
            raise ValueError(f"Required identifier '{name}' is None or empty")
        return str(identifier_value)

    def to_format_dict(self) -> dict[str, str]:
        """文字列フォーマット用の辞書を生成"""
        format_dict = {
            'contest_name': self.contest_name,
            'problem_name': self.problem_name,
            'language': self.language,
            'language_name': self.language,
            'env_type': self.env_type,
            'command_type': self.command_type,
            'local_workspace_path': self._get_required_path(self.local_workspace_path, 'local_workspace_path'),
            'contest_current_path': self._get_required_path(self.contest_current_path, 'contest_current_path'),
            'contest_stock_path': self._get_required_path(self.contest_stock_path, 'contest_stock_path'),
            'contest_template_path': self._get_required_path(self.contest_template_path, 'contest_template_path'),
            'contest_temp_path': self._get_required_path(self.contest_temp_path, 'contest_temp_path'),
            'source_file_name': self._get_required_filename(self.source_file_name, 'source_file_name'),
            'language_id': self._get_required_identifier(self.language_id, 'language_id'),
        }

        # Add file patterns to format dict
        if self.file_patterns:
            for pattern_name, patterns in self.file_patterns.items():
                # Convert list of patterns to comma-separated string for simple templates
                format_dict[pattern_name] = ','.join(patterns)


        return format_dict


@dataclass(frozen=True)
class Step:
    """実行可能な単一ステップを表現する不変データクラス"""
    type: StepType
    cmd: list[str]
    allow_failure: bool = False
    show_output: bool = False
    cwd: Optional[str] = None
    force_env_type: Optional[str] = None
    format_options: Optional[dict[str, Any]] = None
    output_format: Optional[str] = None
    format_preset: Optional[str] = None
    when: Optional[str] = None
    name: Optional[str] = None
    auto_generated: bool = False  # fitting/依存関係解決で自動生成されたステップかどうか
    max_workers: int = 1  # ステップの並列実行worker数（1=逐次実行、2以上=並列実行）

    def __post_init__(self):
        """データ検証"""
        if not self.cmd:
            raise ValueError(f"Step {self.type} must have non-empty cmd")

        # 各ステップタイプの必要な引数をチェック
        if self.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE, StepType.DOCKER_CP] and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (src, dst)")

        if self.type in [StepType.MKDIR, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE] and len(self.cmd) < 1:
                raise ValueError(f"Step {self.type} requires at least 1 argument (path)")

        if self.type == StepType.DOCKER_EXEC and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (container, command)")

        if self.type in [StepType.DOCKER_RUN, StepType.DOCKER_BUILD] and len(self.cmd) < 1:
            raise ValueError(f"Step {self.type} requires at least 1 argument")

        if self.type == StepType.DOCKER_COMMIT and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (container, image)")

        if self.type in [StepType.DOCKER_RM, StepType.DOCKER_RMI] and len(self.cmd) < 1:
            raise ValueError(f"Step {self.type} requires at least 1 argument")

        if self.type == StepType.CHMOD and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (mode, path)")


@dataclass(frozen=True)
class StepGenerationResult:
    """ステップ生成の結果を表現するクラス"""
    steps: list[Step]
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])

    @property
    def is_success(self) -> bool:
        """エラーがない場合はTrue"""
        return len(self.errors) == 0

    def add_error(self, error: str) -> 'StepGenerationResult':
        """エラーを追加した新しいインスタンスを返す"""
        new_errors = [*list(self.errors), error]
        return StepGenerationResult(self.steps, new_errors, self.warnings)

    def add_warning(self, warning: str) -> 'StepGenerationResult':
        """警告を追加した新しいインスタンスを返す"""
        new_warnings = [*list(self.warnings), warning]
        return StepGenerationResult(self.steps, self.errors, new_warnings)
