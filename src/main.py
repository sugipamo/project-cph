def main(args, user_input_parser, operations):
    """
    メイン処理本体。args, user_input_parser, operationsは必須。
    """
    context = user_input_parser.from_args(args)
    from src.env.env_workflow_service import EnvWorkflowService
    service = EnvWorkflowService.from_context(context, operations)
    result = service.run_workflow()
    print(result)

if __name__ == "__main__":
    import sys
    import json
    from src.context.user_input_parser import UserInputParser, LocalSystemInfoProvider
    from src.env.build_di_container_and_context import build_operations_and_context

    args = sys.argv[1:]
    user_input_parser = UserInputParser(LocalSystemInfoProvider())
    # contextはUserInputParserで生成
    context = user_input_parser.from_args(args)
    _, operations = build_operations_and_context(context)

    try:
        main(args, user_input_parser, operations)
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
