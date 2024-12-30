# E2Eテスト実装計画

## 1. テスト対象のコマンド

### 1.1 実行シーケンス
1. `cph atcoder work abc300`
2. `cph atcoder open a`
3. `cph atcoder submit a`

### 1.2 各コマンドの機能
- work: コンテストの作業ディレクトリを設定
- open: 問題ページを開く
- submit: 解答を提出

## 2. テスト実装方針

### 2.1 テストの基本構造
```rust
#[tokio::test]
async fn test_atcoder_workflow() {
    // テストの準備
    // コマンドの実行
    // 結果の検証
}
```

### 2.2 必要なモック
1. AtCoderのログイン状態
2. 問題ページのアクセス
3. 提出API

### 2.3 検証項目
1. workコマンド
   - active_contestディレクトリの作成
   - テンプレートファイルのコピー
   - コンテスト設定の保存

2. openコマンド
   - ソースファイルの作成
   - 問題URLの生成
   - エディタでの表示

3. submitコマンド
   - ソースコードの読み込み
   - 提出前のテスト実行
   - 提出処理

## 3. テストの実装手順

### 3.1 テストヘルパーの作成
1. テスト用のディレクトリ構造を作成
   - `tests/E2E/mod.rs`
   - `tests/E2E/helpers/mod.rs`
   - `tests/E2E/fixtures/`

2. 共通のヘルパー関数
   - テスト環境のセットアップ
   - クリーンアップ処理
   - モックサーバーの設定

### 3.2 テストケースの実装
1. 基本フロー
   ```rust
   setup_test_environment();
   execute_work_command();
   verify_work_results();
   execute_open_command();
   verify_open_results();
   execute_submit_command();
   verify_submit_results();
   cleanup_test_environment();
   ```

2. エラーケース
   - 無効なコンテストID
   - 存在しない問題
   - 提出失敗

### 3.3 検証関数の実装
1. ディレクトリ構造の検証
   ```rust
   fn verify_directory_structure() {
       // active_contestディレクトリの存在確認
       // テンプレートファイルの存在確認
       // 設定ファイルの存在確認
   }
   ```

2. ファイル内容の検証
   ```rust
   fn verify_file_contents() {
       // 設定ファイルの内容確認
       // ソースファイルの内容確認
   }
   ```

## 4. 実装の優先順位

### 4.1 第1フェーズ
1. テスト環境の基本設定
2. workコマンドのテスト実装
3. 基本的な検証関数の実装

### 4.2 第2フェーズ
1. openコマンドのテスト実装
2. モックサーバーの実装
3. URL生成の検証

### 4.3 第3フェーズ
1. submitコマンドのテスト実装
2. 提出APIのモック
3. エラーケースのテスト

## 5. 注意点

### 5.1 テスト環境
- テスト用の一時ディレクトリを使用
- テスト終了後のクリーンアップ
- 環境変数の適切な設定

### 5.2 非同期処理
- `tokio`テストランタイムの使用
- 適切なタイムアウト設定
- エラーハンドリング

### 5.3 モック
- 外部APIの適切なモック
- テスト用の設定ファイル
- エラー状態のシミュレーション 