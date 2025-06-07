#!/usr/bin/env python3
"""
並列実行機能のデモンストレーション
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.workflow_execution_service import WorkflowExecutionService
from src.context.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_operations

def demo_parallel_execution():
    """並列実行のデモ"""
    
    # オペレーションとコンテキストを設定
    operations = build_operations()
    
    # 複数のタスクを含むコマンドをシミュレート
    # 実際のユーザー入力の代わりにモックデータを使用
    test_args = ["python", "abc300", "open", "a"]
    context = parse_user_input(test_args, operations)
    
    print("=== 並列実行デモ ===")
    
    # 順次実行
    print("\n1. 順次実行:")
    service = WorkflowExecutionService(context, operations)
    start_time = time.time()
    result = service.execute_workflow(parallel=False)
    sequential_time = time.time() - start_time
    print(f"   実行時間: {sequential_time:.3f}秒")
    print(f"   成功: {result.success}")
    print(f"   ステップ数: {len(result.results)}")
    
    # 並列実行
    print("\n2. 並列実行:")
    service = WorkflowExecutionService(context, operations)
    start_time = time.time()
    result = service.execute_workflow(parallel=True, max_workers=4)
    parallel_time = time.time() - start_time
    print(f"   実行時間: {parallel_time:.3f}秒")
    print(f"   成功: {result.success}")
    print(f"   ステップ数: {len(result.results)}")
    
    # パフォーマンス比較
    improvement = ((sequential_time - parallel_time) / sequential_time) * 100
    print(f"\n3. パフォーマンス改善:")
    print(f"   改善率: {improvement:.1f}%")
    
    # 実行の詳細分析
    print(f"\n4. 実行詳細:")
    for i, step_result in enumerate(result.results):
        print(f"   ステップ {i+1}: {step_result.operation_type} - {'成功' if step_result.success else '失敗'}")

if __name__ == "__main__":
    import time
    demo_parallel_execution()