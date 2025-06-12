"""プロパティアクセスの提供"""
from ..core.execution_configuration import ExecutionConfiguration


class ConfigurationPropertyProvider:
    """ExecutionConfigurationのプロパティアクセスを提供"""

    def __init__(self, config: ExecutionConfiguration):
        self.config = config

    @property
    def command_type(self) -> str:
        return self.config.command_type

    @property
    def language(self) -> str:
        return self.config.language

    @property
    def contest_name(self) -> str:
        return self.config.contest_name

    @property
    def problem_name(self) -> str:
        return self.config.problem_name

    @property
    def env_type(self) -> str:
        return self.config.env_type

    @property
    def workspace_path(self) -> str:
        return str(self.config.paths.workspace)

    @property
    def contest_current_path(self) -> str:
        return str(self.config.paths.contest_current)

    @property
    def contest_stock_path(self) -> str:
        return str(self.config.paths.contest_stock)

    @property
    def contest_template_path(self) -> str:
        return str(self.config.paths.contest_template)

    @property
    def contest_temp_path(self) -> str:
        return str(self.config.paths.contest_temp)
