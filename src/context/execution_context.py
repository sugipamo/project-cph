from dataclasses import dataclass
from typing import Dict, Optional, Tuple

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
    contest_current_path: str
    workspace_path: Optional[str] = None
    dockerfile: Optional[str] = None
    oj_dockerfile: Optional[str] = None
    old_execution_context: Optional["ExecutionContext"] = None
    

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

    def get_env_config(self) -> dict:
        return self.env_json.get('env', {})

    def get_language_config(self) -> dict:
        return self.env_json.get('language', {})

    def get_command_config(self) -> dict:
        return self.env_json.get('command', {})

    def get_contest_config(self) -> dict:
        return self.env_json.get('contest', {})

    def get_problem_config(self) -> dict:
        return self.env_json.get('problem', {}) 