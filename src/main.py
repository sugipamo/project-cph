def main():
    """
    メイン処理本体。context, operationsは必須。
    """
    from src.env.env_workflow_service import EnvWorkflowService
    from context import ExecutionContext, parse_user_input
    import sys

    args = sys.argv[1:]
    try:
        context = parse_user_input(args)
    except Exception as e:
        print(f"[ERROR] 入力パース失敗: {e}")
        sys.exit(1)

    service = EnvWorkflowService.from_context(context)
    result = service.run_workflow()
    print(result)

if __name__ == "__main__":
    import sys
    import json
    from src.env.build_di_container_and_context import build_operations_and_context

    try:
        main()
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
