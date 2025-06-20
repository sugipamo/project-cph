"""Tests for persistence-specific exceptions."""
import pytest

from src.operations.exceptions.persistence_exceptions import (
    ConnectionError,
    IntegrityError,
    MigrationError,
    PersistenceError,
    QueryError,
    RepositoryError,
    SchemaError,
    TransactionError,
)


class TestPersistenceError:
    """Test PersistenceError base exception."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        error = PersistenceError("Test error message")

        assert str(error) == "Test error message"
        assert error.operation is None
        assert error.details == {}

    def test_initialization_with_operation(self):
        """Test initialization with operation parameter."""
        error = PersistenceError("Test error", operation="test_operation")

        assert str(error) == "Test error"
        assert error.operation == "test_operation"
        assert error.details == {}

    def test_initialization_with_details(self):
        """Test initialization with details parameter."""
        details = {"key": "value", "number": 42}
        error = PersistenceError("Test error", details=details)

        assert str(error) == "Test error"
        assert error.operation is None
        assert error.details == details
        # Note: Current implementation stores reference, not copy

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        details = {"error_code": 500, "context": "testing"}
        error = PersistenceError("Test error", operation="test_op", details=details)

        assert str(error) == "Test error"
        assert error.operation == "test_op"
        assert error.details == details

    def test_none_details_becomes_empty_dict(self):
        """Test that None details becomes empty dict."""
        error = PersistenceError("Test error", details=None)

        assert error.details == {}

    def test_inheritance_from_exception(self):
        """Test that PersistenceError inherits from Exception."""
        error = PersistenceError("Test error")

        assert isinstance(error, Exception)
        assert isinstance(error, PersistenceError)


class TestConnectionError:
    """Test ConnectionError exception."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = ConnectionError()

        assert str(error) == "Database connection failed"
        assert error.operation == "connection"
        assert error.details == {}

    def test_custom_message(self):
        """Test initialization with custom message."""
        error = ConnectionError("Custom connection error")

        assert str(error) == "Custom connection error"
        assert error.operation == "connection"

    def test_with_details(self):
        """Test initialization with details."""
        details = {"host": "localhost", "port": 5432}
        error = ConnectionError("Connection failed", details=details)

        assert str(error) == "Connection failed"
        assert error.operation == "connection"
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = ConnectionError()

        assert isinstance(error, PersistenceError)
        assert isinstance(error, ConnectionError)


class TestMigrationError:
    """Test MigrationError exception."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = MigrationError("Migration failed")

        assert str(error) == "Migration failed"
        assert error.operation == "migration"
        assert error.migration_version is None

    def test_with_migration_version(self):
        """Test initialization with migration version."""
        error = MigrationError("Migration failed", migration_version=5)

        assert str(error) == "Migration failed"
        assert error.operation == "migration"
        assert error.migration_version == 5

    def test_with_details(self):
        """Test initialization with details."""
        details = {"table": "users", "sql": "CREATE TABLE users..."}
        error = MigrationError("Migration failed", migration_version=3, details=details)

        assert str(error) == "Migration failed"
        assert error.operation == "migration"
        assert error.migration_version == 3
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = MigrationError("Migration failed")

        assert isinstance(error, PersistenceError)
        assert isinstance(error, MigrationError)


class TestQueryError:
    """Test QueryError exception."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = QueryError("Query failed")

        assert str(error) == "Query failed"
        assert error.operation == "query"
        assert error.query is None
        assert error.params is None

    def test_with_query(self):
        """Test initialization with query."""
        query = "SELECT * FROM users WHERE id = ?"
        error = QueryError("Query failed", query=query)

        assert str(error) == "Query failed"
        assert error.operation == "query"
        assert error.query == query
        assert error.params is None

    def test_with_params(self):
        """Test initialization with params."""
        params = (123, "test")
        error = QueryError("Query failed", params=params)

        assert str(error) == "Query failed"
        assert error.operation == "query"
        assert error.query is None
        assert error.params == params

    def test_with_query_and_params(self):
        """Test initialization with both query and params."""
        query = "SELECT * FROM users WHERE id = ? AND name = ?"
        params = (123, "test")
        error = QueryError("Query failed", query=query, params=params)

        assert str(error) == "Query failed"
        assert error.operation == "query"
        assert error.query == query
        assert error.params == params

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = QueryError("Query failed")

        assert isinstance(error, PersistenceError)
        assert isinstance(error, QueryError)


class TestTransactionError:
    """Test TransactionError exception."""

    def test_default_initialization(self):
        """Test default initialization."""
        error = TransactionError()

        assert str(error) == "Transaction failed"
        assert error.operation == "transaction"
        assert error.details == {}

    def test_custom_message(self):
        """Test initialization with custom message."""
        error = TransactionError("Custom transaction error")

        assert str(error) == "Custom transaction error"
        assert error.operation == "transaction"

    def test_with_details(self):
        """Test initialization with details."""
        details = {"isolation_level": "READ_COMMITTED", "timeout": 30}
        error = TransactionError("Transaction timeout", details=details)

        assert str(error) == "Transaction timeout"
        assert error.operation == "transaction"
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = TransactionError()

        assert isinstance(error, PersistenceError)
        assert isinstance(error, TransactionError)


class TestRepositoryError:
    """Test RepositoryError exception."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = RepositoryError("Repository operation failed")

        assert str(error) == "Repository operation failed"
        assert error.operation == "repository"
        assert error.repository_name is None
        assert error.entity_id is None

    def test_with_repository_name(self):
        """Test initialization with repository name."""
        error = RepositoryError("Repository failed", repository_name="UserRepository")

        assert str(error) == "Repository failed"
        assert error.operation == "repository"
        assert error.repository_name == "UserRepository"
        assert error.entity_id is None

    def test_with_entity_id(self):
        """Test initialization with entity ID."""
        error = RepositoryError("Repository failed", entity_id="user-123")

        assert str(error) == "Repository failed"
        assert error.operation == "repository"
        assert error.repository_name is None
        assert error.entity_id == "user-123"

    def test_with_all_parameters(self):
        """Test initialization with all parameters."""
        details = {"method": "find_by_id", "table": "users"}
        error = RepositoryError(
            "Repository failed",
            repository_name="UserRepository",
            entity_id="user-123",
            details=details
        )

        assert str(error) == "Repository failed"
        assert error.operation == "repository"
        assert error.repository_name == "UserRepository"
        assert error.entity_id == "user-123"
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = RepositoryError("Repository failed")

        assert isinstance(error, PersistenceError)
        assert isinstance(error, RepositoryError)


class TestIntegrityError:
    """Test IntegrityError exception."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = IntegrityError("Integrity constraint violated")

        assert str(error) == "Integrity constraint violated"
        assert error.operation == "integrity"
        assert error.constraint is None

    def test_with_constraint(self):
        """Test initialization with constraint."""
        error = IntegrityError("Unique constraint violated", constraint="users_email_unique")

        assert str(error) == "Unique constraint violated"
        assert error.operation == "integrity"
        assert error.constraint == "users_email_unique"

    def test_with_details(self):
        """Test initialization with details."""
        details = {"table": "users", "column": "email", "value": "test@example.com"}
        error = IntegrityError(
            "Unique constraint violated",
            constraint="users_email_unique",
            details=details
        )

        assert str(error) == "Unique constraint violated"
        assert error.operation == "integrity"
        assert error.constraint == "users_email_unique"
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = IntegrityError("Integrity constraint violated")

        assert isinstance(error, PersistenceError)
        assert isinstance(error, IntegrityError)


class TestSchemaError:
    """Test SchemaError exception."""

    def test_basic_initialization(self):
        """Test basic initialization."""
        error = SchemaError("Schema error occurred")

        assert str(error) == "Schema error occurred"
        assert error.operation == "schema"
        assert error.table_name is None

    def test_with_table_name(self):
        """Test initialization with table name."""
        error = SchemaError("Table not found", table_name="users")

        assert str(error) == "Table not found"
        assert error.operation == "schema"
        assert error.table_name == "users"

    def test_with_details(self):
        """Test initialization with details."""
        details = {"expected_columns": ["id", "name"], "actual_columns": ["id"]}
        error = SchemaError(
            "Column missing",
            table_name="users",
            details=details
        )

        assert str(error) == "Column missing"
        assert error.operation == "schema"
        assert error.table_name == "users"
        assert error.details == details

    def test_inheritance(self):
        """Test inheritance from PersistenceError."""
        error = SchemaError("Schema error")

        assert isinstance(error, PersistenceError)
        assert isinstance(error, SchemaError)


class TestExceptionRaising:
    """Test that exceptions can be properly raised and caught."""

    def test_raise_and_catch_persistence_error(self):
        """Test raising and catching PersistenceError."""
        with pytest.raises(PersistenceError) as exc_info:
            raise PersistenceError("Test error", operation="test")

        assert str(exc_info.value) == "Test error"
        assert exc_info.value.operation == "test"

    def test_catch_specific_error_as_base(self):
        """Test catching specific error as base PersistenceError."""
        with pytest.raises(PersistenceError) as exc_info:
            raise ConnectionError("Connection failed")

        assert isinstance(exc_info.value, ConnectionError)
        assert isinstance(exc_info.value, PersistenceError)

    def test_catch_specific_error_type(self):
        """Test catching specific error type."""
        with pytest.raises(QueryError) as exc_info:
            raise QueryError("Query failed", query="SELECT * FROM users")

        assert exc_info.value.query == "SELECT * FROM users"

    def test_exception_attributes_preserved(self):
        """Test that exception attributes are preserved when raised."""
        details = {"error_code": 500}

        with pytest.raises(RepositoryError) as exc_info:
            raise RepositoryError(
                "Repository failed",
                repository_name="TestRepo",
                entity_id="123",
                details=details
            )

        error = exc_info.value
        assert error.repository_name == "TestRepo"
        assert error.entity_id == "123"
        assert error.details == details
        assert error.operation == "repository"
