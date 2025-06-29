"""Tests for persistence exceptions"""
import pytest
from src.infrastructure.persistence_exceptions import (
    PersistenceError,
    ConnectionError,
    MigrationError,
    QueryError,
    TransactionError,
    RepositoryError,
    IntegrityError,
    SchemaError
)


class TestPersistenceError:
    """Test cases for PersistenceError base class"""

    def test_init_with_all_params(self):
        """Test initialization with all parameters"""
        details = {"key": "value", "count": 42}
        error = PersistenceError("Test error", operation="test_op", details=details)
        
        assert str(error) == "Test error"
        assert error.operation == "test_op"
        assert error.details == details

    def test_init_minimal(self):
        """Test initialization with minimal parameters"""
        error = PersistenceError("Simple error", operation=None, details={})
        
        assert str(error) == "Simple error"
        assert error.operation is None
        assert error.details == {}

    def test_init_without_details_raises_error(self):
        """Test that initialization without details raises TypeError"""
        with pytest.raises(TypeError) as exc_info:
            PersistenceError("Error message", operation="op")
        
        assert "missing 1 required positional argument: 'details'" in str(exc_info.value)

    def test_init_with_none_details_raises_error(self):
        """Test that passing None for details raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            PersistenceError("Error message", operation=None, details=None)
        
        assert "Details must be explicitly provided" in str(exc_info.value)


class TestConnectionError:
    """Test cases for ConnectionError"""

    def test_default_message(self):
        """Test default message and operation"""
        error = ConnectionError("Database connection failed", details={})
        
        assert str(error) == "Database connection failed"
        assert error.operation == "connection"
        assert error.details == {}

    def test_custom_message(self):
        """Test custom message"""
        error = ConnectionError("Custom connection error", details={"host": "localhost"})
        
        assert str(error) == "Custom connection error"
        assert error.operation == "connection"
        assert error.details == {"host": "localhost"}


class TestMigrationError:
    """Test cases for MigrationError"""

    def test_with_migration_version(self):
        """Test with migration version"""
        error = MigrationError("Migration failed", migration_version=5, details={})
        
        assert str(error) == "Migration failed"
        assert error.operation == "migration"
        assert error.migration_version == 5
        assert error.details == {}

    def test_without_migration_version(self):
        """Test without migration version"""
        error = MigrationError("General migration error", details={"reason": "syntax error"})
        
        assert str(error) == "General migration error"
        assert error.operation == "migration"
        assert error.migration_version is None
        assert error.details == {"reason": "syntax error"}


class TestQueryError:
    """Test cases for QueryError"""

    def test_with_query_and_params(self):
        """Test with query string and parameters"""
        query = "SELECT * FROM users WHERE id = ?"
        params = (123,)
        error = QueryError("Query failed", query=query, params=params, details={})
        
        assert str(error) == "Query failed"
        assert error.operation == "query"
        assert error.query == query
        assert error.params == params
        assert error.details == {}

    def test_without_query_details(self):
        """Test without query details"""
        error = QueryError("Unknown query error", details={"code": "SYNTAX_ERROR"})
        
        assert str(error) == "Unknown query error"
        assert error.operation == "query"
        assert error.query is None
        assert error.params is None
        assert error.details == {"code": "SYNTAX_ERROR"}


class TestTransactionError:
    """Test cases for TransactionError"""

    def test_default_message(self):
        """Test default message"""
        error = TransactionError(details={})
        
        assert str(error) == "Transaction failed"
        assert error.operation == "transaction"
        assert error.details == {}

    def test_custom_message(self):
        """Test custom message"""
        error = TransactionError("Deadlock detected", details={"isolation_level": "SERIALIZABLE"})
        
        assert str(error) == "Deadlock detected"
        assert error.operation == "transaction"
        assert error.details == {"isolation_level": "SERIALIZABLE"}


class TestRepositoryError:
    """Test cases for RepositoryError"""

    def test_with_all_attributes(self):
        """Test with repository name and entity ID"""
        error = RepositoryError(
            "Entity not found",
            repository_name="UserRepository",
            entity_id="user-123",
            details={"table": "users"}
        )
        
        assert str(error) == "Entity not found"
        assert error.operation == "repository"
        assert error.repository_name == "UserRepository"
        assert error.entity_id == "user-123"
        assert error.details == {"table": "users"}

    def test_minimal_attributes(self):
        """Test with minimal attributes"""
        error = RepositoryError("Save failed", details={})
        
        assert str(error) == "Save failed"
        assert error.operation == "repository"
        assert error.repository_name is None
        assert error.entity_id is None
        assert error.details == {}


class TestIntegrityError:
    """Test cases for IntegrityError"""

    def test_with_constraint(self):
        """Test with constraint name"""
        error = IntegrityError(
            "Unique constraint violation",
            constraint="users_email_unique",
            details={"field": "email"}
        )
        
        assert str(error) == "Unique constraint violation"
        assert error.operation == "integrity"
        assert error.constraint == "users_email_unique"
        assert error.details == {"field": "email"}

    def test_without_constraint(self):
        """Test without constraint name"""
        error = IntegrityError("Foreign key violation", details={"table": "orders"})
        
        assert str(error) == "Foreign key violation"
        assert error.operation == "integrity"
        assert error.constraint is None
        assert error.details == {"table": "orders"}


class TestSchemaError:
    """Test cases for SchemaError"""

    def test_with_table_name(self):
        """Test with table name"""
        error = SchemaError(
            "Table does not exist",
            table_name="users",
            details={"database": "test_db"}
        )
        
        assert str(error) == "Table does not exist"
        assert error.operation == "schema"
        assert error.table_name == "users"
        assert error.details == {"database": "test_db"}

    def test_without_table_name(self):
        """Test without table name"""
        error = SchemaError("Invalid schema version", details={"version": "1.0.0"})
        
        assert str(error) == "Invalid schema version"
        assert error.operation == "schema"
        assert error.table_name is None
        assert error.details == {"version": "1.0.0"}


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance"""

    def test_all_exceptions_inherit_from_persistence_error(self):
        """Test that all specific exceptions inherit from PersistenceError"""
        exceptions = [
            ConnectionError("test", details={}),
            MigrationError("test", details={}),
            QueryError("test", details={}),
            TransactionError("test", details={}),
            RepositoryError("test", details={}),
            IntegrityError("test", details={}),
            SchemaError("test", details={})
        ]
        
        for exc in exceptions:
            assert isinstance(exc, PersistenceError)
            assert isinstance(exc, Exception)

    def test_exception_catching(self):
        """Test catching exceptions at different levels"""
        # Can catch as specific exception
        with pytest.raises(ConnectionError):
            raise ConnectionError("Connection failed", details={})
        
        # Can catch as PersistenceError
        with pytest.raises(PersistenceError):
            raise QueryError("Query failed", details={})
        
        # Can catch as general Exception
        with pytest.raises(Exception):
            raise SchemaError("Schema error", details={})