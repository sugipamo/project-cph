import sys
from command_executor import CommandExecutor
from docker_operator import LocalDockerOperator
from contest_file_manager import ContestFileManager
from file_operator import LocalFileOperator
from command_parser import CommandParser

# コマンドライン引数: main.py {contest_name} {command} {problem_name} {language_name}

def print_help():
    print("""
使い方: python3 src/main.py [contest_name] [command] [problem_name] [language_name]

コマンド一覧:
  open (o)     : 問題テンプレート展開＋テストケース取得
  test (t)     : テストケースで実行
  submit (s)   : 提出
  login        : ログイン

引数例:
  python3 src/main.py abc300 open a python
  python3 src/main.py abc300 t b pypy
  python3 src/main.py abc300 s c rust

引数は順不同・エイリアス可
  contest_name: abc300, arc100, agc001, ahc100...
  problem_name: a, b, c, d, e, f, g, ex
  language_name: python, pypy, rust
""")

def main():
    if any(arg in ("--help", "-h") for arg in sys.argv[1:]):
        print_help()
        return

    parser = CommandParser()
    parser.parse(sys.argv[1:])
    args = parser.get_effective_args()
    command = args["command"]
    contest_name = args["contest_name"]
    problem_name = args["problem_name"]
    language_name = args["language_name"]

    # 不足要素があればエラー内容をprintして終了
    if command == "login":
        missing = [k for k in ["command"] if args[k] is None]
    else:
        missing = [k for k in ["contest_name", "command", "problem_name", "language_name"] if args[k] is None]
    if missing:
        print(f"エラー: 以下の要素が不足しています: {', '.join(missing)}")
        print_help()
        return

    executor = CommandExecutor(
        docker_operator=LocalDockerOperator(),
        file_manager=ContestFileManager(LocalFileOperator())
    )
    import asyncio
    if command == "open":
        asyncio.run(executor.open(contest_name, problem_name, language_name))
    elif command == "login":
        asyncio.run(executor.login())
    elif command == "submit":
        asyncio.run(executor.submit(contest_name, problem_name, language_name))
    elif command == "test":
        asyncio.run(executor.run_test(contest_name, problem_name, language_name))
    else:
        print("未対応のコマンドです\n")
        print_help()

if __name__ == "__main__":
    main() 