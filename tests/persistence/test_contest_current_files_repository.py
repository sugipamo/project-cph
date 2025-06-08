"""Tests for ContestCurrentFilesRepository."""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.persistence.sqlite.repositories.contest_current_files_repository import (
    ContestCurrentFile,
    ContestCurrentFilesRepository,
)


class TestContestCurrentFilesRepository:
    """Test ContestCurrentFilesRepository functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = MagicMock()
        self.repository = ContestCurrentFilesRepository(self.mock_manager)
        # Set the manager attribute directly since the base class expects it
        self.repository.manager = self.mock_manager

    def test_track_file_success(self):
        """Test successful file tracking."""
        # Mock successful execution
        self.mock_manager.execute_query.return_value = None

        result = self.repository.track_file(
            language_name="python",
            contest_name="abc123",
            problem_name="a",
            relative_path="main.py",
            source_type="template",
            source_path="/path/to/template/main.py"
        )

        assert result is True
        self.mock_manager.execute_query.assert_called_once()

        # Check the SQL query and parameters
        call_args = self.mock_manager.execute_query.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert "INSERT OR REPLACE INTO contest_current_files" in sql
        assert params == ("python", "abc123", "a", "main.py", "template", "/path/to/template/main.py")

    def test_track_file_failure(self):
        """Test file tracking failure."""
        # Mock exception during execution
        self.mock_manager.execute_query.side_effect = Exception("Database error")

        result = self.repository.track_file(
            language_name="python",
            contest_name="abc123",
            problem_name="a",
            relative_path="main.py",
            source_type="template",
            source_path="/path/to/template/main.py"
        )

        assert result is False

    def test_get_files_for_contest_success(self):
        """Test successful retrieval of files for contest."""
        # Mock database response
        mock_rows = [
            (1, "python", "abc123", "a", "main.py", "template", "/path/to/template/main.py",
             "2023-01-01 10:00:00", "2023-01-01 11:00:00"),
            (2, "python", "abc123", "a", "input.txt", "stock", "/path/to/stock/input.txt",
             "2023-01-01 10:00:00", "2023-01-01 11:00:00")
        ]
        self.mock_manager.fetch_all.return_value = mock_rows

        result = self.repository.get_files_for_contest("python", "abc123", "a")

        assert len(result) == 2
        assert isinstance(result[0], ContestCurrentFile)
        assert result[0].id == 1
        assert result[0].language_name == "python"
        assert result[0].contest_name == "abc123"
        assert result[0].problem_name == "a"
        assert result[0].relative_path == "main.py"
        assert result[0].source_type == "template"
        assert result[0].source_path == "/path/to/template/main.py"

        assert result[1].relative_path == "input.txt"
        assert result[1].source_type == "stock"

    def test_get_files_for_contest_failure(self):
        """Test get files failure."""
        # Mock exception during fetch
        self.mock_manager.fetch_all.side_effect = Exception("Database error")

        result = self.repository.get_files_for_contest("python", "abc123", "a")

        assert result == []

    def test_clear_contest_tracking_success(self):
        """Test successful clearing of contest tracking."""
        self.mock_manager.execute_query.return_value = None

        result = self.repository.clear_contest_tracking("python", "abc123", "a")

        assert result is True
        self.mock_manager.execute_query.assert_called_once()

        # Check the SQL query
        call_args = self.mock_manager.execute_query.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert "DELETE FROM contest_current_files" in sql
        assert params == ("python", "abc123", "a")

    def test_clear_contest_tracking_failure(self):
        """Test clear contest tracking failure."""
        self.mock_manager.execute_query.side_effect = Exception("Database error")

        result = self.repository.clear_contest_tracking("python", "abc123", "a")

        assert result is False

    def test_get_file_paths_by_source_type_success(self):
        """Test successful retrieval of file paths by source type."""
        mock_rows = [("main.py",), ("utils.py",)]
        self.mock_manager.fetch_all.return_value = mock_rows

        result = self.repository.get_file_paths_by_source_type(
            "python", "abc123", "a", "template"
        )

        assert result == ["main.py", "utils.py"]

        # Check the SQL query
        call_args = self.mock_manager.fetch_all.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert "source_type = ?" in sql
        assert params == ("python", "abc123", "a", "template")

    def test_get_file_paths_by_source_type_failure(self):
        """Test get file paths failure."""
        self.mock_manager.fetch_all.side_effect = Exception("Database error")

        result = self.repository.get_file_paths_by_source_type(
            "python", "abc123", "a", "template"
        )

        assert result == []

    def test_has_files_for_contest_true(self):
        """Test has_files_for_contest returns True when files exist."""
        self.mock_manager.fetch_one.return_value = (5,)  # COUNT(*) = 5

        result = self.repository.has_files_for_contest("python", "abc123", "a")

        assert result is True

        # Check the SQL query
        call_args = self.mock_manager.fetch_one.call_args
        sql = call_args[0][0]
        assert "COUNT(*)" in sql

    def test_has_files_for_contest_false(self):
        """Test has_files_for_contest returns False when no files exist."""
        self.mock_manager.fetch_one.return_value = (0,)  # COUNT(*) = 0

        result = self.repository.has_files_for_contest("python", "abc123", "a")

        assert result is False

    def test_has_files_for_contest_no_result(self):
        """Test has_files_for_contest when no result returned."""
        self.mock_manager.fetch_one.return_value = None

        result = self.repository.has_files_for_contest("python", "abc123", "a")

        assert result is False

    def test_has_files_for_contest_failure(self):
        """Test has_files_for_contest failure."""
        self.mock_manager.fetch_one.side_effect = Exception("Database error")

        result = self.repository.has_files_for_contest("python", "abc123", "a")

        assert result is False

    def test_track_multiple_files_success(self):
        """Test successful tracking of multiple files."""
        files = [
            ("python", "abc123", "a", "main.py", "template", "/path/to/template/main.py"),
            ("python", "abc123", "a", "input.txt", "stock", "/path/to/stock/input.txt")
        ]

        self.mock_manager.execute_many.return_value = None

        result = self.repository.track_multiple_files(files)

        assert result is True
        self.mock_manager.execute_many.assert_called_once()

        # Check the SQL query and data
        call_args = self.mock_manager.execute_many.call_args
        sql = call_args[0][0]
        data = call_args[0][1]

        assert "INSERT OR REPLACE INTO contest_current_files" in sql
        assert data == files

    def test_track_multiple_files_failure(self):
        """Test track multiple files failure."""
        files = [("python", "abc123", "a", "main.py", "template", "/path/to/template/main.py")]

        self.mock_manager.execute_many.side_effect = Exception("Database error")

        result = self.repository.track_multiple_files(files)

        assert result is False

    def test_abstract_method_implementations(self):
        """Test that abstract methods are implemented (even if as pass)."""
        # These should not raise NotImplementedError
        self.repository.create(None)
        self.repository.find_by_id(1)
        self.repository.find_all()
        self.repository.update(None)
        self.repository.delete(1)


class TestContestCurrentFile:
    """Test ContestCurrentFile dataclass."""

    def test_contest_current_file_creation(self):
        """Test ContestCurrentFile creation."""
        now = datetime.now()

        file_obj = ContestCurrentFile(
            id=1,
            language_name="python",
            contest_name="abc123",
            problem_name="a",
            relative_path="main.py",
            source_type="template",
            source_path="/path/to/template/main.py",
            created_at=now,
            updated_at=now
        )

        assert file_obj.id == 1
        assert file_obj.language_name == "python"
        assert file_obj.contest_name == "abc123"
        assert file_obj.problem_name == "a"
        assert file_obj.relative_path == "main.py"
        assert file_obj.source_type == "template"
        assert file_obj.source_path == "/path/to/template/main.py"
        assert file_obj.created_at == now
        assert file_obj.updated_at == now

    def test_contest_current_file_defaults(self):
        """Test ContestCurrentFile with default values."""
        file_obj = ContestCurrentFile(
            id=None,
            language_name="python",
            contest_name="abc123",
            problem_name="a",
            relative_path="main.py",
            source_type="template",
            source_path="/path/to/template/main.py"
        )

        assert file_obj.id is None
        assert file_obj.created_at is None
        assert file_obj.updated_at is None
        assert file_obj.language_name == "python"
