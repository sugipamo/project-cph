"""Exceptions module - Common exception classes."""
from .composite_step_failure import CompositeStepFailureError
from .persistence_exceptions import (
    PersistenceError,
    ConnectionError,
    MigrationError,
    QueryError,
    TransactionError,
    RepositoryError,
    IntegrityError,
    SchemaError,
)

__all__ = [
    "CompositeStepFailureError",
    "PersistenceError",
    "ConnectionError",
    "MigrationError",
    "QueryError",
    "TransactionError",
    "RepositoryError",
    "IntegrityError",
    "SchemaError",
]
