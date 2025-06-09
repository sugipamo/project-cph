"""Tests for folder path resolver pure functions."""
from pathlib import Path

import pytest

from src.workflow.preparation.core.state_definitions import WorkflowContext
from src.workflow.preparation.file.folder_path_resolver import (
    FolderArea,
    define_standard_areas,
    get_area_path,
    resolve_folder_path,
)


class TestResolveFolderPath:
    """Test resolve_folder_path function."""

    def test_resolve_with_context_variables(self):
        """Test path resolution with context variables."""
        context = WorkflowContext(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )
        path_vars = {"base_path": "/home/user"}
        template = "{base_path}/{contest_name}/{problem_name}/{language}"

        result = resolve_folder_path(template, context, path_vars)

        assert result == Path("/home/user/abc300/a/python")

    def test_resolve_with_missing_context(self):
        """Test path resolution with None context values."""
        context = WorkflowContext(
            contest_name=None,
            problem_name="a",
            language="python"
        )
        path_vars = {"base_path": "/home/user"}
        template = "{base_path}/{problem_name}/{language}"

        result = resolve_folder_path(template, context, path_vars)

        assert result == Path("/home/user/a/python")

    def test_resolve_with_language_name_alias(self):
        """Test that language_name is set to same value as language."""
        context = WorkflowContext(
            contest_name="abc300",
            problem_name="a",
            language="cpp"
        )
        path_vars = {"base_path": "/home/user"}
        template = "{base_path}/{language_name}"

        result = resolve_folder_path(template, context, path_vars)

        assert result == Path("/home/user/cpp")


class TestDefineStandardAreas:
    """Test define_standard_areas function."""

    def test_returns_all_expected_areas(self):
        """Test that all expected areas are defined."""
        areas = define_standard_areas()

        expected_areas = {
            "working_area", "archive_area", "template_area", "workspace_area"
        }
        assert set(areas.keys()) == expected_areas

    def test_working_area_definition(self):
        """Test working area is correctly defined."""
        areas = define_standard_areas()
        working_area = areas["working_area"]

        assert working_area.name == "working_area"
        assert working_area.path_template == "{contest_current_path}"
        assert working_area.purpose == "active_work"

    def test_archive_area_definition(self):
        """Test archive area is correctly defined."""
        areas = define_standard_areas()
        archive_area = areas["archive_area"]

        assert archive_area.name == "archive_area"
        assert archive_area.path_template == "{contest_stock_path}/{contest_name}/{problem_name}"
        assert archive_area.purpose == "completed_work_storage"


class TestGetAreaPath:
    """Test get_area_path function."""

    def test_get_existing_area_path(self):
        """Test getting path for existing area."""
        areas = define_standard_areas()
        context = WorkflowContext(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )
        path_vars = {"contest_current_path": "/home/user/current"}

        result = get_area_path("working_area", areas, context, path_vars)

        assert result == Path("/home/user/current")

    def test_get_archive_area_path(self):
        """Test getting path for archive area with contest/problem variables."""
        areas = define_standard_areas()
        context = WorkflowContext(
            contest_name="abc300",
            problem_name="a",
            language="python"
        )
        path_vars = {"contest_stock_path": "/home/user/stock"}

        result = get_area_path("archive_area", areas, context, path_vars)

        assert result == Path("/home/user/stock/abc300/a")

    def test_get_nonexistent_area_raises_error(self):
        """Test that requesting nonexistent area raises ValueError."""
        areas = define_standard_areas()
        context = WorkflowContext()
        path_vars = {}

        with pytest.raises(ValueError, match="Unknown area: nonexistent"):
            get_area_path("nonexistent", areas, context, path_vars)


class TestFolderArea:
    """Test FolderArea dataclass."""

    def test_folder_area_creation(self):
        """Test creating a FolderArea instance."""
        area = FolderArea(
            name="test_area",
            path_template="/test/{language}",
            purpose="testing",
            description="Test area"
        )

        assert area.name == "test_area"
        assert area.path_template == "/test/{language}"
        assert area.purpose == "testing"
        assert area.description == "Test area"
