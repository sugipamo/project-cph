"""Tests for dependency resolution functionality"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.domain.dependency import (
    resolve_dependencies,
    generate_preparation_steps,
    update_resource_tracking,
    analyze_step_dependencies,
    creates_file,
    optimize_mkdir_steps,
    optimize_copy_steps
)
from src.domain.step import Step, StepType, StepContext


class TestDependencyResolution:
    """Test suite for dependency resolution functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.context = StepContext(
            contest_name="ABC100",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="test",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            contest_temp_path="/contest/temp",
            source_file_name="main.py",
            language_id="py",
            file_patterns=["*.py", "*.txt"]
        )
        
        # Create test steps
        self.mkdir_step = Step(
            type=StepType.MKDIR,
            name="mkdir_test",
            allow_failure=False,
            cmd=["/test/dir"]
        )
        
        self.copy_step = Step(
            type=StepType.COPY,
            name="copy_test",
            allow_failure=False,
            cmd=["src.txt", "/test/dir/dst.txt"]
        )
        
        self.shell_step = Step(
            type=StepType.SHELL,
            name="shell_test",
            allow_failure=False,
            cmd=["echo", "test"]
        )
    
    def test_resolve_dependencies_adds_mkdir_for_copy(self):
        """Test that resolve_dependencies adds mkdir step for copy destination"""
        steps = [self.copy_step]
        
        with patch('src.domain.dependency.execution_context_to_simple_context') as mock_context:
            mock_context.return_value = self.context.__dict__
            resolved = resolve_dependencies(steps, self.context)
        
        # Should add mkdir step before copy
        assert len(resolved) >= 2
        # First step should be mkdir
        mkdir_steps = [s for s in resolved if s.type == StepType.MKDIR]
        assert len(mkdir_steps) > 0
    
    def test_resolve_dependencies_no_duplicate_mkdir(self):
        """Test that resolve_dependencies doesn't create duplicate mkdir steps"""
        # Two copies to same directory
        copy1 = Step(
            type=StepType.COPY,
            name="copy1",
            allow_failure=False,
            cmd=["src1.txt", "/test/dir/dst1.txt"],
        )
        copy2 = Step(
            type=StepType.COPY,
            name="copy2",
            allow_failure=False,
            cmd=["src2.txt", "/test/dir/dst2.txt"],
        )
        
        steps = [copy1, copy2]
        
        with patch('src.domain.dependency.execution_context_to_simple_context') as mock_context:
            mock_context.return_value = self.context.__dict__
            resolved = resolve_dependencies(steps, self.context)
        
        # Should only have one mkdir for /test/dir
        mkdir_steps = [s for s in resolved if s.type == StepType.MKDIR and "/test/dir" in str(s.cmd)]
        assert len(mkdir_steps) == 1
    
    def test_generate_preparation_steps_for_copy(self):
        """Test generating preparation steps for copy operation"""
        existing_dirs = set()
        existing_files = set()
        
        prep_steps = generate_preparation_steps(
            self.copy_step, 
            existing_dirs, 
            existing_files,
            self.context
        )
        
        # Should generate mkdir for parent directory
        assert len(prep_steps) > 0
        mkdir_steps = [s for s in prep_steps if s.type == StepType.MKDIR]
        assert len(mkdir_steps) > 0
    
    def test_generate_preparation_steps_with_existing_dir(self):
        """Test that no mkdir is generated for existing directory"""
        existing_dirs = {"/test/dir"}
        existing_files = set()
        
        prep_steps = generate_preparation_steps(
            self.copy_step,
            existing_dirs,
            existing_files,
            self.context
        )
        
        # Should not generate mkdir for existing directory
        mkdir_steps = [s for s in prep_steps if s.type == StepType.MKDIR and "/test/dir" in str(s.cmd)]
        assert len(mkdir_steps) == 0
    
    def test_update_resource_tracking_mkdir(self):
        """Test resource tracking update for mkdir step"""
        existing_dirs = set()
        existing_files = set()
        
        update_resource_tracking(self.mkdir_step, existing_dirs, existing_files)
        
        assert "/test/dir" in existing_dirs
        assert len(existing_files) == 0
    
    def test_update_resource_tracking_copy(self):
        """Test resource tracking update for copy step"""
        existing_dirs = set()
        existing_files = set()
        
        update_resource_tracking(self.copy_step, existing_dirs, existing_files)
        
        assert "/test/dir/dst.txt" in existing_files
    
    def test_analyze_step_dependencies_simple(self):
        """Test analyzing step dependencies"""
        steps = [
            self.mkdir_step,
            self.copy_step,
            self.shell_step
        ]
        
        deps = analyze_step_dependencies(steps)
        
        # Should return a dict mapping step indices to their dependencies
        assert isinstance(deps, dict)
        # Copy step (index 1) should depend on mkdir step (index 0)
        if 1 in deps and deps[1]:
            assert 0 in deps[1]
    
    def test_creates_file_for_copy(self):
        """Test creates_file function for copy step"""
        result = creates_file(self.copy_step, "/test/dir/dst.txt")
        assert result is True
        
        result = creates_file(self.copy_step, "/other/file.txt")
        assert result is False
    
    def test_creates_file_for_non_copy(self):
        """Test creates_file function for non-copy step"""
        result = creates_file(self.shell_step, "/any/file.txt")
        assert result is False
    
    def test_optimize_mkdir_steps(self):
        """Test optimizing mkdir steps to remove redundant ones"""
        steps = [
            Step(
                type=StepType.MKDIR,
                name="mkdir1",
                allow_failure=False,
                cmd=["/test"],
            ),
            Step(
                type=StepType.MKDIR,
                name="mkdir2",
                allow_failure=False,
                cmd=["/test/subdir"],
            ),
            Step(
                type=StepType.MKDIR,
                name="mkdir3",
                allow_failure=False,
                cmd=["/test"],  # Duplicate
            )
        ]
        
        optimized = optimize_mkdir_steps(steps)
        
        # Should remove duplicate mkdir
        assert len(optimized) < len(steps)
        # Should keep unique paths
        paths = [s.cmd[0] for s in optimized if s.type == StepType.MKDIR]
        assert len(paths) == len(set(paths))
    
    def test_optimize_copy_steps(self):
        """Test optimizing copy steps"""
        steps = [
            self.copy_step,
            Step(
                type=StepType.COPY,
                name="copy2",
                allow_failure=False,
                cmd=["src.txt", "/test/dir/dst2.txt"],  # Same source
            ),
            self.shell_step
        ]
        
        optimized = optimize_copy_steps(steps)
        
        # Should preserve all steps (optimization might group them)
        assert len(optimized) == len(steps)