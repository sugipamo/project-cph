def main(context, operations):
    """
    メイン処理本体。context, operations, controllerは必須。
    """
    from src.env.env_workflow_service import EnvWorkflowService
    service = EnvWorkflowService(context, operations)
    result = service.run_workflow()
    [print(r) for r in result]

if __name__ == "__main__":
    import sys
    import json
    from src.context.user_input_parser import parse_user_input
    from src.env.build_di_container_and_context import build_operations
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
        else:
            print(f"予期せぬエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        sys.exit(1)
