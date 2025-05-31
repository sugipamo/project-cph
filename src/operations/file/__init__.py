"""
File operations package
"""
from .file_request import FileRequest
from .file_driver import FileDriver
from .local_file_driver import LocalFileDriver
from .file_op_type import FileOpType

# Strategy pattern exports
try:
    from .strategies import FileOperationStrategyFactory, ReadStrategy, WriteStrategy
    strategy_exports = ['FileOperationStrategyFactory', 'ReadStrategy', 'WriteStrategy']
except ImportError:
    strategy_exports = []

__all__ = [
    'FileRequest',
    'FileDriver', 
    'LocalFileDriver',
    'FileOpType'
] + strategy_exports