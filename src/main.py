def _get_output_config(context):
    """Get output configuration from shared env.json"""
    try:
        shared_config = context.env_json.get('shared', {})
        return shared_config.get('output', {})
    except (AttributeError, TypeError):
        return {}


def main(context, operations):
    """
    メイン処理本体。context, operations, controllerは必須。
    
    Executes workflow based on context configuration with environment preparation.
    """
    from src.workflow_execution_service import WorkflowExecutionService
    
    # Get output configuration
    output_config = _get_output_config(context)
    
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
    if output_config.get('show_workflow_summary', True):
        successful_steps = sum(1 for r in result.results if r.success)
        print(f"\nワークフロー実行完了: {successful_steps}/{len(result.results)} ステップ成功")
    
    # Show detailed step debug information
    if output_config.get('show_step_details', True):
        print(f"\n=== ステップ実行詳細 ===")
        step_details_config = output_config.get('step_details', {})
        max_command_length = step_details_config.get('max_command_length', 80)
        
        for i, step_result in enumerate(result.results):
            if step_result.success:
                status = "✓ 成功"
            else:
                # Check if failure is allowed
                request = step_result.request if hasattr(step_result, 'request') else None
                allow_failure = getattr(request, 'allow_failure', False) if request else False
                if allow_failure:
                    status = "⚠️ 失敗 (許可済み)"
                else:
                    status = "✗ 失敗"
            print(f"\nステップ {i+1}: {status}")
            
            # Show step type and command if available
            if hasattr(step_result, 'request') and step_result.request:
                req = step_result.request
                if step_details_config.get('show_type', True) and hasattr(req, 'operation_type'):
                    # FileRequestの場合はより具体的なfile operation typeを表示
                    if str(req.operation_type) == "OperationType.FILE" and hasattr(req, 'op'):
                        print(f"  タイプ: FILE.{req.op.name}")
                    else:
                        print(f"  タイプ: {req.operation_type}")
                if step_details_config.get('show_command', True) and hasattr(req, 'cmd') and req.cmd:
                    cmd_str = str(req.cmd)
                    try:
                        if len(cmd_str) > max_command_length:
                            cmd_str = cmd_str[:max_command_length-3] + "..."
                    except (TypeError, ValueError):
                        # Handle cases where max_command_length might be a Mock
                        pass
                    print(f"  コマンド: {cmd_str}")
                if step_details_config.get('show_path', True) and hasattr(req, 'path') and req.path:
                    print(f"  パス: {req.path}")
                if step_details_config.get('show_path', True) and hasattr(req, 'dst_path') and req.dst_path:
                    print(f"  送信先: {req.dst_path}")
            
            # Show execution time if available
            if step_details_config.get('show_execution_time', True):
                if (hasattr(step_result, 'start_time') and hasattr(step_result, 'end_time') and
                    step_result.start_time is not None and step_result.end_time is not None):
                    try:
                        duration = step_result.end_time - step_result.start_time
                        print(f"  実行時間: {duration:.3f}秒")
                    except (TypeError, ValueError):
                        # Handle mock objects or invalid time values
                        pass
            
            # Show output
            if step_details_config.get('show_stdout', True):
                try:
                    if step_result.stdout and step_result.stdout.strip():
                        print(f"  標準出力:")
                        for line in step_result.stdout.strip().split('\n'):
                            print(f"    {line}")
                except (AttributeError, TypeError):
                    # Handle mock objects
                    pass
            
            # Show errors
            if step_details_config.get('show_stderr', True) and not step_result.success:
                try:
                    if step_result.stderr and step_result.stderr.strip():
                        print(f"  標準エラー:")
                        for line in step_result.stderr.strip().split('\n'):
                            print(f"    {line}")
                    elif hasattr(step_result, 'error_message') and step_result.error_message:
                        print(f"  エラー: {step_result.error_message}")
                    elif hasattr(step_result, 'error') and step_result.error:
                        print(f"  エラー: {step_result.error}")
                except (AttributeError, TypeError):
                    # Handle mock objects
                    pass
            
            # Show return code if available
            if step_details_config.get('show_return_code', True):
                try:
                    if hasattr(step_result, 'returncode') and step_result.returncode is not None:
                        print(f"  終了コード: {step_result.returncode}")
                except (AttributeError, TypeError):
                    # Handle mock objects
                    pass
    
    if output_config.get('show_execution_completion', True):
        print(f"\n=== 実行完了 ===")
    
    return result

if __name__ == "__main__":
    import sys
    import json
    from src.context.user_input_parser import parse_user_input
    from src.infrastructure.build_infrastructure import build_operations
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
        from src.shared.exceptions.composite_step_failure import CompositeStepFailure
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
