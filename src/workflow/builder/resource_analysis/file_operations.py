"""ファイル操作のリソース抽出

ファイル関連のステップからリソース情報を抽出する純粋関数群
"""
from pathlib import Path

from src.workflow.step.step import Step, StepType

from .resource_types import ResourceInfo


def extract_file_operation_resources(step: Step) -> ResourceInfo:
    """ファイル操作ステップからリソース情報を抽出する純粋関数

    Args:
        step: ファイル操作ステップ

    Returns:
        ResourceInfo: 抽出されたリソース情報
    """
    if step.type == StepType.TOUCH:
        return _extract_touch_resources(step)
    if step.type == StepType.COPY:
        return _extract_copy_resources(step)
    if step.type == StepType.MOVE:
        return _extract_move_resources(step)
    if step.type == StepType.REMOVE:
        return _extract_remove_resources(step)
    if step.type == StepType.RMTREE:
        return _extract_rmtree_resources(step)
    return ResourceInfo.empty()


def _extract_touch_resources(step: Step) -> ResourceInfo:
    """TOUCHステップのリソース情報を抽出"""
    if not step.cmd:
        return ResourceInfo.empty()

    file_path = step.cmd[0]
    parent_dir = str(Path(file_path).parent)

    return ResourceInfo(
        creates_files={file_path},
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={parent_dir} if parent_dir != '.' else set()
    )


def _extract_copy_resources(step: Step) -> ResourceInfo:
    """COPYステップのリソース情報を抽出"""
    if len(step.cmd) < 2:
        return ResourceInfo.empty()

    source_path = step.cmd[0]
    dest_path = step.cmd[1]
    dest_parent = str(Path(dest_path).parent)

    return ResourceInfo(
        creates_files={dest_path},
        creates_dirs=set(),
        reads_files={source_path},
        requires_dirs={dest_parent} if dest_parent != '.' else set()
    )


def _extract_move_resources(step: Step) -> ResourceInfo:
    """MOVEステップのリソース情報を抽出"""
    if len(step.cmd) < 2:
        return ResourceInfo.empty()

    source_path = step.cmd[0]
    dest_path = step.cmd[1]
    dest_parent = str(Path(dest_path).parent)

    return ResourceInfo(
        creates_files={dest_path},
        creates_dirs=set(),
        reads_files={source_path},
        requires_dirs={dest_parent} if dest_parent != '.' else set()
    )


def _extract_remove_resources(step: Step) -> ResourceInfo:
    """REMOVEステップのリソース情報を抽出"""
    if not step.cmd:
        return ResourceInfo.empty()

    target_path = step.cmd[0]

    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files={target_path},
        requires_dirs=set()
    )


def _extract_rmtree_resources(step: Step) -> ResourceInfo:
    """RMTREEステップのリソース情報を抽出"""
    if not step.cmd:
        return ResourceInfo.empty()

    target_path = step.cmd[0]

    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files={target_path},
        requires_dirs=set()
    )
