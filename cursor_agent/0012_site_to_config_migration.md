# Siteの削除とConfigへの移行

## 現状の課題
- `Site`列挙型が設定の柔軟性を制限している
- 新しいサイトの追加にはコードの変更が必要
- URLパターンがハードコードされている
- `Contest`構造体と`Site`の連携が不自然

## 実装方針
1. 設定ファイルの拡張
   ```yaml
   sites:
     atcoder:
       name: "AtCoder"
       url: "https://atcoder.jp"
       problem_url: "{url}/contests/{contest_id}/tasks/{problem_id}"
       submit_url: "{url}/contests/{contest_id}/submit"
       aliases: ["at", "ac"]
   ```

2. `Site`列挙型の削除
   - `src/cli/mod.rs`から`Site`列挙型を削除
   - `Contest`構造体から`site`フィールドを削除
   - 代わりに`site_id: String`を使用（設定のキーとして使用）

3. URL生成の移行
   ```rust
   impl Contest {
       fn get_site_url(&self, url_type: &str) -> Result<String> {
           let pattern = self.config.get::<String>(&format!("sites.{}.{}_url", self.site_id, url_type))?;
           
           Ok(pattern
               .replace("{url}", &self.config.get::<String>(&format!("sites.{}.url", self.site_id))?)
               .replace("{contest_id}", &self.contest_id)
               .replace("{problem_id}", &self.problem_id))
       }
   }
   ```

4. CLIの修正
   ```rust
   #[derive(Debug, Parser)]
   pub struct Cli {
       /// サイト名（例: atcoder）
       pub site: String,
       
       #[command(subcommand)]
       pub command: Commands,
   }
   ```

## 作業難易度
中程度：
- 複数ファイルの変更が必要
- 既存機能の移行作業が必要
- 設定ファイルの構造変更

## 影響範囲
- src/cli/mod.rs
- src/contest/mod.rs
- src/config/config.yaml
- src/cli/commands/*.rs

## 移行手順
1. 設定ファイルの更新
   - 既存の設定構造を維持
   - URLパターンの追加

2. `Contest`構造体の修正
   - `site`フィールドの型変更
   - URL生成メソッドの実装

3. CLIの修正
   - `Site`列挙型の削除
   - コマンドライン引数の型変更

4. 各コマンドの修正
   - `open`コマンドのURL生成処理
   - `submit`コマンドのURL生成処理
   - その他の関連コマンド

## テスト項目
1. 基本機能
   - 問題URLの生成
   - 提出URLの生成
   - サイトIDの解決（設定のキーとして）

2. エラーケース
   - 不正なサイトID
   - 不正なURLパターン
   - 設定値の欠落

3. 互換性
   - 既存のコマンドライン使用方法
   - 既存の設定ファイル 