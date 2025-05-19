from typing import List
from src.execution_context.user_input_parser import UserInputParser

class CommandRunner:
    """
    コマンドライン引数からコマンドを実行するクラス
    """
    @classmethod
    def run(cls, args: List[str]) -> None:
        """
        コマンドを実行する
        
        Args:
            args: コマンドライン引数
            
        Raises:
            ValueError: パースに失敗した場合
        """
        # パーサーの初期化
        context = UserInputParser().from_args(args)
        
        print(context)