# プロジェクトのリンターエラー

## モジュール参照エラー

### 1. `workspace`モジュールが見つからない

以下の3つのファイルで同様のエラーが発生しています：

1. `src/cli/commands/open.rs`:
```rust
use crate::workspace::Workspace;
```

2. `src/cli/commands/generate.rs`:
```rust
use crate::workspace::Workspace;
```

3. `src/test/mod.rs`:
```rust
workspace::Workspace,
```

### エラーの詳細
- エラーコード: E0432
- エラー内容: unresolved import `crate::workspace`
- 原因: クレートのルートに`workspace`モジュールが見つからない

### 現在のモジュール構造 (`lib.rs`)
```rust
pub mod cli;
pub mod docker;
pub mod error;
pub mod test;
pub mod contest;
pub mod oj;
pub mod alias;
```

### 発見された問題
1. `src/workspace`ディレクトリが存在しない
2. `lib.rs`に`workspace`モジュールの宣言がない
3. 複数のファイルが存在しないモジュールを参照している

### 解決方針
1. `workspace`モジュールの作成
   - `src/workspace/mod.rs`を作成
   - `Workspace`構造体の実装
2. モジュールの依存関係の整理
   - `workspace`モジュールが必要とする他のモジュールとの関係を確認
   - 循環参照がないことを確認
3. `lib.rs`の更新
   - `pub mod workspace;`の追加

### 次のステップ
1. `src/workspace/mod.rs`の作成
2. `Workspace`構造体の実装
3. `lib.rs`へのモジュール宣言の追加
4. 依存関係のある各ファイルでの参照の確認 