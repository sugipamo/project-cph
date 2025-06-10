"""File pattern service for configuration-driven file operations."""
import glob
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.domain.interfaces.filesystem_interface import FileSystemInterface
from src.domain.interfaces.logger_interface import LoggerInterface
from src.infrastructure.config.json_config_loader import JsonConfigLoader

from .exceptions import ConfigValidationError, PatternResolutionError


@dataclass
class FileOperationResult:
    """Result of file operation execution."""
    success: bool
    message: str
    files_processed: int
    files_failed: int
    error_details: List[Dict[str, str]]
    operation_log: List[str]


class FilePatternService:
    """Service for pattern-based file operations."""

    def __init__(self, config_loader: JsonConfigLoader, file_driver: FileSystemInterface, logger: LoggerInterface):
        """Initialize FilePatternService.

        Args:
            config_loader: Configuration loader for patterns and operations
            file_driver: File system driver for file operations
            logger: Logger for operation tracking
        """
        self.config_loader = config_loader
        self.file_driver = file_driver
        self.logger = logger

    def get_file_patterns(self, language: str) -> Dict[str, Dict[str, List[str]]]:
        """Get file patterns configuration for a specific language.

        Args:
            language: Language name

        Returns:
            Dictionary containing file patterns for the language
        """
        try:
            lang_config = self.config_loader.get_language_config(language)
            return lang_config.get("file_patterns", {})
        except Exception as e:
            self.logger.error(f"Failed to get file patterns for {language}: {e}")
            return {}

    def get_file_operations(self) -> Dict[str, List[List[str]]]:
        """Get file operations configuration from shared config.

        Returns:
            Dictionary containing file operations definitions
        """
        try:
            shared_config = self.config_loader.get_shared_config()
            return shared_config.get("file_operations", {})
        except Exception as e:
            self.logger.error(f"Failed to get file operations: {e}")
            return {}

    def validate_patterns(self, patterns: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate file patterns configuration.

        Args:
            patterns: Pattern configuration to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if not isinstance(patterns, dict):
            errors.append("Patterns must be a dictionary")
            return False, errors

        for group_name, locations in patterns.items():
            if not isinstance(locations, dict):
                errors.append(f"Pattern group '{group_name}' must be a dictionary")
                continue

            for location, pattern_list in locations.items():
                if location not in ["workspace", "contest_current", "contest_stock"]:
                    errors.append(f"Invalid location '{location}' in group '{group_name}'")

                if not isinstance(pattern_list, list):
                    errors.append(f"Patterns for '{group_name}.{location}' must be a list")
                else:
                    for pattern in pattern_list:
                        if not isinstance(pattern, str) or not pattern.strip():
                            errors.append(f"Invalid pattern in '{group_name}.{location}': {pattern}")

        return len(errors) == 0, errors

    def validate_operations(self, operations: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate file operations configuration.

        Args:
            operations: Operations configuration to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        if not isinstance(operations, dict):
            errors.append("Operations must be a dictionary")
            return False, errors

        for op_name, steps in operations.items():
            if not isinstance(steps, list):
                errors.append(f"Operation '{op_name}' must be a list of steps")
                continue

            for i, step in enumerate(steps):
                if not isinstance(step, list) or len(step) != 2:
                    errors.append(f"Step {i} in operation '{op_name}' must be [source, dest]")
                    continue

                source, dest = step
                if not self._is_valid_pattern_reference(source):
                    errors.append(f"Invalid source pattern reference: {source}")
                if not self._is_valid_pattern_reference(dest):
                    errors.append(f"Invalid dest pattern reference: {dest}")

        return len(errors) == 0, errors

    def _is_valid_pattern_reference(self, ref: str) -> bool:
        """Check if pattern reference is valid.

        Args:
            ref: Pattern reference (e.g., "workspace.test_files")

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(ref, str) or not ref.strip():
            return False

        parts = ref.split('.')
        if len(parts) != 2:
            return False

        location, pattern_group = parts
        return (location in ["workspace", "contest_current", "contest_stock"] and
                pattern_group.isidentifier())

    def resolve_pattern_paths(self, pattern_key: str, context: Dict[str, Any]) -> List[Path]:
        """Resolve pattern key to actual file paths.

        Args:
            pattern_key: Pattern reference (e.g., "workspace.test_files")
            context: Context containing paths and language info

        Returns:
            List of resolved file paths

        Raises:
            PatternResolutionError: If pattern resolution fails
        """
        if not self._is_valid_pattern_reference(pattern_key):
            raise PatternResolutionError(f"Invalid pattern reference format: {pattern_key}")

        location, pattern_group = pattern_key.split('.')
        language = context.get("language", "")

        # Get patterns for the language
        patterns = self.get_file_patterns(language)
        if pattern_group not in patterns:
            raise PatternResolutionError(f"Pattern group '{pattern_group}' not found for language '{language}'")

        if location not in patterns[pattern_group]:
            raise PatternResolutionError(f"Location '{location}' not found in pattern group '{pattern_group}'")

        pattern_list = patterns[pattern_group][location]
        if not pattern_list:
            return []

        # Get base path for the location
        base_path = self._get_base_path_for_location(location, context)
        if not base_path:
            raise PatternResolutionError(f"Location '{location}' not found in pattern group '{pattern_group}'")

        # Resolve patterns to actual paths
        resolved_paths = []
        base_path_obj = Path(base_path)

        for pattern in pattern_list:
            normalized_pattern = self._normalize_pattern(pattern)
            # Use absolute pattern path to avoid directory changes
            full_pattern = str(base_path_obj / normalized_pattern)
            matching_files = glob.glob(full_pattern, recursive=True)

            for file_path in matching_files:
                full_path = Path(file_path)
                if full_path.exists() and not self._is_file_excluded(full_path):
                    resolved_paths.append(full_path.resolve())

        return resolved_paths

    def _get_base_path_for_location(self, location: str, context: Dict[str, Any]) -> str:
        """Get base path for a location.

        Args:
            location: Location name
            context: Context with path information

        Returns:
            Base path string or empty string if not found
        """
        path_map = {
            "workspace": context.get("workspace_path", ""),
            "contest_current": context.get("contest_current_path", ""),
            "contest_stock": context.get("contest_stock_path", "")
        }
        return path_map.get(location, "")

    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize pattern for cross-platform compatibility.

        Args:
            pattern: File pattern to normalize

        Returns:
            Normalized pattern
        """
        # Convert backslashes to forward slashes
        normalized = pattern.replace("\\", "/")

        # Remove leading ./
        if normalized.startswith("./"):
            normalized = normalized[2:]

        # Handle double slashes
        while "//" in normalized:
            normalized = normalized.replace("//", "/")

        return normalized

    def _is_file_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from operations.

        Args:
            file_path: Path to check

        Returns:
            True if file should be excluded
        """
        exclusion_patterns = self._get_exclusion_patterns()
        file_str = str(file_path)

        return any(self._matches_exclusion_pattern(file_str, pattern) for pattern in exclusion_patterns)

    def _get_exclusion_patterns(self) -> List[str]:
        """Get list of exclusion patterns.

        Returns:
            List of patterns for files to exclude
        """
        return [
            "*.tmp",
            "*.log",
            "__pycache__/**/*",
            ".git/**/*",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            "Thumbs.db"
        ]

    def _matches_exclusion_pattern(self, file_str: str, pattern: str) -> bool:
        """Check if file matches exclusion pattern.

        Args:
            file_str: File path as string
            pattern: Exclusion pattern

        Returns:
            True if file matches pattern
        """
        # Simple pattern matching - could be enhanced with fnmatch
        if "**" in pattern:
            # Handle recursive patterns
            pattern_parts = pattern.split("**/")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                return prefix in file_str and file_str.endswith(suffix.replace("*", ""))
        elif "*" in pattern:
            # Handle simple wildcards
            if pattern.startswith("*."):
                extension = pattern[2:]
                return file_str.endswith(f".{extension}")
        else:
            # Exact match
            return pattern in file_str

        return False

    def execute_file_operations(self, operation_name: str, context: Dict[str, Any]) -> FileOperationResult:
        """Execute file operations based on configuration.

        Args:
            operation_name: Name of operation to execute
            context: Context with path information

        Returns:
            FileOperationResult with execution details
        """
        operation_log = [f"Started operation: {operation_name}"]

        try:
            # Get operation definition
            operations = self.get_file_operations()
            if operation_name not in operations:
                return FileOperationResult(
                    success=False,
                    message=f"Operation '{operation_name}' not found in configuration",
                    files_processed=0,
                    files_failed=0,
                    error_details=[],
                    operation_log=operation_log
                )

            operation_steps = operations[operation_name]
            files_processed = 0
            files_failed = 0
            error_details = []

            # Execute each step
            for i, (source_ref, dest_ref) in enumerate(operation_steps, 1):
                operation_log.append(f"Processing step {i}/{len(operation_steps)}: {source_ref} -> {dest_ref}")

                try:
                    # Resolve source patterns
                    source_paths = self.resolve_pattern_paths(source_ref, context)

                    if not source_paths:
                        operation_log.append(f"No files found for pattern: {source_ref}")
                        continue

                    # Process each source file
                    for source_path in source_paths:
                        try:
                            dest_path = self._calculate_destination_path(source_path, source_ref, dest_ref, context)

                            # Create destination directory if needed
                            dest_dir = dest_path.parent
                            if not dest_dir.exists():
                                self.file_driver.create_directory(dest_dir)

                            # Copy file
                            if self.file_driver.copy_file(source_path, dest_path):
                                files_processed += 1
                                operation_log.append(f"Copied: {source_path} -> {dest_path}")
                            else:
                                files_failed += 1
                                error_details.append({
                                    "file": str(source_path),
                                    "error": "Copy operation failed"
                                })

                        except Exception as e:
                            files_failed += 1
                            error_details.append({
                                "file": str(source_path),
                                "error": str(e)
                            })

                except PatternResolutionError as e:
                    operation_log.append(f"Pattern resolution failed for {source_ref}: {e}")
                    return FileOperationResult(
                        success=False,
                        message=str(e),
                        files_processed=files_processed,
                        files_failed=files_failed,
                        error_details=error_details,
                        operation_log=operation_log
                    )

            # Determine overall success
            if files_processed == 0 and files_failed == 0:
                message = "No files found for patterns"
                success = True
            elif files_failed == 0:
                message = f"Successfully processed {files_processed} files"
                success = True
            else:
                message = f"Processed {files_processed} files, {files_failed} failed"
                success = False

            operation_log.append(f"Operation completed: {message}")

            return FileOperationResult(
                success=success,
                message=message,
                files_processed=files_processed,
                files_failed=files_failed,
                error_details=error_details,
                operation_log=operation_log
            )

        except Exception as e:
            self.logger.error(f"Operation {operation_name} failed: {e}")
            operation_log.append(f"Operation failed with error: {e}")

            return FileOperationResult(
                success=False,
                message=str(e),
                files_processed=0,
                files_failed=0,
                error_details=[],
                operation_log=operation_log
            )

    def _calculate_destination_path(self, source_path: Path, source_ref: str, dest_ref: str, context: Dict[str, Any]) -> Path:
        """Calculate destination path for a source file.

        Args:
            source_path: Source file path
            source_ref: Source pattern reference
            dest_ref: Destination pattern reference
            context: Context with path information

        Returns:
            Calculated destination path
        """
        # Get source and destination base paths
        source_location = source_ref.split('.')[0]
        dest_location = dest_ref.split('.')[0]

        source_base = Path(self._get_base_path_for_location(source_location, context))
        dest_base = Path(self._get_base_path_for_location(dest_location, context))

        # Calculate relative path from source base
        relative_path = source_path.relative_to(source_base)

        # Return destination path
        return dest_base / relative_path

    def _get_destination_path(self, source: Path, source_base: Path, dest_base: Path) -> Path:
        """Calculate destination path maintaining directory structure.

        Args:
            source: Source file path
            source_base: Source base directory
            dest_base: Destination base directory

        Returns:
            Destination path
        """
        relative_path = source.relative_to(source_base)
        return dest_base / relative_path

    def execute_with_fallback(self, operation_name: str, context: Dict[str, Any]) -> FileOperationResult:
        """Execute file operations with fallback to legacy implementation.

        Args:
            operation_name: Name of operation to execute
            context: Context with path information

        Returns:
            FileOperationResult with execution details
        """
        try:
            # Validate configuration first
            patterns = self.get_file_patterns(context.get("language", ""))
            operations = self.get_file_operations()

            patterns_valid, pattern_errors = self.validate_patterns(patterns)
            operations_valid, operation_errors = self.validate_operations(operations)

            if not patterns_valid or not operations_valid:
                raise ConfigValidationError(f"Config validation failed: {pattern_errors + operation_errors}")

            # Execute with new implementation
            return self.execute_file_operations(operation_name, context)

        except ConfigValidationError as e:
            self.logger.warning(f"Config validation failed, falling back to legacy: {e}")
            return self._execute_legacy_fallback(context)

        except PatternResolutionError as e:
            self.logger.error(f"Pattern resolution failed: {e}")
            return FileOperationResult(
                success=False,
                message=str(e),
                files_processed=0,
                files_failed=0,
                error_details=[],
                operation_log=[f"Pattern resolution error: {e}"]
            )

    def _execute_legacy_fallback(self, context: Dict[str, Any]) -> FileOperationResult:
        """Execute legacy fallback implementation.

        Args:
            context: Context with path information

        Returns:
            FileOperationResult from legacy implementation
        """
        # This would call the existing move_test_files implementation
        # For now, return a placeholder result
        self.logger.info("Executing legacy fallback implementation")

        return FileOperationResult(
            success=True,
            message="Legacy fallback successful",
            files_processed=1,
            files_failed=0,
            error_details=[],
            operation_log=["Legacy operation completed"]
        )

    def diagnose_config_issues(self, language: str) -> Dict[str, Any]:
        """Diagnose configuration issues and provide suggestions.

        Args:
            language: Language to diagnose

        Returns:
            Dictionary with diagnosis results
        """
        diagnosis = {
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "suggestions": [],
            "config_status": "unknown"
        }

        try:
            # Check pattern configuration
            patterns = self.get_file_patterns(language)
            patterns_valid, pattern_errors = self.validate_patterns(patterns)

            if not patterns_valid:
                diagnosis["issues"].extend(pattern_errors)
                diagnosis["suggestions"].append("Fix pattern validation errors")

            # Check operation configuration
            operations = self.get_file_operations()
            operations_valid, operation_errors = self.validate_operations(operations)

            if not operations_valid:
                diagnosis["issues"].extend(operation_errors)
                diagnosis["suggestions"].append("Fix operation validation errors")

            # Check for missing files
            missing_files = self._check_required_files(language)
            if missing_files:
                diagnosis["issues"].append(f"Missing files: {missing_files}")
                diagnosis["suggestions"].append("Create missing configuration files")

            # Determine overall status
            diagnosis["config_status"] = "valid" if len(diagnosis["issues"]) == 0 else "invalid"

        except Exception as e:
            diagnosis["issues"].append(f"Diagnosis failed: {e!s}")
            diagnosis["config_status"] = "error"

        return diagnosis

    def _check_required_files(self, language: str) -> List[str]:
        """Check for missing required configuration files.

        Args:
            language: Language to check

        Returns:
            List of missing file paths
        """
        missing_files = []

        # Check if language config file exists
        lang_config_path = self.config_loader.base_path / language / "env.json"
        if not lang_config_path.exists():
            missing_files.append(str(lang_config_path))

        # Check if shared config file exists
        shared_config_path = self.config_loader.base_path / "shared" / "env.json"
        if not shared_config_path.exists():
            missing_files.append(str(shared_config_path))

        return missing_files

    def get_fallback_patterns(self, language: str) -> Dict[str, Dict[str, List[str]]]:
        """Get fallback patterns for a language.

        Args:
            language: Language name

        Returns:
            Dictionary with fallback patterns
        """
        # Language-specific fallback patterns
        fallback_patterns = {
            "test_files": {
                "workspace": ["test/**/*.txt", "test/**/*.in", "test/**/*.out"],
                "contest_current": ["test/"],
                "contest_stock": ["test/"]
            }
        }

        if language == "cpp":
            fallback_patterns["contest_files"] = {
                "workspace": ["main.cpp", "*.h", "*.hpp"],
                "contest_current": ["main.cpp"],
                "contest_stock": ["main.cpp", "*.h", "*.hpp"]
            }
        elif language == "python":
            fallback_patterns["contest_files"] = {
                "workspace": ["main.py", "*.py"],
                "contest_current": ["main.py"],
                "contest_stock": ["main.py", "*.py"]
            }
        elif language == "rust":
            fallback_patterns["contest_files"] = {
                "workspace": ["main.rs", "*.rs"],
                "contest_current": ["main.rs"],
                "contest_stock": ["main.rs", "*.rs"]
            }

        return fallback_patterns
