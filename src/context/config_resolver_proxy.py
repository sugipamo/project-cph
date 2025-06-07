"""Configuration resolver proxy
"""

from src.context.utils.validation_utils import get_steps_from_resolver
from src.utils.path_operations import (
    get_contest_current_path,
    get_contest_temp_path,
    get_contest_template_path,
    get_source_file_name,
    get_workspace_path,
)


class ConfigResolverProxy:
    """設定解決を担当するプロキシクラス"""

    def __init__(self, execution_data):
        self.execution_data = execution_data

    def resolve(self, path: list[str]):
        """resolverを使ってパスで設定値ノードを解決する

        Args:
            path: 解決対象のパス

        Returns:
            解決されたノード
        """
        if not self.execution_data.resolver:
            raise ValueError("resolverがセットされていません")
        from src.context.resolver.config_resolver import resolve_best
        return resolve_best(self.execution_data.resolver, path)

    @property
    def workspace_path(self):
        """ワークスペースパスを取得"""
        return get_workspace_path(self.execution_data.resolver, self.execution_data.language)

    @property
    def contest_current_path(self):
        """現在のコンテストパスを取得"""
        return get_contest_current_path(self.execution_data.resolver, self.execution_data.language)

    @property
    def contest_template_path(self):
        """コンテストテンプレートパスを取得"""
        return get_contest_template_path(self.execution_data.resolver, self.execution_data.language)

    @property
    def contest_temp_path(self):
        """コンテスト一時パスを取得"""
        return get_contest_temp_path(self.execution_data.resolver, self.execution_data.language)

    @property
    def source_file_name(self):
        """ソースファイル名を取得"""
        return get_source_file_name(self.execution_data.resolver, self.execution_data.language)

    def get_steps(self):
        """ステップ一覧を取得"""
        return get_steps_from_resolver(
            self.execution_data.resolver,
            self.execution_data.language,
            self.execution_data.command_type
        )
