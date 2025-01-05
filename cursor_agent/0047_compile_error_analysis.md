# コンパイルエラー分析

## 1. `Contest`構造体の引数型の不一致

### 1.1 `Arc<Config>`の問題
```rust
// エラー箇所の例
let mut contest = Contest::new(&config, &self.contest_id)?;
```

- 期待される型: `Arc<Config>`
- 実際の型: `&Config`
- 影響を受けるファイル:
  - `src/cli/commands/work.rs`
  - `src/cli/commands/test.rs`
  - `src/cli/commands/language.rs`
  - `src/cli/commands/open.rs`
  - `src/cli/commands/submit.rs`
  - `src/cli/commands/generate.rs`
  - `src/cli/commands/login.rs`
  - `src/test/mod.rs`

## 2. プライベートフィールドへのアクセス問題

### 2.1 `site`フィールドへのアクセス
```rust
// エラー箇所
self.contest.site // プライベートフィールド
```
- 影響を受けるファイル: `src/oj/mod.rs`
- 解決策: `site()`メソッドを使用する必要がある

### 2.2 `active_contest_dir`フィールドへのアクセス
```rust
// エラー箇所
contest.active_contest_dir // プライベートフィールド
```
- 影響を受けるファイル: `src/test/mod.rs`
- 解決策: `active_contest_dir()`メソッドを使用する必要がある

## 3. 存在しないメソッドの呼び出し

### 3.1 未実装のメソッド
- `run_test`: `src/cli/commands/test.rs`
- `set_language`: `src/cli/commands/language.rs`
- `get_solution_language`: `src/cli/commands/submit.rs`
- `generate_test`: `src/cli/commands/generate.rs`

## 4. その他の警告

### 4.1 未使用のインポート
- `std::path::PathBuf`: `src/docker/runner/mod.rs`
- `std::process::Stdio`: `src/docker/runner/mod.rs`
- `tokio::process::Command`: `src/docker/runner/mod.rs`
- `Path`: `src/contest/fs/transaction.rs`

## 5. 修正の優先順位

1. `Arc<Config>`の型不一致
   - 最も広範囲に影響
   - 基本的な機能に関わる

2. プライベートフィールドのアクセス
   - カプセル化の問題
   - メソッド呼び出しへの変更で解決

3. 未実装メソッド
   - 機能の実装が必要
   - インターフェースの設計を検討

4. 未使用インポートの削除
   - 警告レベルの問題
   - 簡単に修正可能

## 6. 修正方針

1. `Contest::new`の呼び出し箇所の修正
   - `Arc::new(config)`を使用して`Config`をラップ
   - または`Contest::new`の引数型を変更

2. プライベートフィールドのアクセス
   - 適切なメソッド呼び出しに変更
   - 必要に応じてメソッドの可視性を調整

3. 未実装メソッドの追加
   - 各メソッドの仕様を検討
   - テストを含めた実装を行う

4. 不要なインポートの削除
   - 使用されていないインポートを特定
   - 安全に削除 