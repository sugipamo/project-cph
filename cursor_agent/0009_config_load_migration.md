# 設定読み込み方式の移行計画

## 現状の問題
`Config::builder()`の戻り値型を`ConfigBuilder`に変更したことで、多くのファイルで`map_err`や`?`演算子を使用している箇所でエラーが発生しています。

## 影響を受けているファイルと行数
1. `src/docker/runner/mod.rs`
   - 110行目: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`
   - 180行目: 同上
   - 221行目: 同上

2. `src/oj/mod.rs`
   - 59行目: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`
   - 200行目: 同上
   - 259行目: 同上

3. `src/cli/commands/`
   - `work.rs:28`: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`
   - `language.rs:47`: 同上
   - `submit.rs:24`: 同上
   - `generate.rs:53`: 同上

4. `src/test/mod.rs`
   - 10行目: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`

5. `src/contest/mod.rs`
   - 23行目: `.expect("Failed to load config")`
   - 95行目: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`
   - 118行目: 同上
   - 157行目: `Config::builder()?`
   - 175行目: 同上
   - 231行目: `.map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?`
   - 309行目: 同上
   - 365行目: 同上

6. `src/docker/config.rs`
   - 22行目: `Config::builder()?`

## 修正方針
1. `Config::load()`メソッドを復活させ、内部で以下の処理を行う：
   - デフォルトの設定ファイルパスを使用
   - `builder()`と`from_file()`を組み合わせて設定を読み込む
   - エラーハンドリングを統一

2. 各ファイルの修正方法：
   - `Config::builder()`の呼び出しを`Config::load()`に置き換える
   - エラーメッセージは統一して「設定の読み込みに失敗しました」を使用

## 作業難易度
🟡 中程度
- 多くのファイルで同様の修正が必要
- エラーハンドリングの統一が必要

## 移行手順
1. `Config::load()`メソッドの再実装
   ```rust
   impl Config {
       pub fn load() -> Result<Self, ConfigError> {
           let config_path = "src/config/config.yaml";
           let builder = ConfigBuilder::new();
           Self::from_file(config_path, builder)
       }
   }
   ```

2. 各ファイルでの修正例：
   ```rust
   // 修正前
   let config = Config::builder()
       .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;

   // 修正後
   let config = Config::load()
       .map_err(|e| format!("設定の読み込みに失敗しました: {}", e))?;
   ```

## 期待される効果
1. コードの一貫性向上
   - 設定読み込みのパターンが統一される
   - エラーメッセージが統一される

2. 保守性の向上
   - 設定読み込みのロジックが一箇所に集中
   - 将来的な変更が容易

3. エラーハンドリングの改善
   - エラーメッセージの統一
   - エラー処理の一貫性確保 