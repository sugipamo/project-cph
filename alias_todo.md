# エイリアス対応の実装状況と計画

## ✅ 完了した実装
1. エイリアス設定の基盤実装
   - `src/config/aliases.yaml`: 設定ファイルの作成
   - `src/config/aliases.rs`: 設定読み込みと解決ロジックの実装
   - テストケースの実装

2. サイトのエイリアス
   - AtCoderのエイリアス設定
   - `resolve_site`メソッドの実装
   - テストケースの追加

## 🚧 実装予定の機能

### 1. 言語の解決（最優先）
1. `src/lib.rs`の`Language`列挙型
   - 現在の実装: `FromStr`トレイトで直接ハードコーディング
   - 改善案: エイリアス設定を使用して解決する
   ```rust
   impl FromStr for Language {
       type Err = String;
       fn from_str(s: &str) -> Result<Self, Self::Err> {
           // TODO: エイリアス設定を使用
           let aliases = AliasConfig::load("src/config/aliases.yaml")?;
           match aliases.resolve_language(s) {
               Some("rust") => Ok(Language::Rust),
               Some("pypy") => Ok(Language::PyPy),
               _ => Err(format!("Unknown language: {}", s))
           }
       }
   }
   ```

2. `src/docker/config.rs`の`RunnerConfig`
   - 現在の実装: 直接文字列マッチング
   - 改善案: エイリアス設定を使用して言語を解決する
   ```rust
   impl RunnerConfig {
       pub fn get_language_config(&self, lang: &str) -> Option<&LanguageConfig> {
           // TODO: エイリアス設定を使用
           let aliases = AliasConfig::load("src/config/aliases.yaml")?;
           match aliases.resolve_language(lang).as_deref() {
               Some("python") => Some(&self.languages.python),
               Some("cpp") => Some(&self.languages.cpp),
               Some("rust") => Some(&self.languages.rust),
               _ => None,
           }
       }
   }
   ```

### 2. コマンドの解決
1. `src/cli.rs`の`CommonSubCommand`列挙型
   - 現在の実装: `clap`の`alias`属性で直接指定
   - 改善案: エイリアス設定を使用してコマンドを解決する
   - 注意点: `clap`との統合方法の検討が必要

### 3. サイトの解決
1. `src/cli.rs`の`Site`列挙型
   - 現在の実装: ハードコーディングされたエイリアス
   - 改善案: 実装済みの`resolve_site`メソッドを使用
   ```rust
   impl FromStr for Site {
       type Err = String;
       fn from_str(s: &str) -> Result<Self, Self::Err> {
           let aliases = AliasConfig::load("src/config/aliases.yaml")?;
           match aliases.resolve_site(s).as_deref() {
               Some("atcoder") => Ok(Site::AtCoder { command: default_command() }),
               _ => Err(format!("Unknown site: {}", s))
           }
       }
   }
   ```

## 📝 実装時の注意点
1. パフォーマンスの考慮
   - 設定ファイルの読み込みを最適化（キャッシュの検討）
   - エイリアス解決のメモリ使用量の最適化

2. エラーハンドリング
   - 設定ファイルが存在しない場合の対応
   - 無効なエイリアス設定の検出と報告

3. テストカバレッジ
   - エッジケースのテスト追加
   - 大文字小文字の組み合わせテスト
   - 無効な入力のテスト 