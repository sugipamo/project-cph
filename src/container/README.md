# Container Module

## 使用例

### 基本的なコンテナの作成と実行
```rust
let container = ContainerBuilder::new()
    .with_buffer(Arc::new(Buffer::new()))
    .build_for_language("python", "script.py", vec!["python", "script.py"])
    .await?;

container.run().await?;
```

### コンテナ間のメッセージング
```rust
// 共有ネットワークの作成
let network = Arc::new(Network::new());

// 送信側コンテナ
let sender = ContainerBuilder::new()
    .with_network(network.clone())
    .with_buffer(Arc::new(Buffer::new()))
    .build_for_language("python", "sender.py", vec!["python", "sender.py"])
    .await?;

// 受信側コンテナ
let receiver = ContainerBuilder::new()
    .with_network(network.clone())
    .with_buffer(Arc::new(Buffer::new()))
    .build_for_language("python", "receiver.py", vec!["python", "receiver.py"])
    .await?;

// メッセージの送信
network.send(&sender.id(), &receiver.id(), "Hello!").await?;

// ブロードキャストメッセージ
network.broadcast(&sender.id(), "Broadcast message").await?;
```

### 並列実行
```rust
let containers = vec![
    ContainerBuilder::new()
        .with_network(network.clone())
        .with_buffer(Arc::new(Buffer::new()))
        .build_for_language("python", "node1.py", vec!["python", "node1.py"])
        .await?,
    ContainerBuilder::new()
        .with_network(network.clone())
        .with_buffer(Arc::new(Buffer::new()))
        .build_for_language("python", "node2.py", vec!["python", "node2.py"])
        .await?,
];

// 並列実行
let handles: Vec<_> = containers.iter()
    .map(|container| {
        tokio::spawn(container.run())
    })
    .collect();

// 全てのコンテナの完了を待機
for handle in handles {
    handle.await??;
}
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