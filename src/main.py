def main(context, operations):
    """
    メイン処理本体。context, operations, controllerは必須。
    
    Executes workflow based on context configuration with environment preparation.
    """
    from src.workflow_execution_service import WorkflowExecutionService
    
    # Create workflow execution service
    service = WorkflowExecutionService(context, operations)
    
    # Execute workflow with fitting
    result = service.execute_workflow(parallel=False)
    
    # Handle results
    if result.preparation_results:
        print(f"準備タスク実行: {len(result.preparation_results)} 件")
        for i, prep_result in enumerate(result.preparation_results):
            if prep_result.success:
                print(f"  ✓ 準備タスク {i+1}: 成功")
            else:
                print(f"  ✗ 準備タスク {i+1}: 失敗 - {prep_result.get_error_output()}")
    
    if result.warnings:
        for warning in result.warnings:
            print(f"警告: {warning}")
    
    if not result.success:
        for error in result.errors:
            print(f"エラー: {error}")
        raise Exception("ワークフロー実行に失敗しました")
    
    # Show results summary
    successful_steps = sum(1 for r in result.results if r.success)
    print(f"\nワークフロー実行完了: {successful_steps}/{len(result.results)} ステップ成功")
    
    # Show output from steps that produced output
    for i, step_result in enumerate(result.results):
        if step_result.stdout and step_result.stdout.strip():
            print(f"\nステップ {i+1} の出力:")
            print(step_result.stdout)
    
    return result

if __name__ == "__main__":
    import sys
    import json
    from src.context.user_input_parser import parse_user_input
    from src.env.build_operations import build_operations
    try:
        operations = build_operations()
        context = parse_user_input(sys.argv[1:], operations)
        main(context, operations)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSONの解析に失敗しました: {e}")
        sys.exit(1)
    except Exception as e:
        from src.operations.exceptions.composite_step_failure import CompositeStepFailure
        if isinstance(e, CompositeStepFailure):
            print(f"ユーザー定義コマンドでエラーが発生しました: {e}")
            if hasattr(e, 'result') and e.result is not None:
                try:
                    print(e.result.get_error_output())
                except Exception:
                    pass
        else:
            print(f"予期せぬエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        sys.exit(1)
