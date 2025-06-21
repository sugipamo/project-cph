"""Tests for ConfigurationRepository"""
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.infrastructure.persistence.configuration_repository import ConfigurationRepository


class TestConfigurationRepository:
    """Test suite for ConfigurationRepository"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        # Create the required table structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                config_key TEXT PRIMARY KEY,
                config_value TEXT
            )
        """)
        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def repo(self, temp_db_path):
        """Create ConfigurationRepository instance with temp database"""
        return ConfigurationRepository(temp_db_path)

    def test_init_with_default_path(self):
        """Test initialization with default database path"""
        repo = ConfigurationRepository()
        assert repo.db_path == "cph_history.db"

    def test_init_with_custom_path(self):
        """Test initialization with custom database path"""
        custom_path = "/custom/path/test.db"
        repo = ConfigurationRepository(custom_path)
        assert repo.db_path == custom_path


    def test_load_previous_values_empty_db(self, repo):
        """Test loading previous values from empty database"""
        result = repo.load_previous_values()

        expected = {
            "old_contest_name": "",
            "old_problem_name": ""
        }
        assert result == expected

    def test_save_and_load_current_values(self, repo):
        """Test saving and loading configuration values"""
        contest_name = "test_contest"
        problem_name = "test_problem"

        # Save values
        repo.save_current_values(contest_name, problem_name)

        # Load values
        result = repo.load_previous_values()

        assert result["old_contest_name"] == contest_name
        assert result["old_problem_name"] == problem_name


    def test_save_current_values_overwrite(self, repo):
        """Test overwriting existing configuration values"""
        # Save initial values
        repo.save_current_values("contest1", "problem1")

        # Overwrite with new values
        repo.save_current_values("contest2", "problem2")

        # Verify new values are loaded
        result = repo.load_previous_values()
        assert result["old_contest_name"] == "contest2"
        assert result["old_problem_name"] == "problem2"

    def test_get_config_value_existing(self, repo):
        """Test getting existing configuration value"""
        # Insert test data directly
        with sqlite3.connect(repo.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_config (config_key, config_value) VALUES (?, ?)",
                ("test_key", json.dumps("test_value"))
            )
            conn.commit()

        # Test getting the value
        with sqlite3.connect(repo.db_path) as conn:
            cursor = conn.cursor()
            result = repo._get_config_value(cursor, "test_key")

        assert result == "test_value"



    def test_save_config_value(self, repo):
        """Test saving configuration value"""
        with sqlite3.connect(repo.db_path) as conn:
            cursor = conn.cursor()
            repo._save_config_value(cursor, "test_key", "test_value")
            conn.commit()

            # Verify value was saved
            cursor.execute(
                "SELECT config_value FROM system_config WHERE config_key = ?",
                ("test_key",)
            )
            row = cursor.fetchone()

        assert row is not None
        assert json.loads(row[0]) == "test_value"

    def test_get_available_config_keys_empty(self, repo):
        """Test getting available config keys from empty database"""
        result = repo.get_available_config_keys()
        assert result == []

    def test_get_available_config_keys_with_data(self, repo):
        """Test getting available config keys with data"""
        # Insert test data
        test_keys = ["key1", "key2", "key3"]
        with sqlite3.connect(repo.db_path) as conn:
            cursor = conn.cursor()
            for key in test_keys:
                cursor.execute(
                    "INSERT INTO system_config (config_key, config_value) VALUES (?, ?)",
                    (key, json.dumps(f"value_{key}"))
                )
            conn.commit()

        result = repo.get_available_config_keys()
        assert sorted(result) == sorted(test_keys)




