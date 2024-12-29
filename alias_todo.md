# エイリアス実装の再設計計画（拡張性重視版）

## 🎯 設計方針

### 1. トレイトベースの設計
1. **エイリアス解決の抽象化**
   ```rust
   pub trait AliasResolver {
       fn resolve(&self, input: &str) -> Result<String>;
       fn validate(&self, resolved: &str) -> Result<()>;
   }
   ```

2. **カテゴリ別の実装**
   ```rust
   pub struct LanguageResolver {
       aliases: HashMap<String, String>,
       valid_values: HashSet<String>,
   }

   pub struct SiteResolver {
       aliases: HashMap<String, String>,
       supported_sites: HashSet<String>,
   }
   ```

### 2. 設定管理の改善
1. **YAML設定の構造化**
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

2. **バリデーションルール**
   ```yaml
   # validation.yaml
   rules:
     problem_id:
       pattern: "^[a-gA-G]$|^ex$"
     contest_id:
       prefixes: ["abc", "arc", "agc"]
       pattern: "^[a-z]{3}\\d+$"
   ```

## 📋 実装計画

### フェーズ1: 基盤整備（3h）
1. **トレイト定義**
   ```rust
   src/alias/
   ├── traits.rs      # 基本トレイト定義
   ├── resolvers/     # リゾルバー実装
   │   ├── language.rs
   │   ├── site.rs
   │   └── command.rs
   └── config.rs      # 設定読み込み
   ```

2. **設定構造の整備**
   - YAMLスキーマの定義
   - バリデーションルールの構造化
   - エラー型の整理

### フェーズ2: リゾルバー実装（3h）
1. **基本リゾルバー**
   ```rust
   impl AliasResolver for LanguageResolver {
       fn resolve(&self, input: &str) -> Result<String> {
           // エイリアス解決ロジック
       }
       
       fn validate(&self, resolved: &str) -> Result<()> {
           // バリデーションロジック
       }
   }
   ```

2. **コンテキスト管理**
   ```rust
   pub struct ResolutionContext {
       current_site: Option<String>,
       current_command: Option<String>,
   }
   ```

### フェーズ3: 拡張機能（2h）
1. **プラグイン機構**
   ```rust
   pub trait CommandHandler {
       fn handle(&self, args: &[String]) -> Result<()>;
       fn validate(&self, args: &[String]) -> Result<()>;
   }
   ```

2. **カスタムバリデーター**
   ```rust
   pub trait ValidationRule {
       fn validate(&self, value: &str) -> Result<()>;
   }
   ```

## ⚠️ 注意点

1. **後方互換性**
   - 既存の設定ファイル形式との互換性維持
   - 段階的な移行パス提供

2. **パフォーマンス**
   - 動的ディスパッチの使用は必要最小限に
   - キャッシュ戦略の検討

3. **エラーハンドリング**
   - エラーメッセージの改善
   - コンテキストを考慮したエラー情報

## 📝 将来の拡張性

1. **新規リゾルバー追加**
   - テストケースエイリアス
   - カスタムコマンド

2. **高度な機能**
   - 正規表現ベースのエイリアス
   - コンテキスト依存の解決ルール
   - 優先順位付きの解決

## 🔍 テスト計画

1. **単体テスト**
   - 各リゾルバーのテスト
   - バリデーションルールのテスト
   - エラーケースの網羅

2. **統合テスト**
   - 設定ファイル読み込み
   - エイリアス解決フロー
   - コマンド実行シナリオ