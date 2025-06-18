#!/usr/bin/env python3
import sys

sys.path.insert(0, 'src')

print("Starting debug test...")

try:
    print("Importing MinimalCLIApp...")
    from src.cli.cli_app import MinimalCLIApp

    print("Creating app instance...")
    app = MinimalCLIApp()

    # 標準エラー出力を標準出力にリダイレクト
    import contextlib
    import io

    print("Running app with arguments...")
    args = ['abc300', 'open', 'a', 'python', 'local']
    print(f"Arguments: {args}")

    # 標準エラー出力をキャプチャ
    stderr_capture = io.StringIO()
    with contextlib.redirect_stderr(stderr_capture):
        result = app.run(args)

    # キャプチャした内容を表示
    stderr_content = stderr_capture.getvalue()
    if stderr_content:
        print("=== Captured stderr ===")
        print(stderr_content)
        print("======================")

    print(f"Result: {result}")

except Exception as e:
    print(f"Exception caught: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("Debug test complete.")
