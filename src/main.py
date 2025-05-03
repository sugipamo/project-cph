import sys
from command_executor import CommandExecutor
from podman_operator import LocalPodmanOperator
from contest_file_manager import ContestFileManager
from file_operator import LocalFileOperator
from commands import CommandParser

# コマンドライン引数: main.py {contest_name} {command} {problem_name} {language_name}

def main():
    parser = CommandParser()
    parser.parse(sys.argv[1:])
    command = parser.parsed["command"]
    contest_name = parser.parsed["contest_name"]
    problem_name = parser.parsed["problem_name"]
    language_name = parser.parsed["language_name"]

    # 不足要素があればエラー内容をprintして終了
    missing = [k for k, v in parser.parsed.items() if v is None]
    if missing:
        print(f"エラー: 以下の要素が不足しています: {', '.join(missing)}")
        return

    executor = CommandExecutor(
        podman_operator=LocalPodmanOperator(),
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
        asyncio.run(executor.test(contest_name, problem_name, language_name))
    else:
        print("未対応のコマンドです")

if __name__ == "__main__":
    main() 