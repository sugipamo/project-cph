"""ディレクトリ操作のリソース抽出

ディレクトリ関連のステップからリソース情報を抽出する純粋関数群
"""
from src.workflow.step.step import Step, StepType

from .resource_types import ResourceInfo


def extract_directory_operation_resources(step: Step) -> ResourceInfo:
    """ディレクトリ操作ステップからリソース情報を抽出する純粋関数

    Args:
        step: ディレクトリ操作ステップ

    Returns:
        ResourceInfo: 抽出されたリソース情報
    """
    if step.type == StepType.MKDIR:
        return _extract_mkdir_resources(step)
    if step.type == StepType.MOVETREE:
        return _extract_movetree_resources(step)
    return ResourceInfo.empty()


def _extract_mkdir_resources(step: Step) -> ResourceInfo:
    """MKDIRステップのリソース情報を抽出"""
    if not step.cmd:
        return ResourceInfo.empty()

    dir_path = step.cmd[0]

    return ResourceInfo(
        creates_files=set(),
        creates_dirs={dir_path},
        reads_files=set(),
        requires_dirs=set()
    )


def _extract_movetree_resources(step: Step) -> ResourceInfo:
    """MOVETREEステップのリソース情報を抽出"""
    if not step.cmd or len(step.cmd) < 2:
        return ResourceInfo.empty()

    source_dir = step.cmd[0]
    dest_dir = step.cmd[1]

    return ResourceInfo(
        creates_files=set(),
        creates_dirs={dest_dir},
        reads_files={source_dir},
        requires_dirs=set()
    )
