"""Path operation types and data structures."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union


@dataclass(frozen=True)
class PathOperationResult:
    """パス操作結果の統一データクラス"""
    success: bool
    result: Optional[str]
    errors: list[str]
    warnings: list[str]
    metadata: dict[str, Any]

    def __post_init__(self):
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class PathInfo:
    """パス情報の不変データクラス"""
    path: str
    is_absolute: bool
    is_directory: bool
    is_file: bool
    parent: str
    name: str
    stem: str
    suffix: str
    parts: tuple[str, ...]

    @classmethod
    def from_path(cls, file_path: Union[str, Path]) -> 'PathInfo':
        """パスからPathInfoを作成"""
        path_obj = Path(file_path)
        return cls(
            path=str(path_obj),
            is_absolute=path_obj.is_absolute(),
            is_directory=path_obj.is_dir() if path_obj.exists() else False,
            is_file=path_obj.is_file() if path_obj.exists() else False,
            parent=str(path_obj.parent),
            name=path_obj.name,
            stem=path_obj.stem,
            suffix=path_obj.suffix,
            parts=path_obj.parts
        )
