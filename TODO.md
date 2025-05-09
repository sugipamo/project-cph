#TODO
#TODO

- src/docker/ctl.py, pool.py の機能を src/execution_client 側に移行する
- DockerCtl/DockerPool の呼び出しを ExecutionManager/ContainerClient などに置き換える
- 必要なコンテナの起動・調整ロジックを execution_client 側で実装する
- コマンド実行・ファイルコピー・状態管理も execution_client 側のAPIで統一する
- src/commands/ 配下の各コマンドの依存を書き換える
- system_info.json などの管理ロジックも新APIに合わせて調整する
- テスト・提出・open等のコマンドでの動作確認・修正
- ボリュームマウントや環境変数の扱いを確認・対応
- ローカル実行(local/client.py)との切り替えも考慮する