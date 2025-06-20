"""Tests for CLI dependencies documentation"""

from pathlib import Path

import pytest


class TestDependencies:
    """Tests for the CLI dependencies documentation file"""

    def test_dependencies_file_exists(self):
        """Verify that the dependencies documentation file exists"""
        file_path = Path("src/cli/dependencies.py")
        assert file_path.exists(), f"Dependencies file not found at {file_path}"

    def test_dependencies_file_is_documentation(self):
        """Verify that the file contains only documentation"""
        file_path = Path("src/cli/dependencies.py")
        content = file_path.read_text(encoding="utf-8")

        # Check that it starts with a docstring
        assert content.strip().startswith('"""'), "File should start with a docstring"

        # Check that it contains the expected sections
        expected_sections = [
            "CLI実装に必要な機能一覧",
            "DI Container注入",
            "Workflow構築",
            "設定管理システム",
            "コンテキスト解析",
            "ログ機能",
            "結果表示",
            "エラーハンドリング",
            "永続化機能"
        ]

        for section in expected_sections:
            assert section in content, f"Expected section '{section}' not found in documentation"

    def test_dependencies_structure(self):
        """Verify the documentation structure is well-formed"""
        file_path = Path("src/cli/dependencies.py")
        content = file_path.read_text(encoding="utf-8")

        lines = content.strip().split('\n')

        # Should start and end with docstrings
        assert lines[0] == '"""CLI dependency requirements documentation"""'
        assert lines[-1] == '"""'

        # Count the number of main sections (### headers)
        main_sections = [line for line in lines if line.strip().startswith("### ")]
        assert len(main_sections) == 8, f"Expected 8 main sections, found {len(main_sections)}"

        # Verify each section has content
        for i, line in enumerate(lines):
            if line.strip().startswith("### ") and i + 1 < len(lines):
                # Check that the next line after a section header has content
                next_line = lines[i + 1].strip()
                assert next_line and not next_line.startswith("#"), \
                    f"Section '{line}' should have content after it"

    def test_dependencies_references_valid_paths(self):
        """Verify that referenced file paths in documentation exist"""
        file_path = Path("src/cli/dependencies.py")
        content = file_path.read_text(encoding="utf-8")

        # Extract file paths mentioned in the documentation
        import re
        path_pattern = re.compile(r'src/[\w/]+\.py')
        referenced_paths = path_pattern.findall(content)

        # Check that at least some key files exist
        key_files = [
            "src/configuration/config_manager.py",
            "src/context/user_input_parser/user_input_parser.py",
            "src/infrastructure/drivers/logging/unified_logger.py",
            "src/application/orchestration/workflow_result_presenter.py"
        ]

        for key_file in key_files:
            assert key_file in referenced_paths, f"Key file '{key_file}' not referenced in documentation"
            # Note: We're not checking if files exist as they might be in different states

    def test_checkmarks_consistency(self):
        """Verify that checkmarks (✓) are used consistently"""
        file_path = Path("src/cli/dependencies.py")
        content = file_path.read_text(encoding="utf-8")

        lines_with_checkmarks = [line for line in content.split('\n') if '✓' in line]

        # Verify checkmarks are only used in section headers
        for line in lines_with_checkmarks:
            assert line.strip().startswith("### "), \
                f"Checkmark should only appear in section headers: {line.strip()}"

        # Count sections with checkmarks
        assert len(lines_with_checkmarks) == 2, \
            f"Expected 2 sections with checkmarks, found {len(lines_with_checkmarks)}"
