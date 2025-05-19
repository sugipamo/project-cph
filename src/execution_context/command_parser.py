from typing import List, Dict, Optional

class CommandParser:
    """
    コマンド名・エイリアス解決など、コマンド判定の共通ロジックを提供するクラス。
    UserInputParserやCommandRegistryから利用されることを想定。
    """
    @staticmethod
    def match_name_or_alias(target: str, name: str, aliases: Optional[List[str]] = None) -> bool:
        """
        targetがnameまたはaliasesのいずれかと一致するか判定
        """
        if target == name:
            return True
        if aliases:
            return target in aliases
        return False

    @staticmethod
    def find_match(targets: List[str], name: str, aliases: Optional[List[str]] = None) -> Optional[str]:
        """
        targetsリスト内にnameまたはaliasesと一致するものがあれば返す
        """
        for t in targets:
            if CommandParser.match_name_or_alias(t, name, aliases):
                return t
        return None 