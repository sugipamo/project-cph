"""
Workflow package - workflow building, execution, and step management
"""

# Workflow builders
try:
    from ..env_core.workflow import (
        GraphBasedWorkflowBuilder, RequestExecutionGraph,
        GraphToCompositeAdapter, PureRequestFactory
    )
    builder_exports = [
        'GraphBasedWorkflowBuilder', 'RequestExecutionGraph',
        'GraphToCompositeAdapter', 'PureRequestFactory'
    ]
except ImportError:
    builder_exports = []

# Step management
try:
    from ..env_core.step import Step, StepType, StepContext
    from ..env_core.step.workflow import Workflow
    step_exports = ['Step', 'StepType', 'StepContext', 'Workflow']
except ImportError:
    step_exports = []

# Execution engine
try:
    from ..operations.composite import ExecutionController
    execution_exports = ['ExecutionController']
except ImportError:
    execution_exports = []

# Graph analysis
try:
    from ..env_core.step.simple_graph_analysis import SimpleGraphAnalysis
    graph_exports = ['SimpleGraphAnalysis']
except ImportError:
    graph_exports = []

__all__ = builder_exports + step_exports + execution_exports + graph_exports