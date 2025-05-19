if __name__ == "__main__":
    import sys
    from src.executor import CommandRunner
    from src.execution_context.user_input_parser import UserInputParser
    import json

    try:
        CommandRunner.run(sys.argv[1:])
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
        print(f"予期せぬエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
