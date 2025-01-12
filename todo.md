# Container関連の実装TODO

## 優先度高
1. コマンド実行時の標準出力/エラー出力のキャプチャ
   - ExecProcessRequestにストリームハンドラを追加
   - 出力のバッファリング実装

## 優先度中
1. スナップショット管理の改善
   - 不要なスナップショットの自動クリーンアップ
   - スナップショットの命名規則の整備

2. エラーハンドリングの強化
   - タイムアウト処理の追加
   - リトライ機構の実装

## 検討事項
1. コンテナのリソース制限
   - メモリ制限
   - CPU制限
   - ディスク使用量制限 

## 類似した名前や機能を持つファイルの整理

### 状態管理関連
- src/container/state/status.rs (ContainerStatus)
- src/container/runtime/container.rs (State)

### オーケストレーション関連
- src/container/orchestrator.rs (高レベルオーケストレーション)
- src/container/runtime/orchestrator.rs (ランタイムレベルオーケストレーション)

### Containerd関連
- src/container/runtime/containerd.rs (ランタイム実装)
- src/container/registry/image.rs (イメージ管理)

これらのファイルは異なる責務を持っていますが、名前や機能が似ているため、コードベースを理解する際に注意が必要です。 