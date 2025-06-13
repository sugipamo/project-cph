"""Docker操作のリソース抽出

Docker関連のステップからリソース情報を抽出する純粋関数群
"""
from src.workflow.step.step import Step, StepType
from .resource_types import ResourceInfo


def extract_docker_operation_resources(step: Step) -> ResourceInfo:
    """Docker操作ステップからリソース情報を抽出する純粋関数
    
    Args:
        step: Docker操作ステップ
        
    Returns:
        ResourceInfo: 抽出されたリソース情報
    """
    if step.type == StepType.DOCKER_RUN:
        return _extract_docker_run_resources(step)
    elif step.type == StepType.DOCKER_EXEC:
        return _extract_docker_exec_resources(step)
    elif step.type == StepType.DOCKER_CP:
        return _extract_docker_cp_resources(step)
    else:
        return ResourceInfo.empty()


def _extract_docker_run_resources(step: Step) -> ResourceInfo:
    """DOCKER_RUNステップのリソース情報を抽出"""
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={"./workspace"}
    )


def _extract_docker_exec_resources(step: Step) -> ResourceInfo:
    """DOCKER_EXECステップのリソース情報を抽出"""
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={"./workspace"}
    )


def _extract_docker_cp_resources(step: Step) -> ResourceInfo:
    """DOCKER_CPステップのリソース情報を抽出"""
    return ResourceInfo(
        creates_files=set(),
        creates_dirs=set(),
        reads_files=set(),
        requires_dirs={"./workspace"}
    )