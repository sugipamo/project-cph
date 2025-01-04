# CLI構造の再設計

## 1. 現状の問題点

### 1.1 コマンド構造の複雑さ
- コマンドごとに構造体を作成
- トレイト実装のオーバーヘッド
- 非同期処理の必要性が不明確

### 1.2 状態管理の問題
- `CommandContext`を介した状態の受け渡し
- コマンド間でのコンテキスト共有が不透明
- 設定の読み込みが分散

### 1.3 エラー処理の不統一
- 文字列ベースのエラー
- 型安全性の欠如
- エラーコンテキストの不足

## 2. 新しい設計案

### 2.1 シンプルな関数ベースのアプローチ
```rust
// src/cli/mod.rs
pub mod commands {
    use crate::config::Config;
    use crate::error::Result;

    pub fn test(config: &Config, problem_id: &str, site_id: &str) -> Result<()> {
        crate::test::run_test(config, problem_id, site_id)
    }

    pub fn set_language(config: &Config, problem_id: &str, language: &str) -> Result<()> {
        crate::language::set_language(config, problem_id, language)
    }

    pub fn submit(config: &Config, problem_id: &str, site_id: &str) -> Result<()> {
        crate::submit::submit_solution(config, problem_id, site_id)
    }
}
```

### 2.2 コマンドライン引数のパース
```rust
// src/cli/args.rs
pub struct Args {
    pub command: Command,
    pub problem_id: String,
    pub site_id: String,
}

pub enum Command {
    Test,
    Language { language: String },
    Submit,
    Generate,
}

impl Args {
    pub fn parse() -> Result<Self> {
        // clap を使用して引数をパース
    }
}
```

### 2.3 メインエントリーポイント
```rust
// src/main.rs
fn main() -> Result<()> {
    // 引数をパース
    let args = Args::parse()?;

    // 設定を読み込む（一度だけ）
    let config = Config::load()?;

    // コマンドを実行
    match args.command {
        Command::Test => commands::test(&config, &args.problem_id, &args.site_id)?,
        Command::Language { language } => commands::set_language(&config, &args.problem_id, &language)?,
        Command::Submit => commands::submit(&config, &args.problem_id, &args.site_id)?,
        Command::Generate => commands::generate(&config, &args.problem_id)?,
    }

    Ok(())
}
```

## 3. 改善点

### 3.1 シンプル化
- 構造体とトレイトの削除
- 直接的な関数呼び出し
- 状態管理の簡素化

### 3.2 型安全性
- 適切な型の使用
- コンパイル時のエラーチェック
- 明確なエラー型

### 3.3 設定管理
- 一元的な設定読み込み
- 設定の共有
- 一貫した設定アクセス

### 3.4 エラー処理
- 統一されたエラー型
- 文脈を含むエラーメッセージ
- エラーの伝播

## 4. 移行計画

1. 新しい引数パーサーの実装
   - `clap`を使用
   - コマンドと引数の定義
   - ヘルプメッセージの改善

2. コマンド関数の実装
   - 既存の機能を関数として再実装
   - エラー処理の統一
   - テストの追加

3. 既存コードの置き換え
   - 段階的な移行
   - 後方互換性の維持
   - テストでの検証

## 5. 期待される効果

1. コードの簡素化
   - 理解しやすい構造
   - メンテナンスの容易さ
   - デバッグの簡易化

2. 信頼性の向上
   - 型安全性の確保
   - エラー処理の改善
   - テストの容易さ

3. パフォーマンスの最適化
   - 不要なオーバーヘッドの削除
   - メモリ使用量の削減
   - 起動時間の短縮

## まとめ

CLIの再設計により、より保守しやすく、信頼性の高いコードベースを実現できます。
関数ベースのアプローチと適切な型の使用により、コードの複雑さを大幅に削減し、
エラー処理と設定管理を改善することができます。 