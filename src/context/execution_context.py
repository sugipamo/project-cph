from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
from src.context.utils.format_utils import format_with_missing_keys
from src.context.utils.validation_utils import validate_execution_context_data, get_steps_from_resolver

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
        return validate_execution_context_data(
            self.command_type,
            self.language, 
            self.contest_name,
            self.problem_name,
            self.env_json
        )

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

    @property
    def contest_stock_path(self):
        node = self.resolve([self.language, "contest_stock_path"])
        return node.value if node else None

    @property
    def contest_template_path(self):
        node = self.resolve([self.language, "contest_template_path"])
        return node.value if node else None

    @property
    def contest_temp_path(self):
        node = self.resolve([self.language, "contest_temp_path"])
        return node.value if node else None

    @property
    def source_file_name(self):
        node = self.resolve([self.language, "source_file_name"])
        return node.value if node else None

    def get_steps(self) -> list:
        """
        現在のlanguageとcommand_typeに基づきstepsのConfigNodeリストを返す。
        取得できない場合はValueErrorを投げる。
        """
        if not self.resolver:
            raise ValueError("resolverがセットされていません")
        return get_steps_from_resolver(self.resolver, self.language, self.command_type)

    @property
    def language_id(self):
        node = self.resolve([self.language, "language_id"])
        return node.value if node else None
