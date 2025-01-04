# エラー処理の使用例

## 1. 基本的な使用方法

### 1.1 コンテキストの追加
```rust
fn load_config(path: &Path) -> Result<Config> {
    std::fs::read_to_string(path)
        .map_err(|e| ContestError::from(e)
            .with_context("設定ファイルの読み込み", path.display().to_string())
            .add_hint("ファイルが存在し、読み取り権限があることを確認してください"))
        .and_then(|content| serde_yaml::from_str(&content)
            .map_err(|e| ContestError::from(e)
                .with_context("設定ファイルのパース", path.display().to_string())
                .add_hint("YAMLの形式が正しいことを確認してください")))
}
```

### 1.2 トランザクションでの使用
```rust
fn execute_transaction(&mut self) -> Result<()> {
    let mut context = ErrorContext::new("トランザクション実行", &self.name)
        .with_hint("トランザクションの操作順序を確認してください");

    for operation in &self.operations {
        if let Err(e) = operation.execute() {
            context = context.with_hint(format!(
                "操作 '{}' が失敗しました。前の操作をロールバックします。",
                operation.description()
            ));
            return Err(ContestError::Transaction {
                message: "トランザクションの実行に失敗".to_string(),
                context,
            });
        }
    }
    Ok(())
}
```

## 2. エラーメッセージの例

### 2.1 設定エラー
```text
設定エラー: YAMLのパースに失敗: expected mapping at line 2 column 1 
(操作: 設定ファイルの読み込み, 場所: config.yaml)
ヒント: YAMLの形式が正しいことを確認してください
```

### 2.2 ファイルシステムエラー
```text
ファイルシステムエラー: パーミッションが拒否されました 
(操作: ファイル作成, 場所: /path/to/file.txt)
ヒント: ファイルの権限を確認してください
```

### 2.3 トランザクションエラー
```text
トランザクションエラー: トランザクションの実行に失敗 
(操作: コンテストファイルの作成, 場所: contest_123)
ヒント: 操作 'ディレクトリ作成' が失敗しました。前の操作をロールバックします。
スタックトレース:
   0: cph::contest::fs::transaction::execute_transaction
   1: cph::contest::fs::manager::create_contest_directory
   2: cph::contest::manager::create_contest
```

## 3. エラー処理のベストプラクティス

1. コンテキストの追加
   - 操作の種類を明確に
   - 場所を具体的に
   - 関連するパスや識別子を含める

2. ヒントの提供
   - 問題の原因を説明
   - 解決方法を提案
   - 具体的な手順を示す

3. デバッグ情報
   - デバッグビルドでスタックトレースを含める
   - 関連する変数の値を記録
   - システムの状態を説明

## 4. 今後の改善案

1. エラーの分類
   - 重要度によるエラーの分類
   - ユーザーエラーとシステムエラーの区別
   - リカバリー可能なエラーの識別

2. エラーレポート
   - エラーログの構造化
   - エラー統計の収集
   - 自動エラー分析

3. エラー処理の自動化
   - 共通エラーパターンの検出
   - 自動リカバリーの実装
   - エラー予防メカニズム

## まとめ

新しいエラー処理機能により、より詳細なエラー情報の提供が可能になりました。
これにより、問題の診断と解決が容易になり、ユーザーエクスペリエンスが向上します。
今後も継続的な改善を行い、より堅牢なエラー処理システムを目指します。 