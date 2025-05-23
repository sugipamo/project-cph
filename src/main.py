def main(context, controller, operations):
    """
    メイン処理本体。context, operations, controllerは必須。
    """
    from src.env.env_workflow_service import EnvWorkflowService
    service = EnvWorkflowService(context, controller, operations)
    result = service.run_workflow()
    print(result)

if __name__ == "__main__":
    import sys
    import json
    from context import parse_user_input
    from src.env.build_di_container_and_context import build_operations_and_context
    from src.env.env_resource_controller import EnvResourceController
    from src.env.resource.file.local_file_handler import LocalFileHandler
    from src.env.resource.run.local_run_handler import LocalRunHandler
    from src.env.resource.utils.const_handler import ConstHandler

    try:
        args = sys.argv[1:]
        context = parse_user_input(args)
        _, operations = build_operations_and_context(context)
        const_handler = ConstHandler(context)
        file_handler = LocalFileHandler(context, const_handler)
        run_handler = LocalRunHandler(context, const_handler)
        controller = EnvResourceController(context, file_handler, run_handler, const_handler)
        main(context, controller, operations)
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
