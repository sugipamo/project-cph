#!/usr/bin/env python3
"""
結果置換機能のデモンストレーション
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.env_core.workflow.request_execution_graph import RequestExecutionGraph, RequestNode
from src.operations.shell.shell_request import ShellRequest
from src.operations.result.result import OperationResult

def demo_result_substitution():
    """結果置換機能のデモ"""
    
    print("=== 結果置換機能デモ ===")
    
    # グラフを作成
    graph = RequestExecutionGraph()
    
    # ステップ1: テストコマンドを実行
    test_request = ShellRequest(cmd=["echo", "Test passed: 5/5"], show_output=True)
    test_node = RequestNode("test", test_request)
    graph.add_request_node(test_node)
    
    # ステップ2: テスト結果を使用するコマンド
    result_request = ShellRequest(
        cmd=["echo", "Previous result: {{step_test.stdout}} (code: {{step_test.returncode}})"], 
        show_output=True
    )
    result_node = RequestNode("result", result_request)
    graph.add_request_node(result_node)
    
    print("\n1. 置換前のコマンド:")
    print(f"   test: {test_request.cmd}")
    print(f"   result: {result_request.cmd}")
    
    # テスト結果をシミュレート
    test_result = OperationResult(
        success=True,
        returncode=0,
        stdout="Test passed: 5/5",
        stderr="",
    )
    graph.execution_results["test"] = test_result
    
    print("\n2. 実行結果を蓄積:")
    print(f"   test結果: stdout='{test_result.stdout}', returncode={test_result.returncode}")
    
    # 結果置換を適用
    graph.apply_result_substitution_to_request(result_request, "result")
    
    print("\n3. 置換後のコマンド:")
    print(f"   result: {result_request.cmd}")
    
    # 置換の例をいくつか表示
    print("\n4. 置換パターンの例:")
    examples = [
        "{{step_test.stdout}}",
        "{{step_test.returncode}}",
        "{{step_test.result.success}}",
        "Result: {{step_test.stdout}} with code {{step_test.returncode}}"
    ]
    
    for example in examples:
        substituted = graph.substitute_result_placeholders(example)
        print(f"   '{example}' -> '{substituted}'")

def demo_complex_substitution():
    """複雑な置換パターンのデモ"""
    
    print("\n=== 複雑な置換パターンデモ ===")
    
    graph = RequestExecutionGraph()
    
    # 複数のステップ結果をシミュレート
    results = {
        "compile": OperationResult(success=True, returncode=0, stdout="Compilation successful"),
        "test": OperationResult(success=True, returncode=0, stdout="5 tests passed", stderr=""),
        "benchmark": OperationResult(success=True, returncode=0, stdout="Execution time: 1.23s")
    }
    
    graph.execution_results.update(results)
    
    # 複雑な置換パターン
    patterns = [
        "Build: {{step_compile.stdout}}, Tests: {{step_test.stdout}}, Performance: {{step_benchmark.stdout}}",
        "if [[ {{step_test.returncode}} -eq 0 ]]; then echo 'Success'; fi",
        "echo 'Results: compile={{step_compile.success}}, test={{step_test.success}}'",
        "mkdir results_{{step_test.returncode}}_{{step_benchmark.returncode}}"
    ]
    
    for i, pattern in enumerate(patterns, 1):
        substituted = graph.substitute_result_placeholders(pattern)
        print(f"{i}. '{pattern}'")
        print(f"   -> '{substituted}'")
        print()

if __name__ == "__main__":
    demo_result_substitution()
    demo_complex_substitution()