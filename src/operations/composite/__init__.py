"""
Composite operations package
"""
from .base_composite_request import BaseCompositeRequest
from .composite_request import CompositeRequest
from .driver_bound_request import DriverBoundRequest  
from .parallel_composite_request import ParallelCompositeRequest

# New separated components
try:
    from .execution_controller import ExecutionController
    from .output_manager import OutputManager
    from .composite_structure import CompositeStructure
    separated_exports = ['ExecutionController', 'OutputManager', 'CompositeStructure']
except ImportError:
    separated_exports = []

__all__ = [
    'BaseCompositeRequest',
    'CompositeRequest',
    'DriverBoundRequest',
    'ParallelCompositeRequest'
] + separated_exports