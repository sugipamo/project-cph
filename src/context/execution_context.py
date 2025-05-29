from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
from src.context.utils.format_utils import format_with_missing_keys

@dataclass
class ExecutionContext:
    """
    実行コンテキストを保持するクラス。
    パース結果の保持、バリデーション、環境設定の取得を担当。
    """
    command_type: str
    language: str
    contest_name: str
    problem_name: str
    env_type: str
    env_json: dict
    resolver: Optional[object] = None  # ConfigResolver型（循環import回避のためobject型で）
    

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        基本的なバリデーションを行う
        
        Returns:
            Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
        """
        # 必須項目の存在チェック
        missing_fields = []
        if not self.command_type:
            missing_fields.append("コマンド")
        if not self.language:
            missing_fields.append("言語")
        if not self.contest_name:
            missing_fields.append("コンテスト名")
        if not self.problem_name:
            missing_fields.append("問題名")
            
        if missing_fields:
            return False, f"以下の項目が指定されていません: {', '.join(missing_fields)}"
            
        # env_jsonの存在チェック
        if not self.env_json:
            return False, "環境設定ファイル(env.json)が見つかりません"
            
        # 言語がenv_jsonに存在するかチェック
        if self.language not in self.env_json:
            return False, f"指定された言語 '{self.language}' は環境設定ファイルに存在しません"

        return True, None

    def resolve(self, path: List[str]):
        """
        resolverを使ってパスで設定値ノードを解決する
        """
        if not self.resolver:
            raise ValueError("resolverがセットされていません")
        from src.context.resolver.config_resolver import resolve_best
        return resolve_best(self.resolver, path)

    @property
    def workspace_path(self):
        node = self.resolve([self.language, "workspace_path"])
        return node.value if node else None

    @property
    def contest_current_path(self):
        node = self.resolve([self.language, "contest_current_path"])
        return node.value if node else None

    def get_steps(self) -> list:
        """
        現在のlanguageとcommand_typeに基づきstepsのConfigNodeリストを返す。
        取得できない場合はValueErrorを投げる。
        """
        try:
            steps_node = self.resolve([self.language, "commands", self.command_type, "steps"])
            if not steps_node:
                raise ValueError("stepsが見つかりません")
            
            # steps配列の各要素のConfigNodeを返す
            step_nodes = []
            for child in steps_node.next_nodes:
                if isinstance(child.key, int):  # 配列のインデックス
                    step_nodes.append(child)
            
            # インデックス順にソート
            step_nodes.sort(key=lambda n: n.key)
            return step_nodes
        except Exception as e:
            raise ValueError(f"stepsの取得に失敗しました: {e}")

    @property
    def language_id(self):
        node = self.resolve([self.language, "language_id"])
        return node.value if node else None
