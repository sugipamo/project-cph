"""ビルド操作のリソース抽出

ビルド関連のステップからリソース情報を抽出する純粋関数群
"""
from pathlib import Path
from src.workflow.step.step import Step, StepType
from .resource_types import ResourceInfo


def extract_build_operation_resources(step: Step) -> ResourceInfo:
    """ビルド操作ステップからリソース情報を抽出する純粋関数
    
    Args:
        step: ビルド操作ステップ
        
    Returns:
        ResourceInfo: 抽出されたリソース情報
    """
    if step.type == StepType.BUILD:
        return _extract_build_resources(step)
    elif step.type == StepType.TEST:
        return _extract_test_resources(step)
    elif step.type in [StepType.PYTHON, StepType.SHELL]:
        return _extract_script_resources(step)
    else:
        return ResourceInfo.empty()


def _extract_build_resources(step: Step) -> ResourceInfo:
    """BUILDステップのリソース情報を抽出"""
    if step.cmd and step.cmd[0]:
        build_dir = step.cmd[0]
    else:
        build_dir = "./workspace"
        
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={build_dir}
    )


def _extract_test_resources(step: Step) -> ResourceInfo:
    """TESTステップのリソース情報を抽出"""
    if len(step.cmd) < 2:
        return ResourceInfo(
            creates_files=set(),
            creates_dirs=set(),
            reads_files=set(),
            requires_dirs={"./workspace"}
        )
        
    target_file = step.cmd[1]
    parent_dir = str(Path(target_file).parent)
    
    requires_dirs = set()
    if parent_dir != '.':
        requires_dirs.add(parent_dir)
    
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files={target_file},
        requires_dirs=requires_dirs
    )


def _extract_script_resources(step: Step) -> ResourceInfo:
    """スクリプト実行ステップのリソース情報を抽出"""
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={"./workspace"}
    )