import sys
from typing import TextIO, Optional, List

class JudgeInterface:
    def __init__(self, input_file: Optional[TextIO] = None):
        self.input_file = input_file or sys.stdin
        self.query_count = 0
        self.max_queries = 100  # デフォルトのクエリ制限

    def set_max_queries(self, max_queries: int) -> None:
        self.max_queries = max_queries

    def output(self, message: str) -> None:
        print(message, flush=True)

    def input(self) -> str:
        if self.query_count >= self.max_queries:
            self.wrong_answer("クエリ制限超過")
        self.query_count += 1
        return input().strip()

    def correct_answer(self) -> None:
        sys.exit(0)

    def wrong_answer(self, message: str = "") -> None:
        print(f"Wrong Answer: {message}", file=sys.stderr)
        sys.exit(1)

def main():
    judge = JudgeInterface()
    # TODO: インタラクティブジャッジの実装
    # 例: 数当てゲーム
    n = 42
    judge.output("数当てゲームを開始します。1から100の数字を当ててください。")
    
    while True:
        try:
            guess = int(judge.input())
            if guess == n:
                judge.output("正解です！")
                judge.correct_answer()
            elif guess < n:
                judge.output("もっと大きいです")
            else:
                judge.output("もっと小さいです")
        except ValueError:
            judge.wrong_answer("不正な入力です")

if __name__ == "__main__":
    main() 