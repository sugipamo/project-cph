"""File operation request."""
import time
from pathlib import Path
from typing import Any, Optional

from src.domain.constants.operation_type import OperationType
from src.domain.requests.base.base_request import OperationRequestFoundation
from src.domain.requests.file.file_op_type import FileOpType
from src.domain.results.file_result import FileResult


class FileRequest(OperationRequestFoundation):
    """Request for file operations."""

    def __init__(self, op: FileOpType, path: str, content: Optional[str] = None,
                 dst_path: Optional[str] = None, debug_tag: Optional[str] = None,
                 name: Optional[str] = None, allow_failure: bool = False):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.path = path
        self.content = content
        self.dst_path = dst_path
        self.allow_failure = allow_failure

    @property
    def operation_type(self) -> OperationType:
        """Return the operation type."""
        return OperationType.FILE

    def _execute_core(self, driver: Any) -> FileResult:
        """Core execution logic for file operations."""
        self._start_time = time.time()
        try:
            actual_driver = self._resolve_driver(driver)
            return self._dispatch_file_operation(actual_driver)
        except Exception as e:
            return self._handle_file_error(e)

    def _resolve_driver(self, driver: Any) -> Any:
        """Resolve the actual file driver from unified driver if needed."""
        if hasattr(driver, '_get_cached_driver') and callable(driver._get_cached_driver):
            return driver._get_cached_driver("file_driver")
        return driver

    def _dispatch_file_operation(self, actual_driver: Any) -> FileResult:
        """Dispatch to appropriate file operation handler."""
        if self.op == FileOpType.READ:
            return self._handle_read_operation(actual_driver)
        if self.op == FileOpType.WRITE:
            return self._handle_write_operation(actual_driver)
        if self.op == FileOpType.EXISTS:
            return self._handle_exists_operation(actual_driver)
        if self.op in (FileOpType.MOVE, FileOpType.COPY, FileOpType.COPYTREE, FileOpType.MOVETREE):
            return self._handle_move_copy_operations(actual_driver)
        if self.op in (FileOpType.REMOVE, FileOpType.RMTREE, FileOpType.MKDIR, FileOpType.TOUCH):
            return self._handle_single_path_operations(actual_driver)
        raise ValueError(f"Unsupported file operation: {self.op}")

    def _handle_read_operation(self, actual_driver: Any) -> FileResult:
        """Handle file read operation."""
        # Check if it's a mock driver with mock file system
        if hasattr(actual_driver, 'contents') and hasattr(actual_driver, 'files'):
            return self._read_from_mock_driver(actual_driver)

        # Regular driver - use real filesystem
        resolved_path = actual_driver.resolve_path(self.path)
        with resolved_path.open("r", encoding="utf-8") as f:
            content = f.read()
        return FileResult(content=content, path=self.path, success=True, request=self)

    def _read_from_mock_driver(self, actual_driver: Any) -> FileResult:
        """Read file content from mock driver."""
        abs_path = actual_driver.base_dir / Path(self.path)
        if abs_path in actual_driver.contents:
            content = actual_driver.contents[abs_path]
            return FileResult(content=content, path=self.path, success=True, request=self)
        # MockFileDriver: return empty content for non-existent files
        return FileResult(content="", path=self.path, success=True, request=self)

    def _handle_write_operation(self, actual_driver: Any) -> FileResult:
        """Handle file write operation."""
        # Check if it's a mock driver with different API
        if hasattr(actual_driver, '_create_impl'):
            # For drivers with _create_impl, resolve path first
            resolved_path = actual_driver.resolve_path(self.path)
            actual_driver._create_impl(resolved_path, self.content or "")
        else:
            # Regular driver
            actual_driver.create(self.path, self.content or "")
        return FileResult(path=self.path, success=True, request=self)

    def _handle_exists_operation(self, actual_driver: Any) -> FileResult:
        """Handle file exists check operation."""
        # Check if it's a mock driver with mock file system
        if hasattr(actual_driver, 'contents') and hasattr(actual_driver, 'files'):
            # MockFileDriver - use mock filesystem
            exists = actual_driver._exists_impl(self.path)
        else:
            # Regular driver
            exists = actual_driver.exists(self.path)
        return FileResult(path=self.path, success=True, exists=exists, request=self)

    def _handle_move_copy_operations(self, actual_driver: Any) -> FileResult:
        """Handle move and copy operations that require source and destination paths."""
        if self.op == FileOpType.MOVE:
            actual_driver.move(self.path, self.dst_path)
        elif self.op == FileOpType.COPY:
            actual_driver.copy(self.path, self.dst_path)
        elif self.op == FileOpType.COPYTREE:
            actual_driver.copytree(self.path, self.dst_path)
        elif self.op == FileOpType.MOVETREE:
            actual_driver.movetree(self.path, self.dst_path)

        return FileResult(path=self.dst_path, success=True, request=self)

    def _handle_single_path_operations(self, actual_driver: Any) -> FileResult:
        """Handle operations that work on a single path."""
        if self.op == FileOpType.REMOVE:
            actual_driver.remove(self.path)
        elif self.op == FileOpType.RMTREE:
            actual_driver.rmtree(self.path)
        elif self.op == FileOpType.MKDIR:
            actual_driver.mkdir(self.path)
        elif self.op == FileOpType.TOUCH:
            actual_driver.touch(self.path)

        return FileResult(path=self.path, success=True, request=self)

    def _handle_file_error(self, e: Exception) -> FileResult:
        """Handle file operation errors."""
        from src.domain.exceptions.error_codes import ErrorSuggestion, classify_error
        error_code = classify_error(e, "file operation")
        suggestion = ErrorSuggestion.get_suggestion(error_code)
        formatted_error = f"File operation failed: {e}\nError Code: {error_code.value}\nSuggestion: {suggestion}"

        # If allow_failure is True, return a failure result instead of raising exception
        if self.allow_failure:
            return FileResult(
                path=self.path,
                success=False,
                error_message=formatted_error,
                request=self
            )

        from src.domain.exceptions.composite_step_failure import CompositeStepFailureError
        raise CompositeStepFailureError(
            formatted_error,
            original_exception=e,
            error_code=error_code,
            context="file operation"
        ) from e

    def __repr__(self) -> str:
        """String representation of the request."""
        return f"<FileRequest name={self.name} op={self.op} path={self.path} dst={getattr(self, 'dst_path', None)} content={getattr(self, 'content', None)} >"
