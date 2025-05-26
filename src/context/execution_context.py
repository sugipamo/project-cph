from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

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
    workspace_path: Optional[str] = None
    dockerfile: Optional[str] = None
    oj_dockerfile: Optional[str] = None
    old_execution_context: Optional["ExecutionContext"] = None
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
        return self.resolver.resolve(path)

    def get_env_config(self) -> dict:
        return self.env_json['env']

    def get_language_config(self) -> dict:
        return self.env_json['language']

    def get_command_config(self) -> dict:
        return self.env_json['command']

    def get_contest_config(self) -> dict:
        return self.env_json['contest']

    def get_problem_config(self) -> dict:
        return self.env_json['problem']

    def get_steps(self) -> list:
        """
        現在のlanguageとcommand_typeに基づきstepsリストを返す。
        取得できない場合はValueErrorを投げる。
        """
        try:
            return self.env_json[self.language]["commands"][self.command_type]["steps"]
        except Exception as e:
            raise ValueError(f"stepsの取得に失敗しました: {e}")

    @property
    def language_id(self):
        return self.env_json[self.language]["language_id"] 