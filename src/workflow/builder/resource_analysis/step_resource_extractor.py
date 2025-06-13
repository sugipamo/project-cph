"""ステップリソース抽出器

ステップからリソース情報を抽出するメイン関数
"""
from typing import Set, Tuple

from src.workflow.step.step import Step, StepType

from .build_operations import extract_build_operation_resources
from .directory_operations import extract_directory_operation_resources
from .docker_operations import extract_docker_operation_resources
from .file_operations import extract_file_operation_resources
from .resource_types import ResourceInfo


def extract_node_resource_info(step: Step) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """ステップからリソース情報を抽出する純粋関数

    各ステップタイプに応じて適切な抽出関数を呼び出します。

    Args:
        step: 分析対象のステップ

    Returns:
        Tuple[creates_files, creates_dirs, reads_files, requires_dirs]
    """
    result = _extract_resource_info(step)
    return result.creates_files, result.creates_dirs, result.reads_files, result.requires_dirs


def _extract_resource_info(step: Step) -> ResourceInfo:
    """内部的なリソース情報抽出関数"""
    # ステップタイプに応じてリソース情報を抽出
    if step.type in [StepType.COPY, StepType.MOVE, StepType.TOUCH, StepType.REMOVE, StepType.RMTREE]:
        return extract_file_operation_resources(step)

    if step.type in [StepType.MKDIR, StepType.MOVETREE]:
        return extract_directory_operation_resources(step)

    if step.type in [StepType.BUILD, StepType.TEST, StepType.PYTHON, StepType.SHELL]:
        return extract_build_operation_resources(step)

    if step.type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]:
        return extract_docker_operation_resources(step)

    return ResourceInfo.empty()
