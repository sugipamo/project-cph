"""
依存関係解決機能の包括的テスト

Phase 1: dependency.py の15.7% → 95%+ カバレッジ向上を目標
未テストの重要機能をすべて網羅
"""
import pytest
from pathlib import Path
from typing import List, Set

from src.env_core.step.dependency import (
    resolve_dependencies,
    generate_preparation_steps,
    update_resource_tracking
)
from src.env_core.step.step import Step, StepType, StepContext


class TestGeneratePreparationSteps:
    """generate_preparation_steps関数の包括的テスト"""
    
    def setup_method(self):
        """各テストの前に実行される"""
        self.context = StepContext(
            contest_name="test_contest",
            problem_name="test_problem",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="./workspace",
            contest_current_path="./contest_current"
        )
        self.existing_dirs = set()
        self.existing_files = set()
    
    def test_copy_step_requires_destination_directory(self):
        """COPYステップで宛先ディレクトリの作成が必要な場合"""
        copy_step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "target/dest.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            copy_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 宛先ディレクトリ作成ステップが生成される
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ["target"]
        assert prep_steps[0].allow_failure is True
    
    def test_copy_step_destination_directory_exists(self):
        """COPYステップで宛先ディレクトリが既に存在する場合"""
        self.existing_dirs.add("target")
        
        copy_step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "target/dest.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            copy_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 既に存在するため準備ステップは不要
        assert len(prep_steps) == 0
    
    def test_copy_step_destination_is_current_directory(self):
        """COPYステップで宛先が現在ディレクトリの場合"""
        copy_step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "dest.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            copy_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 現在ディレクトリ (.) は準備不要
        assert len(prep_steps) == 0
    
    def test_move_step_requires_destination_directory(self):
        """MOVEステップで宛先ディレクトリの作成が必要な場合"""
        move_step = Step(
            type=StepType.MOVE,
            cmd=["old/file.txt", "new/location/file.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            move_step, self.existing_dirs, self.existing_files, self.context
        )
        
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ["new/location"]
        assert prep_steps[0].allow_failure is True
    
    def test_movetree_step_requires_destination_directory(self):
        """MOVETREEステップで宛先ディレクトリの作成が必要な場合"""
        movetree_step = Step(
            type=StepType.MOVETREE,
            cmd=["old_dir", "new_location/moved_dir"]
        )
        
        prep_steps = generate_preparation_steps(
            movetree_step, self.existing_dirs, self.existing_files, self.context
        )
        
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ["new_location"]
        assert prep_steps[0].allow_failure is True
    
    def test_touch_step_requires_parent_directory(self):
        """TOUCHステップで親ディレクトリの作成が必要な場合"""
        touch_step = Step(
            type=StepType.TOUCH,
            cmd=["deep/nested/dir/file.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            touch_step, self.existing_dirs, self.existing_files, self.context
        )
        
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ["deep/nested/dir"]
        assert prep_steps[0].allow_failure is True
    
    def test_touch_step_parent_directory_exists(self):
        """TOUCHステップで親ディレクトリが既に存在する場合"""
        self.existing_dirs.add("existing_dir")
        
        touch_step = Step(
            type=StepType.TOUCH,
            cmd=["existing_dir/file.txt"]
        )
        
        prep_steps = generate_preparation_steps(
            touch_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 既に存在するため準備不要
        assert len(prep_steps) == 0
    
    def test_working_directory_creation(self):
        """作業ディレクトリが存在しない場合の作成"""
        step_with_cwd = Step(
            type=StepType.SHELL,
            cmd=["echo", "test"],
            cwd="nonexistent/workdir"
        )
        
        prep_steps = generate_preparation_steps(
            step_with_cwd, self.existing_dirs, self.existing_files, self.context
        )
        
        assert len(prep_steps) == 1
        assert prep_steps[0].type == StepType.MKDIR
        assert prep_steps[0].cmd == ["nonexistent/workdir"]
        assert prep_steps[0].allow_failure is True
    
    def test_working_directory_exists(self):
        """作業ディレクトリが既に存在する場合"""
        self.existing_dirs.add("existing_workdir")
        
        step_with_cwd = Step(
            type=StepType.SHELL,
            cmd=["echo", "test"],
            cwd="existing_workdir"
        )
        
        prep_steps = generate_preparation_steps(
            step_with_cwd, self.existing_dirs, self.existing_files, self.context
        )
        
        # 既に存在するため準備不要
        assert len(prep_steps) == 0
    
    def test_complex_step_multiple_preparations(self):
        """複数の準備が必要な複雑なステップ"""
        complex_step = Step(
            type=StepType.COPY,
            cmd=["src.txt", "deep/nested/target.txt"],
            cwd="work/directory"
        )
        
        prep_steps = generate_preparation_steps(
            complex_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 宛先ディレクトリと作業ディレクトリの両方が必要
        assert len(prep_steps) == 2
        
        # 順序は重要ではないが、両方とも MKDIR である必要がある
        mkdir_commands = [step.cmd[0] for step in prep_steps if step.type == StepType.MKDIR]
        assert "deep/nested" in mkdir_commands
        assert "work/directory" in mkdir_commands
    
    def test_no_preparation_needed(self):
        """準備が不要なステップ"""
        simple_step = Step(
            type=StepType.SHELL,
            cmd=["echo", "hello"]
        )
        
        prep_steps = generate_preparation_steps(
            simple_step, self.existing_dirs, self.existing_files, self.context
        )
        
        assert len(prep_steps) == 0
    
    def test_shell_command_no_preparation(self):
        """シェルコマンドでは準備ステップは生成されない"""
        shell_step = Step(
            type=StepType.SHELL,
            cmd=["echo", "test"]
        )
        
        prep_steps = generate_preparation_steps(
            shell_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # SHELLステップでは準備ステップは生成されない
        assert len(prep_steps) == 0
    
    def test_edge_case_current_directory_copy(self):
        """現在ディレクトリ内でのコピー"""
        copy_step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "./dest.txt"]  # 明示的な現在ディレクトリ
        )
        
        prep_steps = generate_preparation_steps(
            copy_step, self.existing_dirs, self.existing_files, self.context
        )
        
        # 現在ディレクトリなので準備不要
        assert len(prep_steps) == 0


class TestUpdateResourceTracking:
    """update_resource_tracking関数の包括的テスト"""
    
    def setup_method(self):
        """各テストの前に実行される"""
        self.existing_dirs = set()
        self.existing_files = set()
    
    def test_mkdir_tracking(self):
        """MKDIRステップでのディレクトリ追跡"""
        mkdir_step = Step(
            type=StepType.MKDIR,
            cmd=["new_directory"]
        )
        
        update_resource_tracking(mkdir_step, self.existing_dirs, self.existing_files)
        
        assert "new_directory" in self.existing_dirs
        assert len(self.existing_files) == 0
    
    def test_touch_tracking(self):
        """TOUCHステップでのファイル追跡"""
        touch_step = Step(
            type=StepType.TOUCH,
            cmd=["new_file.txt"]
        )
        
        update_resource_tracking(touch_step, self.existing_dirs, self.existing_files)
        
        assert "new_file.txt" in self.existing_files
        assert len(self.existing_dirs) == 0
    
    def test_copy_tracking(self):
        """COPYステップでの宛先ファイル追跡"""
        copy_step = Step(
            type=StepType.COPY,
            cmd=["source.txt", "destination.txt"]
        )
        
        update_resource_tracking(copy_step, self.existing_dirs, self.existing_files)
        
        assert "destination.txt" in self.existing_files
        assert len(self.existing_dirs) == 0
    
    def test_move_tracking(self):
        """MOVEステップでの宛先ファイル追跡"""
        move_step = Step(
            type=StepType.MOVE,
            cmd=["source.txt", "moved.txt"]
        )
        
        update_resource_tracking(move_step, self.existing_dirs, self.existing_files)
        
        # 宛先ファイルが追加される
        assert "moved.txt" in self.existing_files
        # 実装では元ファイルは削除追跡しない
    
    def test_movetree_tracking(self):
        """MOVETREEステップでのディレクトリ移動追跡"""
        movetree_step = Step(
            type=StepType.MOVETREE,
            cmd=["old_dir", "new_dir"]
        )
        
        update_resource_tracking(movetree_step, self.existing_dirs, self.existing_files)
        
        # 宛先ディレクトリが追加される
        assert "new_dir" in self.existing_dirs
        # 実装では元ディレクトリは削除追跡しない
    
    def test_rmtree_tracking(self):
        """RMTREEステップでのディレクトリ削除追跡"""
        # 削除対象ディレクトリが追跡済みの状態を模擬
        self.existing_dirs.add("dir_to_remove")
        
        rmtree_step = Step(
            type=StepType.RMTREE,
            cmd=["dir_to_remove"]
        )
        
        update_resource_tracking(rmtree_step, self.existing_dirs, self.existing_files)
        
        # ディレクトリが削除される
        assert "dir_to_remove" not in self.existing_dirs
    
    def test_remove_tracking(self):
        """REMOVEステップでのファイル削除追跡"""
        # 削除対象ファイルが追跡済みの状態を模擬
        self.existing_files.add("file_to_remove.txt")
        
        remove_step = Step(
            type=StepType.REMOVE,
            cmd=["file_to_remove.txt"]
        )
        
        update_resource_tracking(remove_step, self.existing_dirs, self.existing_files)
        
        # ファイルが削除される
        assert "file_to_remove.txt" not in self.existing_files
    
    def test_no_tracking_for_non_resource_steps(self):
        """リソース操作以外のステップでは追跡されない"""
        shell_step = Step(
            type=StepType.SHELL,
            cmd=["echo", "hello"]
        )
        
        update_resource_tracking(shell_step, self.existing_dirs, self.existing_files)
        
        # 何も変更されない
        assert len(self.existing_dirs) == 0
        assert len(self.existing_files) == 0
    
    def test_mkdir_with_parent_directory(self):
        """MKDIRステップでディレクトリとその親ディレクトリの追跡"""
        mkdir_step = Step(
            type=StepType.MKDIR,
            cmd=["nested/deep/directory"]
        )
        
        update_resource_tracking(mkdir_step, self.existing_dirs, self.existing_files)
        
        # 作成されたディレクトリが追跡される
        assert "nested/deep/directory" in self.existing_dirs
        assert len(self.existing_files) == 0
    
    def test_touch_creates_parent_directories(self):
        """TOUCHステップで親ディレクトリも作成される"""
        touch_step = Step(
            type=StepType.TOUCH,
            cmd=["deep/nested/file.txt"]
        )
        
        update_resource_tracking(touch_step, self.existing_dirs, self.existing_files)
        
        # ファイルと親ディレクトリが追跡される
        assert "deep/nested/file.txt" in self.existing_files
        assert "deep/nested" in self.existing_dirs


class TestResolveDependencies:
    """resolve_dependencies関数の統合テスト"""
    
    def setup_method(self):
        """各テストの前に実行される"""
        self.context = StepContext(
            contest_name="test_contest",
            problem_name="test_problem",
            language="python",
            env_type="local",
            command_type="test",
            workspace_path="./workspace",
            contest_current_path="./contest_current"
        )
    
    def test_simple_dependency_resolution(self):
        """単純な依存関係の解決"""
        steps = [
            Step(type=StepType.COPY, cmd=["src.txt", "nested/dest.txt"])
        ]
        
        resolved = resolve_dependencies(steps, self.context)
        
        # 準備ステップ（MKDIR）+ 元のステップ
        assert len(resolved) == 2
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ["nested"]
        assert resolved[1] == steps[0]
    
    def test_complex_dependency_resolution(self):
        """複雑な依存関係の解決"""
        steps = [
            Step(type=StepType.COPY, cmd=["a.txt", "temp/a_copy.txt"]),
            Step(type=StepType.TOUCH, cmd=["temp/b.txt"]),
            Step(type=StepType.COPY, cmd=["temp/b.txt", "output/result.txt"])
        ]
        
        resolved = resolve_dependencies(steps, self.context)
        
        # 期待される構造：
        # 1. MKDIR temp (for first COPY)
        # 2. COPY a.txt temp/a_copy.txt
        # 3. TOUCH temp/b.txt (tempは既に作成済み)
        # 4. MKDIR output (for second COPY)
        # 5. COPY temp/b.txt output/result.txt
        
        assert len(resolved) == 5
        assert resolved[0].type == StepType.MKDIR  # temp directory
        assert resolved[0].cmd == ["temp"]
        assert resolved[1] == steps[0]  # first copy
        assert resolved[2] == steps[1]  # touch (no prep needed)
        assert resolved[3].type == StepType.MKDIR  # output directory
        assert resolved[3].cmd == ["output"]
        assert resolved[4] == steps[2]  # second copy
    
    def test_no_dependencies_needed(self):
        """依存関係が不要な場合"""
        steps = [
            Step(type=StepType.SHELL, cmd=["echo", "hello"]),
            Step(type=StepType.TOUCH, cmd=["simple.txt"])
        ]
        
        resolved = resolve_dependencies(steps, self.context)
        
        # 準備ステップは不要、元のステップのみ
        assert len(resolved) == 2
        assert resolved == steps
    
    def test_directory_reuse_optimization(self):
        """ディレクトリ再利用の最適化"""
        steps = [
            Step(type=StepType.COPY, cmd=["a.txt", "shared/a.txt"]),
            Step(type=StepType.COPY, cmd=["b.txt", "shared/b.txt"])
        ]
        
        resolved = resolve_dependencies(steps, self.context)
        
        # sharedディレクトリは一度だけ作成される
        assert len(resolved) == 3
        assert resolved[0].type == StepType.MKDIR
        assert resolved[0].cmd == ["shared"]
        assert resolved[1] == steps[0]
        assert resolved[2] == steps[1]  # 2番目のCOPYに追加の準備は不要
    
    def test_empty_steps_list(self):
        """空のステップリスト"""
        steps = []
        
        resolved = resolve_dependencies(steps, self.context)
        
        assert len(resolved) == 0
        assert resolved == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])