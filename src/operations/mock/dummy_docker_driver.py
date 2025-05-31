"""
Dummy Docker driver implementation
"""
from src.operations.docker.docker_driver import DockerDriver
from typing import Dict, Any, Optional


class DummyDockerDriver(DockerDriver):
    """
    何も実行しないダミーのDockerドライバー
    CI環境やテスト環境でDockerが利用できない場合に使用
    """
    
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None, show_output: bool = True):
        """コンテナを実行する（ダミー実装）"""
        return None

    def stop_container(self, name: str, show_output: bool = True):
        """コンテナを停止する（ダミー実装）"""
        pass

    def remove_container(self, name: str, show_output: bool = True):
        """コンテナを削除する（ダミー実装）"""
        pass

    def exec_in_container(self, name: str, command: str, show_output: bool = True):
        """コンテナ内でコマンドを実行する（ダミー実装）"""
        return None

    def get_logs(self, name: str, show_output: bool = True):
        """コンテナのログを取得する（ダミー実装）"""
        return None

    def build(self, tag: str = None, options: Dict[str, Any] = None, show_output: bool = True, dockerfile_text: str = None):
        """Dockerイメージをビルドする（ダミー実装）"""
        return None

    def image_ls(self, show_output: bool = True):
        """イメージ一覧を取得する（ダミー実装）"""
        return []

    def image_rm(self, image: str, show_output: bool = True):
        """イメージを削除する（ダミー実装）"""
        return None

    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        """コンテナ一覧を取得する（ダミー実装）"""
        return []

    def inspect(self, target: str, type_: str = None, show_output: bool = True):
        """Docker オブジェクトの詳細情報を取得する（ダミー実装）"""
        return None

    def cp(self, src: str, dst: str, container: str, to_container: bool = True, show_output: bool = True):
        """ファイルをコンテナとの間でコピーする（ダミー実装）"""
        pass