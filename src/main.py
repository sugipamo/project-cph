if __name__ == "__main__":
    import sys
    from src.executor import CommandRunner

    args = sys.argv[1:]
    
    try:
        # コマンド実行の準備と実行
        runner = CommandRunner()
        runner.initialize(args)
        runner.execute(args)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
