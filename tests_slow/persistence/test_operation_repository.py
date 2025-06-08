"""Tests for OperationRepository - operation history management."""
import os
import tempfile
from datetime import datetime

import pytest

from src.infrastructure.persistence.sqlite.repositories.operation_repository import (
    Operation,
    OperationRepository,
)
from src.infrastructure.persistence.sqlite.sqlite_manager import SQLiteManager


class TestOperationRepository:
    """Test OperationRepository functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sqlite_manager(self, temp_db_path):
        """Create SQLiteManager with temporary database."""
        return SQLiteManager(temp_db_path)

    @pytest.fixture
    def operation_repo(self, sqlite_manager):
        """Create OperationRepository."""
        return OperationRepository(sqlite_manager)

    @pytest.fixture
    def sample_operation(self):
        """Create sample operation for testing."""
        return Operation(
            command="test",
            language="python",
            contest_name="abc123",
            problem_name="a",
            env_type="local",
            result="success",
            execution_time_ms=1500,
            stdout="Test output",
            stderr="",
            return_code=0,
            details={"test_key": "test_value"}
        )

    def test_create_operation(self, operation_repo, sample_operation):
        """Test creating a new operation."""
        created_op = operation_repo.create(sample_operation)

        assert created_op.id is not None
        assert created_op.command == "test"
        assert created_op.language == "python"
        assert created_op.contest_name == "abc123"
        assert created_op.problem_name == "a"
        assert created_op.env_type == "local"
        assert created_op.result == "success"
        assert created_op.execution_time_ms == 1500
        assert created_op.stdout == "Test output"
        assert created_op.stderr == ""
        assert created_op.return_code == 0
        assert created_op.details == {"test_key": "test_value"}
        assert isinstance(created_op.timestamp, datetime)

    def test_create_operation_with_explicit_timestamp(self, operation_repo):
        """Test creating operation with explicit timestamp."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        operation = Operation(
            command="build",
            timestamp=timestamp,
            language="cpp"
        )

        created_op = operation_repo.create(operation)
        assert created_op.timestamp == timestamp

    def test_create_operation_with_none_details(self, operation_repo):
        """Test creating operation with None details."""
        operation = Operation(
            command="test",
            details=None
        )

        created_op = operation_repo.create(operation)
        assert created_op.details is None

    def test_find_by_id_existing(self, operation_repo, sample_operation):
        """Test finding operation by existing ID."""
        created_op = operation_repo.create(sample_operation)
        found_op = operation_repo.find_by_id(created_op.id)

        assert found_op is not None
        assert found_op.id == created_op.id
        assert found_op.command == sample_operation.command
        assert found_op.language == sample_operation.language

    def test_find_by_id_nonexistent(self, operation_repo):
        """Test finding operation by non-existent ID."""
        found_op = operation_repo.find_by_id(99999)
        assert found_op is None

    def test_find_all_empty(self, operation_repo):
        """Test finding all operations when database is empty."""
        operations = operation_repo.find_all()
        assert operations == []

    def test_find_all_with_data(self, operation_repo):
        """Test finding all operations with data."""
        # Create test operations
        op1 = Operation(command="test", language="python")
        op2 = Operation(command="build", language="cpp")
        op3 = Operation(command="run", language="java")

        operation_repo.create(op1)
        operation_repo.create(op2)
        operation_repo.create(op3)

        operations = operation_repo.find_all()
        assert len(operations) == 3
        # Should be ordered by timestamp DESC (most recent first)
        assert operations[0].command == "run"  # Last created
        assert operations[1].command == "build"
        assert operations[2].command == "test"

    def test_find_all_with_pagination(self, operation_repo):
        """Test pagination in find_all."""
        # Create 5 operations
        for i in range(5):
            op = Operation(command=f"cmd{i}", language="python")
            operation_repo.create(op)

        # Test limit
        limited = operation_repo.find_all(limit=3)
        assert len(limited) == 3

        # Test limit with offset
        offset_ops = operation_repo.find_all(limit=2, offset=2)
        assert len(offset_ops) == 2

        # Test that offset works correctly
        all_ops = operation_repo.find_all()
        assert offset_ops[0].id == all_ops[2].id
        assert offset_ops[1].id == all_ops[3].id

    def test_find_by_command(self, operation_repo):
        """Test finding operations by command."""
        # Create operations with different commands
        operation_repo.create(Operation(command="test", language="python"))
        operation_repo.create(Operation(command="build", language="cpp"))
        operation_repo.create(Operation(command="test", language="java"))
        operation_repo.create(Operation(command="run", language="python"))

        test_ops = operation_repo.find_by_command("test")
        assert len(test_ops) == 2
        assert all(op.command == "test" for op in test_ops)

        build_ops = operation_repo.find_by_command("build")
        assert len(build_ops) == 1
        assert build_ops[0].command == "build"

        # Test nonexistent command
        none_ops = operation_repo.find_by_command("nonexistent")
        assert len(none_ops) == 0

    def test_find_by_command_with_limit(self, operation_repo):
        """Test finding operations by command with limit."""
        # Create multiple operations with same command
        for i in range(5):
            operation_repo.create(Operation(command="test", language=f"lang{i}"))

        limited_ops = operation_repo.find_by_command("test", limit=3)
        assert len(limited_ops) == 3

    def test_find_by_contest_with_problem(self, operation_repo):
        """Test finding operations by contest and problem."""
        # Create operations for different contests/problems
        operation_repo.create(Operation(command="test", contest_name="abc123", problem_name="a"))
        operation_repo.create(Operation(command="build", contest_name="abc123", problem_name="b"))
        operation_repo.create(Operation(command="test", contest_name="abc123", problem_name="a"))
        operation_repo.create(Operation(command="run", contest_name="def456", problem_name="a"))

        ops = operation_repo.find_by_contest("abc123", "a")
        assert len(ops) == 2
        assert all(op.contest_name == "abc123" and op.problem_name == "a" for op in ops)

    def test_find_by_contest_without_problem(self, operation_repo):
        """Test finding operations by contest only."""
        # Create operations for different contests
        operation_repo.create(Operation(command="test", contest_name="abc123", problem_name="a"))
        operation_repo.create(Operation(command="build", contest_name="abc123", problem_name="b"))
        operation_repo.create(Operation(command="run", contest_name="def456", problem_name="a"))

        ops = operation_repo.find_by_contest("abc123")
        assert len(ops) == 2
        assert all(op.contest_name == "abc123" for op in ops)

    def test_find_by_language(self, operation_repo):
        """Test finding operations by language."""
        # Create operations with different languages
        operation_repo.create(Operation(command="test", language="python"))
        operation_repo.create(Operation(command="build", language="cpp"))
        operation_repo.create(Operation(command="run", language="python"))
        operation_repo.create(Operation(command="test", language="java"))

        python_ops = operation_repo.find_by_language("python")
        assert len(python_ops) == 2
        assert all(op.language == "python" for op in python_ops)

        cpp_ops = operation_repo.find_by_language("cpp")
        assert len(cpp_ops) == 1
        assert cpp_ops[0].language == "cpp"

    def test_find_by_language_with_limit(self, operation_repo):
        """Test finding operations by language with limit."""
        # Create multiple operations with same language
        for i in range(4):
            operation_repo.create(Operation(command=f"cmd{i}", language="python"))

        limited_ops = operation_repo.find_by_language("python", limit=2)
        assert len(limited_ops) == 2

    def test_get_recent_operations(self, operation_repo):
        """Test getting recent operations."""
        # Create operations
        for i in range(15):
            operation_repo.create(Operation(command=f"cmd{i}", language="python"))

        # Default limit is 10
        recent = operation_repo.get_recent_operations()
        assert len(recent) == 10

        # Custom limit
        recent_5 = operation_repo.get_recent_operations(limit=5)
        assert len(recent_5) == 5

    def test_get_statistics_empty(self, operation_repo):
        """Test statistics on empty database."""
        stats = operation_repo.get_statistics()

        assert stats["total_operations"] == 0
        assert stats["successful_operations"] == 0
        assert stats["success_rate"] == 0
        assert stats["language_usage"] == []
        assert stats["command_usage"] == []

    def test_get_statistics_with_data(self, operation_repo):
        """Test statistics with data."""
        # Create test operations
        operation_repo.create(Operation(command="test", language="python", result="success"))
        operation_repo.create(Operation(command="build", language="python", result="failure"))
        operation_repo.create(Operation(command="test", language="cpp", result="success"))
        operation_repo.create(Operation(command="run", language="python", result="success"))
        operation_repo.create(Operation(command="test", language="java", result="success"))

        stats = operation_repo.get_statistics()

        assert stats["total_operations"] == 5
        assert stats["successful_operations"] == 4
        assert stats["success_rate"] == 80.0

        # Check language usage (should be sorted by count DESC)
        lang_usage = stats["language_usage"]
        assert len(lang_usage) == 3
        assert lang_usage[0]["language"] == "python"
        assert lang_usage[0]["count"] == 3

        # Check command usage (should be sorted by count DESC)
        cmd_usage = stats["command_usage"]
        assert len(cmd_usage) == 3
        assert cmd_usage[0]["command"] == "test"
        assert cmd_usage[0]["count"] == 3

    def test_update_operation(self, operation_repo, sample_operation):
        """Test updating an existing operation."""
        created_op = operation_repo.create(sample_operation)

        # Modify the operation
        created_op.result = "failure"
        created_op.stderr = "Error occurred"
        created_op.return_code = 1
        created_op.details = {"error": "test error"}

        # Update it
        updated_op = operation_repo.update(created_op)

        # Verify update
        assert updated_op.result == "failure"
        assert updated_op.stderr == "Error occurred"
        assert updated_op.return_code == 1
        assert updated_op.details == {"error": "test error"}

        # Verify from database
        found_op = operation_repo.find_by_id(created_op.id)
        assert found_op.result == "failure"
        assert found_op.stderr == "Error occurred"
        assert found_op.return_code == 1
        assert found_op.details == {"error": "test error"}

    def test_delete_operation(self, operation_repo, sample_operation):
        """Test deleting an operation."""
        created_op = operation_repo.create(sample_operation)
        operation_id = created_op.id

        # Verify it exists
        assert operation_repo.find_by_id(operation_id) is not None

        # Delete it
        result = operation_repo.delete(operation_id)
        assert result is True

        # Verify it's gone
        assert operation_repo.find_by_id(operation_id) is None

    def test_delete_nonexistent_operation(self, operation_repo):
        """Test deleting non-existent operation."""
        result = operation_repo.delete(99999)
        assert result is False

    def test_json_details_handling(self, operation_repo):
        """Test proper JSON handling for details field."""
        # Test with complex nested structure
        complex_details = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "boolean": True,
            "null": None
        }

        operation = Operation(
            command="test",
            details=complex_details
        )

        created_op = operation_repo.create(operation)
        found_op = operation_repo.find_by_id(created_op.id)

        assert found_op.details == complex_details

    def test_invalid_json_details_handling(self, operation_repo, sqlite_manager):
        """Test handling of invalid JSON in details field."""
        # Manually insert invalid JSON
        with sqlite_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO operations (command, details)
                VALUES (?, ?)
            """, ("test", "invalid json {"))

        # Should handle gracefully
        operations = operation_repo.find_all()
        assert len(operations) == 1
        assert operations[0].details == {"raw": "invalid json {"}

    def test_datetime_handling(self, operation_repo):
        """Test proper datetime serialization/deserialization."""
        specific_time = datetime(2023, 5, 15, 14, 30, 45)

        operation = Operation(
            command="test",
            timestamp=specific_time
        )

        created_op = operation_repo.create(operation)
        found_op = operation_repo.find_by_id(created_op.id)

        # Should preserve the timestamp
        assert found_op.timestamp == specific_time
