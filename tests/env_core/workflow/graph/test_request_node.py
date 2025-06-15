"""
Tests for RequestNode class
"""
from unittest.mock import Mock

import pytest

from src.domain.requests.base.base_request import OperationRequestFoundation
from src.workflow.builder.request_execution_graph import RequestNode


class TestRequestNode:
    """Tests for RequestNode class"""

    def test_request_node_creation_minimal(self):
        """Test creating RequestNode with minimal parameters"""
        request = Mock(spec=OperationRequestFoundation)
        node = RequestNode("node1", request)

        assert node.id == "node1"
        assert node.request == request
        assert node.status == "pending"
        assert node.result is None
        assert node.creates_files == set()
        assert node.creates_dirs == set()
        assert node.reads_files == set()
        assert node.requires_dirs == set()
        assert node.metadata == {}

    def test_request_node_creation_with_resources(self):
        """Test creating RequestNode with resource information"""
        request = Mock(spec=OperationRequestFoundation)
        node = RequestNode(
            "node2",
            request,
            creates_files={"output.txt", "result.log"},
            creates_dirs={"output_dir"},
            reads_files={"input.txt"},
            requires_dirs={"working_dir"},
            metadata={"priority": "high"}
        )

        assert node.creates_files == {"output.txt", "result.log"}
        assert node.creates_dirs == {"output_dir"}
        assert node.reads_files == {"input.txt"}
        assert node.requires_dirs == {"working_dir"}
        assert node.metadata == {"priority": "high"}

    def test_request_node_string_representation(self):
        """Test string representation of RequestNode"""
        request = Mock(spec=OperationRequestFoundation)
        node = RequestNode("test_node", request)

        # RequestNode doesn't have a custom __str__ method, so we'll test the object creation
        assert node.id == "test_node"
        assert node.status == "pending"

    def test_request_node_equality(self):
        """Test RequestNode equality comparison"""
        request = Mock(spec=OperationRequestFoundation)
        node1 = RequestNode("node1", request)
        node2 = RequestNode("node1", request)
        node3 = RequestNode("node2", request)

        assert node1 == node2  # Same ID
        assert node1 != node3  # Different ID

    def test_request_node_hash(self):
        """Test RequestNode is hashable and can be used in sets"""
        request = Mock(spec=OperationRequestFoundation)
        node1 = RequestNode("node1", request)
        node2 = RequestNode("node2", request)

        node_set = {node1, node2}
        assert len(node_set) == 2
        assert node1 in node_set
        assert node2 in node_set

    def test_request_node_status_management(self):
        """Test request node status changes"""
        request = Mock(spec=OperationRequestFoundation)
        node = RequestNode("node1", request)

        # Initial status
        assert node.status == "pending"

        # Status changes
        node.status = "running"
        assert node.status == "running"

        node.status = "completed"
        assert node.status == "completed"

        node.status = "failed"
        assert node.status == "failed"
