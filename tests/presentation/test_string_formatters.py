"""Tests for string formatters module."""
import pytest
from unittest.mock import Mock
from src.presentation.string_formatters import (
    format_template_string,
    extract_missing_template_keys,
    is_potential_script_path,
    validate_file_path_format,
    parse_container_names,
    normalize_filesystem_path,
    is_absolute_filesystem_path
)


class TestFormatTemplateString:
    """Test cases for format_template_string function."""

    def test_format_simple_template(self):
        """Test formatting simple template."""
        template = "Hello {name}, welcome to {place}!"
        context = {"name": "Alice", "place": "Wonderland"}
        result = format_template_string(template, context)
        assert result == "Hello Alice, welcome to Wonderland!"

    def test_format_with_missing_keys(self):
        """Test formatting with missing keys leaves them unchanged."""
        template = "Hello {name}, your age is {age}"
        context = {"name": "Bob"}
        result = format_template_string(template, context)
        assert result == "Hello Bob, your age is {age}"

    def test_format_with_empty_context(self):
        """Test formatting with empty context."""
        template = "Hello {name}!"
        context = {}
        result = format_template_string(template, context)
        assert result == "Hello {name}!"

    def test_format_non_string_template(self):
        """Test that non-string templates are returned as-is."""
        template = 123
        context = {"name": "Test"}
        result = format_template_string(template, context)
        assert result == 123

    def test_format_with_numeric_values(self):
        """Test formatting with numeric values."""
        template = "The answer is {answer}"
        context = {"answer": 42}
        result = format_template_string(template, context)
        assert result == "The answer is 42"

    def test_format_with_special_characters(self):
        """Test formatting with special characters in values."""
        template = "Path: {path}"
        context = {"path": "/home/user/{data}/file.txt"}
        result = format_template_string(template, context)
        assert result == "Path: /home/user/{data}/file.txt"


class TestExtractMissingTemplateKeys:
    """Test cases for extract_missing_template_keys function."""

    def test_extract_no_missing_keys(self):
        """Test extraction when all keys are available."""
        template = "Hello {name}, welcome to {place}!"
        available_keys = {"name", "place"}
        regex_ops = Mock()
        regex_ops.compile_pattern.return_value = "pattern"
        regex_ops.findall.return_value = ["name", "place"]
        
        result = extract_missing_template_keys(template, available_keys, regex_ops)
        assert result == []

    def test_extract_some_missing_keys(self):
        """Test extraction with some missing keys."""
        template = "Hello {name}, your age is {age} and city is {city}"
        available_keys = {"name"}
        regex_ops = Mock()
        regex_ops.compile_pattern.return_value = "pattern"
        regex_ops.findall.return_value = ["name", "age", "city"]
        
        result = extract_missing_template_keys(template, available_keys, regex_ops)
        assert result == ["age", "city"]

    def test_extract_all_missing_keys(self):
        """Test extraction when all keys are missing."""
        template = "{var1} and {var2}"
        available_keys = set()
        regex_ops = Mock()
        regex_ops.compile_pattern.return_value = "pattern"
        regex_ops.findall.return_value = ["var1", "var2"]
        
        result = extract_missing_template_keys(template, available_keys, regex_ops)
        assert result == ["var1", "var2"]

    def test_extract_duplicate_keys(self):
        """Test extraction with duplicate keys in template."""
        template = "{name} says hello to {name}"
        available_keys = set()
        regex_ops = Mock()
        regex_ops.compile_pattern.return_value = "pattern"
        regex_ops.findall.return_value = ["name", "name"]
        
        result = extract_missing_template_keys(template, available_keys, regex_ops)
        assert result == ["name", "name"]  # Preserves duplicates


class TestIsPotentialScriptPath:
    """Test cases for is_potential_script_path function."""

    def test_is_script_with_py_extension(self):
        """Test detection of Python script."""
        result = is_potential_script_path(["script.py"], [".py", ".sh"])
        assert result is True

    def test_is_script_with_sh_extension(self):
        """Test detection of shell script."""
        result = is_potential_script_path(["script.sh"], [".py", ".sh"])
        assert result is True

    def test_not_script_wrong_extension(self):
        """Test non-script file."""
        result = is_potential_script_path(["file.txt"], [".py", ".sh"])
        assert result is False

    def test_not_script_multiple_items(self):
        """Test multiple items in list."""
        result = is_potential_script_path(["script.py", "arg"], [".py"])
        assert result is False

    def test_not_script_empty_list(self):
        """Test empty list."""
        result = is_potential_script_path([], [".py", ".sh"])
        assert result is False

    def test_script_with_path(self):
        """Test script with full path."""
        result = is_potential_script_path(["/path/to/script.py"], [".py"])
        assert result is True

    def test_no_script_extensions_raises_error(self):
        """Test that None script_extensions raises error."""
        with pytest.raises(ValueError, match="script_extensions parameter is required"):
            is_potential_script_path(["script.py"], None)


class TestValidateFilePathFormat:
    """Test cases for validate_file_path_format function."""

    def test_valid_simple_path(self):
        """Test valid simple path."""
        valid, error = validate_file_path_format("file.txt")
        assert valid is True
        assert error is None

    def test_valid_nested_path(self):
        """Test valid nested path."""
        valid, error = validate_file_path_format("dir/subdir/file.txt")
        assert valid is True
        assert error is None

    def test_empty_path(self):
        """Test empty path."""
        valid, error = validate_file_path_format("")
        assert valid is False
        assert error == "Path cannot be empty"

    def test_path_traversal_relative(self):
        """Test path traversal detection with relative path."""
        valid, error = validate_file_path_format("../etc/passwd")
        assert valid is False
        assert error == "Path traversal detected"

    def test_path_traversal_nested(self):
        """Test path traversal detection with nested path."""
        valid, error = validate_file_path_format("dir/../../../etc/passwd")
        assert valid is False
        assert error == "Path traversal detected"

    def test_absolute_path_with_dotdot(self):
        """Test absolute path with '..' is rejected."""
        valid, error = validate_file_path_format("/home/../etc/passwd")
        assert valid is False
        assert error == "Absolute paths with '..' are not allowed"

    def test_dangerous_characters(self):
        """Test detection of dangerous characters."""
        dangerous_paths = [
            "file|command",
            "file;command",
            "file&command",
            "file$var",
            "file`cmd`",
            "file\ncommand",
            "file\rcommand",
            "file\0command"
        ]
        for path in dangerous_paths:
            valid, error = validate_file_path_format(path)
            assert valid is False
            assert "dangerous characters" in error

    def test_valid_absolute_path(self):
        """Test valid absolute path."""
        valid, error = validate_file_path_format("/home/user/file.txt")
        assert valid is True
        assert error is None


class TestParseContainerNames:
    """Test cases for parse_container_names function."""

    def test_parse_single_container(self):
        """Test parsing single container."""
        output = """CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
abc123         ubuntu    bash      1 hour    Up       80      my-container"""
        result = parse_container_names(output)
        assert result == ["my-container"]

    def test_parse_multiple_containers(self):
        """Test parsing multiple containers."""
        output = """CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
abc123         ubuntu    bash      1 hour    Up       80      container1
def456         nginx     nginx     2 hours   Up       443     container2
ghi789         redis     redis     3 hours   Up       6379    container3"""
        result = parse_container_names(output)
        assert result == ["container1", "container2", "container3"]

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = parse_container_names("")
        assert result == []

    def test_parse_header_only(self):
        """Test parsing header only."""
        output = "CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES"
        result = parse_container_names(output)
        assert result == []

    def test_parse_with_spaces_in_names(self):
        """Test parsing with spaces handled properly."""
        output = """CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS   PORTS   NAMES
abc123         ubuntu    bash      1 hour    Up       80      my-container-name"""
        result = parse_container_names(output)
        assert result == ["my-container-name"]


class TestNormalizeFilesystemPath:
    """Test cases for normalize_filesystem_path function."""

    def test_normalize_simple_path(self):
        """Test normalizing simple path."""
        result = normalize_filesystem_path("dir/file.txt")
        assert result == "dir/file.txt"

    def test_normalize_with_current_dir(self):
        """Test normalizing with current directory references."""
        result = normalize_filesystem_path("./dir/./file.txt")
        assert result == "dir/file.txt"

    def test_normalize_with_parent_dir(self):
        """Test normalizing with parent directory references."""
        result = normalize_filesystem_path("dir1/dir2/../file.txt")
        assert result == "dir1/file.txt"

    def test_normalize_multiple_parent_dirs(self):
        """Test normalizing with multiple parent directory references."""
        result = normalize_filesystem_path("dir1/dir2/../../file.txt")
        assert result == "file.txt"

    def test_normalize_absolute_path(self):
        """Test normalizing absolute path."""
        result = normalize_filesystem_path("/home/user/../other/file.txt")
        assert result == "/home/other/file.txt"

    def test_normalize_empty_path(self):
        """Test normalizing empty path."""
        result = normalize_filesystem_path("")
        assert result == ""

    def test_normalize_windows_path(self):
        """Test normalizing Windows-style path."""
        result = normalize_filesystem_path("dir\\subdir\\file.txt")
        assert result == "dir/subdir/file.txt"

    def test_normalize_excess_parent_dirs(self):
        """Test normalizing with excess parent directory references."""
        result = normalize_filesystem_path("../../../file.txt")
        assert result == "../../../file.txt"

    def test_normalize_root_path(self):
        """Test normalizing root path."""
        result = normalize_filesystem_path("/")
        assert result == "/"

    def test_normalize_to_empty_becomes_dot(self):
        """Test that paths normalizing to empty become '.'."""
        result = normalize_filesystem_path("dir/..")
        assert result == "."


class TestIsAbsoluteFilesystemPath:
    """Test cases for is_absolute_filesystem_path function."""

    def test_unix_absolute_path(self):
        """Test Unix-style absolute path."""
        assert is_absolute_filesystem_path("/home/user") is True
        assert is_absolute_filesystem_path("/") is True

    def test_windows_absolute_path(self):
        """Test Windows-style absolute path."""
        assert is_absolute_filesystem_path("C:\\Users") is True
        assert is_absolute_filesystem_path("D:") is True
        assert is_absolute_filesystem_path("Z:\\") is True

    def test_relative_paths(self):
        """Test relative paths."""
        assert is_absolute_filesystem_path("relative/path") is False
        assert is_absolute_filesystem_path("./path") is False
        assert is_absolute_filesystem_path("../path") is False

    def test_empty_path(self):
        """Test empty path."""
        assert is_absolute_filesystem_path("") is False

    def test_invalid_windows_paths(self):
        """Test invalid Windows-style paths."""
        assert is_absolute_filesystem_path("1:") is False  # Digit instead of letter
        assert is_absolute_filesystem_path(":C") is False  # Wrong order
        assert is_absolute_filesystem_path("CC:") is False  # Two letters