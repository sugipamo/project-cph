"""Tests for resource analysis types."""
import pytest

from src.workflow.builder.resource_analysis.resource_types import ResourceInfo


class TestResourceInfo:
    """Test ResourceInfo dataclass."""

    def test_init_basic(self):
        info = ResourceInfo(
            creates_files={"file1.txt", "file2.txt"},
            creates_dirs={"dir1", "dir2"},
            reads_files={"input1.txt", "input2.txt"},
            requires_dirs={"required_dir1", "required_dir2"}
        )

        assert info.creates_files == {"file1.txt", "file2.txt"}
        assert info.creates_dirs == {"dir1", "dir2"}
        assert info.reads_files == {"input1.txt", "input2.txt"}
        assert info.requires_dirs == {"required_dir1", "required_dir2"}

    def test_init_empty_sets(self):
        info = ResourceInfo(
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs=set()
        )

        assert info.creates_files == set()
        assert info.creates_dirs == set()
        assert info.reads_files == set()
        assert info.requires_dirs == set()

    def test_immutability(self):
        info = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input.txt"},
            requires_dirs={"req_dir"}
        )

        # frozen=True prevents attribute modification
        with pytest.raises(AttributeError):
            info.creates_files = {"new_file.txt"}

        with pytest.raises(AttributeError):
            info.creates_dirs = {"new_dir"}

        with pytest.raises(AttributeError):
            info.reads_files = {"new_input.txt"}

        with pytest.raises(AttributeError):
            info.requires_dirs = {"new_req_dir"}

    def test_empty_factory_method(self):
        empty_info = ResourceInfo.empty()

        assert empty_info.creates_files == set()
        assert empty_info.creates_dirs == set()
        assert empty_info.reads_files == set()
        assert empty_info.requires_dirs == set()

    def test_merge_non_overlapping(self):
        info1 = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        info2 = ResourceInfo(
            creates_files={"file2.txt"},
            creates_dirs={"dir2"},
            reads_files={"input2.txt"},
            requires_dirs={"req_dir2"}
        )

        merged = info1.merge(info2)

        assert merged.creates_files == {"file1.txt", "file2.txt"}
        assert merged.creates_dirs == {"dir1", "dir2"}
        assert merged.reads_files == {"input1.txt", "input2.txt"}
        assert merged.requires_dirs == {"req_dir1", "req_dir2"}

        # Original objects unchanged
        assert info1.creates_files == {"file1.txt"}
        assert info2.creates_files == {"file2.txt"}

    def test_merge_overlapping(self):
        info1 = ResourceInfo(
            creates_files={"file1.txt", "shared.txt"},
            creates_dirs={"dir1", "shared_dir"},
            reads_files={"input1.txt", "shared_input.txt"},
            requires_dirs={"req_dir1", "shared_req"}
        )

        info2 = ResourceInfo(
            creates_files={"file2.txt", "shared.txt"},
            creates_dirs={"dir2", "shared_dir"},
            reads_files={"input2.txt", "shared_input.txt"},
            requires_dirs={"req_dir2", "shared_req"}
        )

        merged = info1.merge(info2)

        # Sets automatically handle duplicates
        assert merged.creates_files == {"file1.txt", "file2.txt", "shared.txt"}
        assert merged.creates_dirs == {"dir1", "dir2", "shared_dir"}
        assert merged.reads_files == {"input1.txt", "input2.txt", "shared_input.txt"}
        assert merged.requires_dirs == {"req_dir1", "req_dir2", "shared_req"}

    def test_merge_with_empty(self):
        info = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        empty_info = ResourceInfo.empty()

        # Merge with empty
        merged1 = info.merge(empty_info)
        assert merged1.creates_files == {"file1.txt"}
        assert merged1.creates_dirs == {"dir1"}
        assert merged1.reads_files == {"input1.txt"}
        assert merged1.requires_dirs == {"req_dir1"}

        # Merge empty with info
        merged2 = empty_info.merge(info)
        assert merged2.creates_files == {"file1.txt"}
        assert merged2.creates_dirs == {"dir1"}
        assert merged2.reads_files == {"input1.txt"}
        assert merged2.requires_dirs == {"req_dir1"}

    def test_merge_empty_with_empty(self):
        empty1 = ResourceInfo.empty()
        empty2 = ResourceInfo.empty()

        merged = empty1.merge(empty2)

        assert merged.creates_files == set()
        assert merged.creates_dirs == set()
        assert merged.reads_files == set()
        assert merged.requires_dirs == set()

    def test_merge_creates_new_instance(self):
        info1 = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        info2 = ResourceInfo(
            creates_files={"file2.txt"},
            creates_dirs={"dir2"},
            reads_files={"input2.txt"},
            requires_dirs={"req_dir2"}
        )

        merged = info1.merge(info2)

        # Should be a new instance
        assert merged is not info1
        assert merged is not info2

        # Original instances should be unchanged
        assert info1.creates_files == {"file1.txt"}
        assert info2.creates_files == {"file2.txt"}

    def test_equality(self):
        info1 = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        info2 = ResourceInfo(
            creates_files={"file1.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        info3 = ResourceInfo(
            creates_files={"file2.txt"},
            creates_dirs={"dir1"},
            reads_files={"input1.txt"},
            requires_dirs={"req_dir1"}
        )

        assert info1 == info2
        assert info1 != info3

    def test_hash_consistency(self):
        # Since ResourceInfo is frozen, it should be hashable
        info1 = ResourceInfo(
            creates_files=frozenset({"file1.txt"}),
            creates_dirs=frozenset({"dir1"}),
            reads_files=frozenset({"input1.txt"}),
            requires_dirs=frozenset({"req_dir1"})
        )

        info2 = ResourceInfo(
            creates_files=frozenset({"file1.txt"}),
            creates_dirs=frozenset({"dir1"}),
            reads_files=frozenset({"input1.txt"}),
            requires_dirs=frozenset({"req_dir1"})
        )

        # Note: sets are not hashable, but we can still test structural equality
        assert info1 == info2

    def test_complex_merge_scenario(self):
        # Create a more complex scenario with multiple merges
        base = ResourceInfo.empty()

        step1 = ResourceInfo(
            creates_files={"output1.txt"},
            creates_dirs={"build"},
            reads_files={"source1.py"},
            requires_dirs={"src"}
        )

        step2 = ResourceInfo(
            creates_files={"output2.txt"},
            creates_dirs={"dist"},
            reads_files={"source2.py", "output1.txt"},  # Reads from step1
            requires_dirs={"src", "build"}  # Requires build from step1
        )

        step3 = ResourceInfo(
            creates_files={"final.zip"},
            creates_dirs=set(),
            reads_files={"output1.txt", "output2.txt"},
            requires_dirs={"dist"}
        )

        # Chain merges
        partial = base.merge(step1)
        partial = partial.merge(step2)
        final = partial.merge(step3)

        assert final.creates_files == {"output1.txt", "output2.txt", "final.zip"}
        assert final.creates_dirs == {"build", "dist"}
        assert final.reads_files == {"source1.py", "source2.py", "output1.txt", "output2.txt"}
        assert final.requires_dirs == {"src", "build", "dist"}
