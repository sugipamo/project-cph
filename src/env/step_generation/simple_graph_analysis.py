"""
シンプルなグラフ分析（networkx不要）
"""
from typing import List, Dict, Set, Tuple
from .step import Step, StepType
from pathlib import Path


def analyze_parallelization_potential(steps: List[Step]) -> Dict[str, object]:
    """ステップリストの並行化可能性を分析"""
    
    # リソース依存関係を分析
    resource_deps = build_resource_dependencies(steps)
    
    # 並行実行可能なグループを特定
    parallel_groups = find_parallel_groups(steps, resource_deps)
    
    # 結果をまとめる
    total_steps = len(steps)
    parallel_potential = sum(len(group) for group in parallel_groups if len(group) > 1)
    
    return {
        'total_steps': total_steps,
        'parallel_groups': parallel_groups,
        'sequential_groups': [group for group in parallel_groups if len(group) == 1],
        'parallelizable_steps': parallel_potential,
        'parallelization_ratio': parallel_potential / total_steps if total_steps > 0 else 0,
        'resource_dependencies': resource_deps
    }


def build_resource_dependencies(steps: List[Step]) -> Dict[int, Set[int]]:
    """ステップ間のリソース依存関係を構築"""
    dependencies = {}
    
    for i, step in enumerate(steps):
        deps = set()
        
        # 現在のステップが必要とするリソース
        required_resources = get_required_resources(step)
        
        # 前のステップが作成するリソースをチェック
        for j in range(i):
            prev_step = steps[j]
            created_resources = get_created_resources(prev_step)
            
            # リソースの重複をチェック
            if required_resources.intersection(created_resources):
                deps.add(j)
        
        dependencies[i] = deps
    
    return dependencies


def get_required_resources(step: Step) -> Set[str]:
    """ステップが必要とするリソースを取得"""
    resources = set()
    
    if step.type in [StepType.COPY, StepType.MOVE]:
        # ソースファイル
        resources.add(f"file:{step.cmd[0]}")
        # 宛先の親ディレクトリ
        parent = str(Path(step.cmd[1]).parent)
        if parent != '.':
            resources.add(f"dir:{parent}")
    
    elif step.type == StepType.TOUCH:
        # 親ディレクトリ
        parent = str(Path(step.cmd[0]).parent)
        if parent != '.':
            resources.add(f"dir:{parent}")
    
    elif step.type in [StepType.REMOVE, StepType.RMTREE]:
        # 削除対象ファイル
        resources.add(f"file:{step.cmd[0]}")
    
    elif step.type == StepType.SHELL and step.cwd:
        # 作業ディレクトリ
        resources.add(f"dir:{step.cwd}")
    
    return resources


def get_created_resources(step: Step) -> Set[str]:
    """ステップが作成するリソースを取得"""
    resources = set()
    
    if step.type == StepType.MKDIR:
        resources.add(f"dir:{step.cmd[0]}")
    
    elif step.type == StepType.TOUCH:
        resources.add(f"file:{step.cmd[0]}")
    
    elif step.type in [StepType.COPY, StepType.MOVE]:
        resources.add(f"file:{step.cmd[1]}")
    
    elif step.type == StepType.MOVETREE:
        resources.add(f"dir:{step.cmd[1]}")
    
    return resources


def find_parallel_groups(steps: List[Step], dependencies: Dict[int, Set[int]]) -> List[List[int]]:
    """並行実行可能なグループを特定"""
    groups = []
    remaining = set(range(len(steps)))
    
    while remaining:
        # 依存関係のないステップを見つける
        ready = []
        for step_idx in remaining:
            deps = dependencies[step_idx]
            if not deps.intersection(remaining):
                ready.append(step_idx)
        
        if not ready:
            # デッドロック状態（通常は発生しない）
            ready = [min(remaining)]
        
        groups.append(ready)
        remaining -= set(ready)
    
    return groups


def compare_workflows_analysis():
    """異なるワークフローパターンの分析比較"""
    
    workflows = {
        "独立ファイル操作": [
            Step(StepType.MKDIR, ['/tmp/dir1']),
            Step(StepType.MKDIR, ['/tmp/dir2']),
            Step(StepType.COPY, ['src1.txt', '/tmp/dir1/dst1.txt']),
            Step(StepType.COPY, ['src2.txt', '/tmp/dir2/dst2.txt']),
        ],
        
        "順次依存チェーン": [
            Step(StepType.TOUCH, ['/tmp/temp.txt']),
            Step(StepType.COPY, ['/tmp/temp.txt', '/tmp/copy.txt']),
            Step(StepType.SHELL, ['cat', '/tmp/copy.txt']),
        ],
        
        "混合パターン": [
            Step(StepType.MKDIR, ['/tmp/a']),
            Step(StepType.MKDIR, ['/tmp/b']),
            Step(StepType.TOUCH, ['/tmp/source.txt']),
            Step(StepType.COPY, ['/tmp/source.txt', '/tmp/a/copy1.txt']),
            Step(StepType.COPY, ['/tmp/source.txt', '/tmp/b/copy2.txt']),
            Step(StepType.SHELL, ['echo', 'done']),
        ]
    }
    
    results = {}
    for name, workflow in workflows.items():
        analysis = analyze_parallelization_potential(workflow)
        results[name] = analysis
    
    return results