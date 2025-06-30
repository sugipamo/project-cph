"""Path operation types and data structures."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass(frozen=True)
class PathOperationResult:
    """パス操作結果の統一データクラス"""
    success: bool
    result: Optional[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
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
    parts: Tuple[str, ...]

    @classmethod
    def from_path_with_operations(cls, file_path: Union[str, object], path_operations: Any) -> 'PathInfo':
        """パスからPathInfoを作成（パス操作を依存性注入）"""
        if not path_operations.exists(file_path):
            raise FileNotFoundError(f"Path does not exist: {file_path}")

        path_str = str(file_path)
        path_parts = path_operations.get_path_parts(file_path)

        return cls(
            path=path_str,
            is_absolute=path_operations.is_absolute(file_path),
            is_directory=path_operations.is_directory(file_path),
            is_file=path_operations.is_file(file_path),
            parent=path_operations.get_parent(file_path),
            name=path_operations.get_name(file_path),
            stem=path_operations.get_stem(file_path),
            suffix=path_operations.get_suffix(file_path),
            parts=path_parts
        )
