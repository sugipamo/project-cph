if __name__ == "__main__":
    import sys
    from src.executor import CommandRunner

    try:
        CommandRunner.run(sys.argv[1:])
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
