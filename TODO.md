# TODO: execution_client/ExecutionManager層とcommands層の連携

## 1. 目的
- Docker/ローカル/将来のクラウド等、実行環境を抽象化し、commands層から透過的に利用できるようにする
- ExecutionManager/ClientのDI設計で切り替え可能に

## 2. 主な作業項目

### (A) TestExecutionEnvironmentの抽象化・新実装
- [ ] DockerTestExecutionEnvironment依存を排除したExecutionManagerTestEnvironment（仮称）を新設
- [ ] ExecutionManager/ClientをDIで受け取る構造に
- [ ] run_test_case等でmanager.run_and_measureを利用

### (B) handlerのrun/buildの修正
- [ ] handler.run(ctl, container, ...) → handler.run(manager, name, ...)
- [ ] manager経由でコマンド実行・計測・タイムアウト等を統一

### (C) CommandTestの依存先差し替え
- [ ] self.env = ExecutionManagerTestEnvironment(...) で初期化
- [ ] run_test_cases等でcontainerではなくnameを渡す形に
- [ ] 既存DockerTestExecutionEnvironmentとの切り替えも容易に

### (D) main.py等でのDI例・切り替え実装
- [ ] LocalAsyncClient/ContainerClient等の切り替え例をmain.py等に追加

### (E) テスト・動作確認
- [ ] 単体・統合テストの修正・追加
- [ ] commands層からのend-to-end動作確認

## 3. 今後の拡張・課題
- [ ] SSH/クラウドクライアント等の追加設計
- [ ] ドキュメント・CI/CD整備
- [ ] 実運用でのパフォーマンス・安定性検証

---

必要に応じて細分化・追記してください。 