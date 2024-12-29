# エイリアス実装の再設計計画（拡張性重視版）

## 🎯 設計方針

### 1. ディレクトリ構造
```
src/
├── cli/
│   ├── mod.rs           # CLIのエントリーポイント
│   ├── parser.rs        # コマンドライン引数のパーサー
│   └── commands/        # 各コマンドの実装
│       ├── mod.rs
│       ├── work.rs
│       ├── test.rs
│       └── language.rs
├── alias/
│   ├── mod.rs           # エイリアスシステムのエントリーポイント
│   ├── traits.rs        # トレイト定義
│   ├── resolvers/       # 各リゾルバーの実装
│   │   ├── mod.rs
│   │   ├── language.rs
│   │   └── site.rs
│   └── config.rs        # 設定管理
```

### 2. トレイトベースの設計
```rust
// src/alias/traits.rs
pub trait AliasResolver {
    fn resolve(&self, input: &str) -> Result<String>;
    fn validate(&self, resolved: &str) -> Result<()>;
}

// src/alias/resolvers/language.rs
pub struct LanguageResolver {
    aliases: HashMap<String, String>,
    valid_values: HashSet<String>,
}

// src/alias/resolvers/site.rs
pub struct SiteResolver {
    aliases: HashMap<String, String>,
    supported_sites: HashSet<String>,
}
```

### 3. 設定管理の改善
```yaml
# aliases.yaml
resolvers:
  language:
    valid_values:
      - python
      - cpp
      - rust
    aliases:
      python: ["py", "python3"]
      cpp: ["c++"]
  site:
    valid_values:
      - atcoder
    aliases:
      atcoder: ["at-coder", "ac"]
```

## 📋 実装計画

### フェーズ1: 基盤整備（3h）
1. **エイリアスシステムの実装**
   - トレイト定義
   - 基本リゾルバーの実装
   - 設定読み込み機能

2. **CLIシステムの整備**
   - パーサーの実装
   - コマンド構造の整理
   - エラーハンドリング

### フェーズ2: 機能実装（3h）
1. **コマンド実装**
   ```rust
   // src/cli/commands/work.rs
   pub struct WorkCommand {
       site: Site,
       contest_id: String,
   }

   impl Command for WorkCommand {
       fn execute(&self) -> Result<()>;
   }
   ```

2. **エイリアス解決**
   ```rust
   // src/alias/mod.rs
   pub struct AliasManager {
       resolvers: HashMap<String, Box<dyn AliasResolver>>,
   }
   ```

### フェーズ3: 統合とテスト（2h）
1. **統合テスト**
   ```rust
   #[test]
   fn test_command_resolution() {
       let cli = CliParser::new();
       let result = cli.parse(vec!["cph", "ac", "t", "a"]);
       assert_eq!(result.site, "atcoder");
       assert_eq!(result.command, "test");
       assert_eq!(result.args[0], "a");
   }
   ```

2. **エラーハンドリング**
   ```rust
   #[derive(Error, Debug)]
   pub enum AliasError {
       #[error("無効なエイリアス: {0}")]
       InvalidAlias(String),
       #[error("設定エラー: {0}")]
       ConfigError(String),
   }
   ```

## ⚠️ 注意点

1. **エラーハンドリング**
   - ユーザーフレンドリーなエラーメッセージ
   - コンテキストを考慮したエラー情報

2. **テスト戦略**
   - ユニットテスト
   - 統合テスト
   - エラーケースのテスト

## 📝 将来の拡張性

1. **新規リゾルバー**
   - テストケースエイリアス
   - カスタムコマンド

2. **高度な機能**
   - コンテキスト依存の解決ルール
   - 優先順位付きの解決

## 🔍 テスト計画

1. **ユニットテスト**
   - 各リゾルバーのテスト
   - パーサーのテスト
   - コマンド実行のテスト

2. **統合テスト**
   - エンドツーエンドのコマンド実行
   - エラーケースの検証
   - 設定ファイルの読み込み