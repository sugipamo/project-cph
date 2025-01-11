# Container Module

## 使用例

### コンテナオーケストレーターを使用した制御
```rust
// オーケストレーターの作成
let orchestrator = ContainerOrchestrator::new();

// コンテナの追加
let container1 = orchestrator
    .add_container("python", "node1.py", vec!["python", "node1.py"])
    .await?;
let container2 = orchestrator
    .add_container("python", "node2.py", vec!["python", "node2.py"])
    .await?;
let container3 = orchestrator
    .add_container("python", "node3.py", vec!["python", "node3.py"])
    .await?;

// コンテナ間の通信リンクを設定
orchestrator
    .link(container1.id(), container2.id())
    .link(container2.id(), container3.id())
    .link(container3.id(), container1.id());

// 全コンテナを実行
orchestrator.run_all().await?;

// メッセージの送信（標準化されたフォーマット）
let message = Message::normal(
    container1.id().to_string(),
    container2.id().to_string(),
    "Hello from 1 to 2!".to_string(),
);
orchestrator.send_message(&message).await?;

// システムメッセージのブロードキャスト
let system_msg = Message::system(
    container1.id().to_string(),
    "System update".to_string(),
);
orchestrator.broadcast(&system_msg).await?;

// 全コンテナの終了を待機
// この間もメッセージの送受信は可能
orchestrator.wait_all().await?;
```

### メッセージの種類
```rust
// 通常のメッセージ
Message::normal(from, to, content)

// システムメッセージ（優先度: High）
Message::system(from, content)

// エラーメッセージ（優先度: Critical）
Message::error(from, content)

// デバッグメッセージ（優先度: Low）
Message::debug(from, content)

// ブロードキャストメッセージ
Message::broadcast(from, content)
```

## 要件

このモジュールは以下の要件を必ず満たす必要があります：

1. **並列実行**
   - 複数のコンテナを同時に実行可能であること
   - 各コンテナは独立して動作すること
   - 設定ファイル（src/config/config.yaml）に基づいたリソース制限の適用

2. **コンテナ間通信**
   - 実行中のコンテナ同士が相互に通信可能であること
   - メッセージベースの通信を提供すること
   - 非同期メッセージングによる効率的な通信

3. **出力バッファリング**
   - 各コンテナの出力は適切にバッファリングされること
   - バッファされた出力は指定された受け渡し先に確実に送信されること

4. **実行環境**
   - 各言語に対応したDockerイメージの使用
   - コンパイルと実行の分離
   - 安全なサンドボックス環境の提供 