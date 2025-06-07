"""File operation request."""
import time
from pathlib import Path
from typing import Optional, Any
from src.domain.requests.base.base_request import BaseRequest
from src.domain.constants.operation_type import OperationType
from src.domain.requests.file.file_op_type import FileOpType
from src.domain.results.file_result import FileResult


class FileRequest(BaseRequest):
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
            # Handle unified driver case using duck typing
            if hasattr(driver, '_get_cached_driver') and callable(getattr(driver, '_get_cached_driver')):
                actual_driver = driver._get_cached_driver("file_driver")
            else:
                actual_driver = driver
            
            # Execute based on operation type
            if self.op == FileOpType.READ:
                # Check if it's a mock driver with mock file system
                if hasattr(actual_driver, 'contents') and hasattr(actual_driver, 'files'):
                    # MockFileDriver - use mock filesystem
                    abs_path = actual_driver.base_dir / Path(self.path)
                    if abs_path in actual_driver.contents:
                        content = actual_driver.contents[abs_path]
                        return FileResult(content=content, path=self.path, success=True, request=self)
                    else:
                        # MockFileDriver: return empty content for non-existent files
                        return FileResult(content="", path=self.path, success=True, request=self)
                else:
                    # Regular driver - use real filesystem
                    resolved_path = actual_driver.resolve_path(self.path)
                    with resolved_path.open("r", encoding="utf-8") as f:
                        content = f.read()
                    return FileResult(content=content, path=self.path, success=True, request=self)
            
            elif self.op == FileOpType.WRITE:
                # Check if it's a mock driver with different API
                if hasattr(actual_driver, '_create_impl'):
                    # For drivers with _create_impl, resolve path first
                    resolved_path = actual_driver.resolve_path(self.path)
                    actual_driver._create_impl(resolved_path, self.content or "")
                else:
                    # Regular driver
                    actual_driver.create(self.path, self.content or "")
                return FileResult(path=self.path, success=True, request=self)
            
            elif self.op == FileOpType.EXISTS:
                # Check if it's a mock driver with mock file system
                if hasattr(actual_driver, 'contents') and hasattr(actual_driver, 'files'):
                    # MockFileDriver - use mock filesystem
                    exists = actual_driver._exists_impl(self.path)
                else:
                    # Regular driver
                    exists = actual_driver.exists(self.path)
                return FileResult(path=self.path, success=True, exists=exists, request=self)
            
            elif self.op == FileOpType.MOVE:
                actual_driver.move(self.path, self.dst_path)
                return FileResult(path=self.dst_path, success=True, request=self)
            
            elif self.op == FileOpType.COPY:
                actual_driver.copy(self.path, self.dst_path)
                return FileResult(path=self.dst_path, success=True, request=self)
            
            elif self.op == FileOpType.COPYTREE:
                actual_driver.copytree(self.path, self.dst_path)
                return FileResult(path=self.dst_path, success=True, request=self)
            
            elif self.op == FileOpType.REMOVE:
                actual_driver.remove(self.path)
                return FileResult(path=self.path, success=True, request=self)
            
            elif self.op == FileOpType.RMTREE:
                actual_driver.rmtree(self.path)
                return FileResult(path=self.path, success=True, request=self)
            
            elif self.op == FileOpType.MKDIR:
                actual_driver.mkdir(self.path)
                return FileResult(path=self.path, success=True, request=self)
            
            elif self.op == FileOpType.TOUCH:
                actual_driver.touch(self.path)
                return FileResult(path=self.path, success=True, request=self)
            
            else:
                raise ValueError(f"Unsupported file operation: {self.op}")
                
        except Exception as e:
            # If allow_failure is True, return a failure result instead of raising exception
            if self.allow_failure:
                return FileResult(
                    path=self.path, 
                    success=False, 
                    error_message=f"FileRequest failed: {str(e)}",
                    request=self
                )
            else:
                raise RuntimeError(f"FileRequest failed: {str(e)}")

    def __repr__(self) -> str:
        """String representation of the request."""
        return f"<FileRequest name={self.name} op={self.op} path={self.path} dst={getattr(self, 'dst_path', None)} content={getattr(self, 'content', None)} >"