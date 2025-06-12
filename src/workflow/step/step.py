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
    workspace_path: str
    contest_current_path: str
    contest_stock_path: Optional[str] = None
    contest_template_path: Optional[str] = None
    contest_temp_path: Optional[str] = None
    source_file_name: Optional[str] = None
    language_id: Optional[str] = None
    file_patterns: Optional[dict[str, list[str]]] = None

    def to_format_dict(self) -> dict[str, str]:
        """文字列フォーマット用の辞書を生成"""
        format_dict = {
            'contest_name': self.contest_name,
            'problem_name': self.problem_name,
            'language': self.language,
            'language_name': self.language,
            'env_type': self.env_type,
            'command_type': self.command_type,
            'workspace_path': self.workspace_path or '',
            'contest_current_path': self.contest_current_path or '',
            'contest_stock_path': self.contest_stock_path or '',
            'contest_template_path': self.contest_template_path or '',
            'contest_temp_path': self.contest_temp_path or '',
            'source_file_name': self.source_file_name or '',
            'language_id': self.language_id or '',
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

    def __post_init__(self):
        """データ検証"""
        if not self.cmd:
            raise ValueError(f"Step {self.type} must have non-empty cmd")

        # 各ステップタイプの必要な引数をチェック
        if self.type in [StepType.COPY, StepType.MOVE, StepType.MOVETREE] and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (src, dst)")

        if self.type in [StepType.MKDIR, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE] and len(self.cmd) < 1:
                raise ValueError(f"Step {self.type} requires at least 1 argument (path)")

        if self.type == StepType.DOCKER_EXEC and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (container, command)")

        if self.type == StepType.DOCKER_CP and len(self.cmd) < 2:
            raise ValueError(f"Step {self.type} requires at least 2 arguments (src, dst)")

        if self.type == StepType.DOCKER_RUN and len(self.cmd) < 1:
            raise ValueError(f"Step {self.type} requires at least 1 argument (image)")


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
