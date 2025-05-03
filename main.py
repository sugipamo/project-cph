import sys
from src.commands import CommandParser, login, open_problem, test_problem, submit_problem

def main():
    args = sys.argv[1:]
    parser = CommandParser()
    parser.parse(args)
    parsed = parser.parsed
    if parsed["command"] == "login":
        login()
    elif parsed["command"] == "open":
        open_problem(parsed["contest_name"], parsed["problem_name"], parsed["language_name"])
    elif parsed["command"] == "test":
        test_problem(parsed["contest_name"], parsed["problem_name"], parsed["language_name"])
    elif parsed["command"] == "submit":
        submit_problem(parsed["contest_name"], parsed["problem_name"], parsed["language_name"])
    else:
        print("コマンドが特定できませんでした。引数を確認してください。")

if __name__ == "__main__":
    main() 