from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum, auto
from src.env.resource.utils.path_resolver import PathResolver
from src.env.resource.utils.image_name_resolver import ImageNameResolver
from src.env.resource.utils.env_config_accessor import EnvConfigAccessor
from src.context.execution_context import ExecutionContext

DEFAULT_WORKSPACE_PATH = "./workspace"

class EnvType(Enum):
    LOCAL = auto()
    DOCKER = auto()

class ConstHandler:
    def __init__(self, config: ExecutionContext):
        # workspace_pathが未設定なら例外を投げる
        if not hasattr(config, 'workspace_path') or config.workspace_path is None:
            raise ValueError("workspace_pathがNoneです。必ず有効なパスを指定してください。")
        workspace_path = config.workspace_path
        self.config = config
        self.path_resolver = PathResolver(config, workspace_path)
        self.image_name_resolver = ImageNameResolver(config)
        self.config_accessor = EnvConfigAccessor(config)

    @property
    def workspace_path(self):
        return self.path_resolver.workspace_path

    @property
    def contest_current_path(self):
        return self.path_resolver.contest_current_path

    @property
    def contest_env_path(self):
        return self.path_resolver.contest_env_path

    @property
    def contest_template_path(self):
        return self.path_resolver.contest_template_path

    @property
    def contest_temp_path(self):
        return self.path_resolver.contest_temp_path

    @property
    def test_case_path(self):
        return self.path_resolver.test_case_path

    @property
    def test_case_in_path(self):
        return self.path_resolver.test_case_in_path

    @property
    def test_case_out_path(self):
        return self.path_resolver.test_case_out_path

    @property
    def image_name(self):
        return self.image_name_resolver.image_name

    @property
    def container_name(self):
        return self.image_name_resolver.container_name

    @property
    def base_image_name(self):
        return self.image_name_resolver.base_image_name

    @property
    def base_oj_image_name(self):
        return self.image_name_resolver.base_oj_image_name

    @property
    def oj_image_name(self):
        return self.image_name_resolver.oj_image_name

    @property
    def oj_container_name(self):
        return self.image_name_resolver.oj_container_name

    @property
    def dockerfile_text(self):
        return self.image_name_resolver.dockerfile_text

    @property
    def oj_dockerfile_text(self):
        return self.image_name_resolver.oj_dockerfile_text

    @property
    def source_file_name(self):
        return self.config_accessor.source_file_name

    def parse(self, s: str) -> str:
        # 変数展開: {contest_current} など
        result = s
        result = result.replace("{workspace_path}", str(self.workspace_path))
        result = result.replace("{contest_current_path}", str(self.contest_current_path))
        result = result.replace("{source_file}", str(self.source_file_name))
        result = result.replace("{source_file_name}", str(self.source_file_name))
        result = result.replace("{contest_env}", str(self.contest_env_path))
        result = result.replace("{contest_template}", str(self.contest_template_path))
        result = result.replace("{contest_temp}", str(self.contest_temp_path))
        result = result.replace("{test_case}", str(self.test_case_path))
        result = result.replace("{test_case_in}", str(self.test_case_in_path))
        result = result.replace("{test_case_out}", str(self.test_case_out_path))
        return result
