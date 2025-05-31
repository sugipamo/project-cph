from typing import Dict, Optional, Tuple, List
from src.context.execution_data import ExecutionData
from src.context.context_validator import ContextValidator
from src.context.config_resolver_proxy import ConfigResolverProxy
from src.context.utils.format_utils import format_with_missing_keys


class ExecutionContext:
    """
    実行コンテキストのファサードクラス
    分離された責務を統合して既存APIとの互換性を保つ
    """
    
    def __init__(self, command_type: str, language: str, contest_name: str, 
                 problem_name: str, env_type: str, env_json: dict, resolver=None):
        self._data = ExecutionData(
            command_type=command_type,
            language=language,
            contest_name=contest_name,
            problem_name=problem_name,
            env_type=env_type,
            env_json=env_json,
            resolver=resolver
        )
        self._validator = ContextValidator()
        self._config_resolver = ConfigResolverProxy(self._data)
    
    # データアクセス用プロパティ（既存APIとの互換性）
    @property
    def command_type(self):
        return self._data.command_type
    
    @command_type.setter
    def command_type(self, value):
        self._data.command_type = value
    
    @property
    def language(self):
        return self._data.language
    
    @language.setter
    def language(self, value):
        self._data.language = value
    
    @property
    def contest_name(self):
        return self._data.contest_name
    
    @contest_name.setter
    def contest_name(self, value):
        self._data.contest_name = value
    
    @property
    def problem_name(self):
        return self._data.problem_name
    
    @problem_name.setter
    def problem_name(self, value):
        self._data.problem_name = value
    
    @property
    def env_type(self):
        return self._data.env_type
    
    @env_type.setter
    def env_type(self, value):
        self._data.env_type = value
    
    @property
    def env_json(self):
        return self._data.env_json
    
    @env_json.setter
    def env_json(self, value):
        self._data.env_json = value
    
    @property
    def resolver(self):
        return self._data.resolver
    
    @resolver.setter
    def resolver(self, value):
        self._data.resolver = value
        self._config_resolver = ConfigResolverProxy(self._data)
    
    @property
    def dockerfile(self):
        return self._data.dockerfile
    
    @dockerfile.setter
    def dockerfile(self, value):
        self._data.dockerfile = value
    
    @property
    def oj_dockerfile(self):
        return self._data.oj_dockerfile
    
    @oj_dockerfile.setter
    def oj_dockerfile(self, value):
        self._data.oj_dockerfile = value
    
    @property
    def old_execution_context(self):
        return self._data.old_execution_context
    
    @old_execution_context.setter
    def old_execution_context(self, value):
        self._data.old_execution_context = value
    

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        基本的なバリデーションを行う
        
        Returns:
            Tuple[bool, Optional[str]]: (バリデーション結果, エラーメッセージ)
        """
        return self._validator.validate(self._data)

    def resolve(self, path: List[str]):
        """
        resolverを使ってパスで設定値ノードを解決する
        """
        return self._config_resolver.resolve(path)

    @property
    def workspace_path(self):
        return self._config_resolver.workspace_path

    @property
    def contest_current_path(self):
        return self._config_resolver.contest_current_path

    @property
    def contest_stock_path(self):
        node = self.resolve([self.language, "contest_stock_path"])
        return node.value if node else None

    @property
    def contest_template_path(self):
        return self._config_resolver.contest_template_path

    @property
    def contest_temp_path(self):
        return self._config_resolver.contest_temp_path

    @property
    def source_file_name(self):
        return self._config_resolver.source_file_name

    def get_steps(self) -> list:
        """
        現在のlanguageとcommand_typeに基づきstepsのConfigNodeリストを返す。
        取得できない場合はValueErrorを投げる。
        """
        return self._config_resolver.get_steps()

    @property
    def language_id(self):
        node = self.resolve([self.language, "language_id"])
        return node.value if node else None
