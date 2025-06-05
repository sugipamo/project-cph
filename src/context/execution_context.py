from typing import Dict, Optional, Tuple, List
from src.context.execution_data import ExecutionData
from src.context.context_validator import ContextValidator
from src.context.config_resolver_proxy import ConfigResolverProxy
from src.context.utils.format_utils import format_with_missing_keys
from src.context.dockerfile_resolver import DockerfileResolver
from src.pure_functions.execution_context_formatter_pure import (
    ExecutionFormatData, create_format_dict, format_template_string,
    validate_execution_data, get_docker_naming_from_data
)
from src.utils.path_operations import DockerPathOperations


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
        self._dockerfile_resolver: Optional[DockerfileResolver] = None
    
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
    def dockerfile_resolver(self) -> Optional[DockerfileResolver]:
        """Get the Dockerfile resolver for lazy loading"""
        return self._dockerfile_resolver
    
    @dockerfile_resolver.setter
    def dockerfile_resolver(self, value: Optional[DockerfileResolver]):
        """Set the Dockerfile resolver"""
        self._dockerfile_resolver = value

    @property
    def dockerfile(self):
        """Get dockerfile content via resolver (lazy loading)"""
        if self._dockerfile_resolver:
            return self._dockerfile_resolver.dockerfile
        return None
    
    @dockerfile.setter
    def dockerfile(self, value):
        """Set dockerfile content (backward compatibility - discouraged)"""
        # For backward compatibility only - consider deprecating
        # Content should be managed via resolver
        pass
    
    @property
    def oj_dockerfile(self):
        """Get OJ dockerfile content via resolver (lazy loading)"""
        if self._dockerfile_resolver:
            return self._dockerfile_resolver.oj_dockerfile
        return None
    
    @oj_dockerfile.setter
    def oj_dockerfile(self, value):
        """Set OJ dockerfile content (backward compatibility - discouraged)"""
        # For backward compatibility only - consider deprecating
        # Content should be managed via resolver
        pass
    
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
        # 純粋関数を使用してバリデーション
        format_data = ExecutionFormatData(
            command_type=self.command_type,
            language=self.language,
            contest_name=self.contest_name,
            problem_name=self.problem_name,
            env_type=self.env_type,
            env_json=self.env_json
        )
        return validate_execution_data(format_data)

    def resolve(self, path: List[str]):
        """
        resolverを使ってパスで設定値ノードを解決する
        """
        return self._config_resolver.resolve(path)
    
    def to_format_dict(self) -> Dict[str, str]:
        """
        フォーマット用の辞書を返す
        
        Returns:
            Dict[str, str]: フォーマット用のキーと値の辞書
        """
        # 純粋関数を使用して辞書を生成
        format_data = ExecutionFormatData(
            command_type=self.command_type,
            language=self.language,
            contest_name=self.contest_name,
            problem_name=self.problem_name,
            env_type=self.env_type,
            env_json=self.env_json
        )
        return create_format_dict(format_data)

    def format_string(self, template: str) -> str:
        """
        Format a template string using the current context
        
        Args:
            template: Template string with {key} placeholders
            
        Returns:
            Formatted string
        """
        # 純粋関数を使用してフォーマット
        format_data = ExecutionFormatData(
            command_type=self.command_type,
            language=self.language,
            contest_name=self.contest_name,
            problem_name=self.problem_name,
            env_type=self.env_type,
            env_json=self.env_json
        )
        return format_template_string(template, format_data)[0]

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
    
    def get_docker_names(self) -> dict:
        """Get Docker naming for current context
        
        Returns:
            Dictionary with image_name, container_name, oj_image_name, oj_container_name
        """
        # 純粋関数を使用してDocker名を生成
        format_data = ExecutionFormatData(
            command_type=self.command_type,
            language=self.language,
            contest_name=self.contest_name,
            problem_name=self.problem_name,
            env_type=self.env_type,
            env_json=self.env_json
        )
        
        dockerfile_content = None
        oj_dockerfile_content = None
        
        if self._dockerfile_resolver:
            dockerfile_content = self._dockerfile_resolver.dockerfile
            oj_dockerfile_content = self._dockerfile_resolver.oj_dockerfile
        
        return get_docker_naming_from_data(
            format_data,
            dockerfile_content,
            oj_dockerfile_content
        )
    
    def get_docker_mount_path(self) -> str:
        """Get Docker mount path from configuration
        
        Returns:
            Docker mount path (default: /workspace)
        """
        return DockerPathOperations.get_docker_mount_path_from_config(
            self.env_json,
            self.language,
            '/workspace'
        )
