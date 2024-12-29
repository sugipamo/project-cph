# CLI モジュールの更新計画

## 1. 影響を受ける箇所
### `src/cli/commands/language.rs`
- `Language` enumの使用を`LanguageConfig`に置き換え
- 言語の検証と設定の処理を更新
- エラーハンドリングの改善

### `src/cli/parser.rs`
- `Language` enumを使用したCLAP定義の更新
- 動的な言語リストの生成
- エイリアス解決の仕組みを新しい設定システムに対応

### `src/cli/mod.rs`
- `Site`と`Language`の関係性を再定義
- コマンド構造体の更新

## 2. 実装手順
1. **`LanguageConfig`の拡張**
   - CLAPサポートの追加
   - バリデーション機能の強化
   - エラー型の定義

2. **`language.rs`の更新**
   ```rust
   // 新しい実装イメージ
   impl LanguageCommand {
       async fn execute(&self, command: &Commands) -> Result<()> {
           let config_paths = config::get_config_paths();
           let lang_config = LanguageConfig::load(config_paths.languages)?;

           match command {
               Commands::Language { language } => {
                   // 言語の検証
                   let resolved = lang_config.resolve_language(language)
                       .ok_or_else(|| format!("無効な言語です: {}", language))?;

                   // コンテストの更新
                   let mut contest = Contest::new(self.context.active_contest_dir.clone())?;
                   contest.set_language(&resolved);
                   contest.save()?;

                   println!("言語を設定しました: {}", 
                       lang_config.get_display_name(&resolved)
                           .unwrap_or(resolved.clone()));
               }
               _ => {
                   // 現在の設定を表示
                   let contest = Contest::new(self.context.active_contest_dir.clone())?;
                   if let Some(current) = contest.language {
                       println!("現在の言語: {}", 
                           lang_config.get_display_name(&current)
                               .unwrap_or(current));
                   }
               }
           }
           Ok(())
       }
   }
   ```

3. **`parser.rs`の更新**
   - 動的な言語リストの生成
   - CLAPの設定を更新
   - エイリアス解決の実装

## 3. テスト計画
1. **ユニットテスト**
   - 言語解決のテスト
   - エイリアス解決のテスト
   - バリデーションのテスト

2. **統合テスト**
   - コマンドライン引数の解析
   - 設定ファイルとの連携
   - エラーケースの処理

## 4. 注意点
- 後方互換性の確保
- エラーメッセージの改善
- 設定ファイルの検証
- パフォーマンスの考慮 

# 残りのハードコード箇所

## 1. `src/docker/config.rs`
- `Languages`構造体でpythonとrustがハードコード
```rust
pub struct Languages {
    pub python: LanguageConfig,
    pub rust: LanguageConfig,
}
```
- `get_language_config`でマッピングがハードコード
```rust
match language {
    "python" | "py" => Some(&self.languages.python),
    "rust" | "rs" => Some(&self.languages.rust),
    _ => None,
}
```

## 2. `src/cli/parser.rs`
- サイトの検証でatcoderがハードコード
```rust
match args[1].as_str() {
    "atcoder" => "atcoder",
    _ => return Err("サポートされていないサイトです".into()),
}
```

## 3. `src/cli/mod.rs`
- `Site`enumでAtCoderのみハードコード
```rust
pub enum Site {
    /// AtCoder
    AtCoder,
}
```

## 4. ディレクトリパスの問題
- `docker/config.rs`の作業ディレクトリを`/compile`に修正済み
- 影響範囲の確認が必要
- 設定ファイルでパスを管理することを検討

## 5. dockerモジュールの依存関係
### コマンドとの関係
- `open`: oj-apiを使用してテストケースをダウンロード
- `test`: oj-apiを使用してテストを実行
- `submit`: oj-apiを使用して解答を提出

### 影響を受ける機能
1. テストケース関連
   - ダウンロード時のパス
   - 実行時のマウントポイント
   - 結果の取得

2. 提出関連
   - ソースコードのマウント
   - 言語IDの解決
   - 提出結果の取得

3. 共通設定
   - 作業ディレクトリ（`/compile`）
   - タイムアウト設定
   - メモリ制限

## 改善案
1. `docker/config.rs`
   - `Languages`をHashMapベースの動的な構造に変更
   - 言語設定を`languages.yaml`から読み込む

2. サイト関連
   - `sites.yaml`の活用
   - `Site`enumの動的生成を検討

3. パス設定
   - 作業ディレクトリのパスを設定ファイルで管理
   - 環境変数での制御も検討

4. Docker関連の設定の統合
   - `runner.yaml`の拡張
   - パスやマウントポイントの設定
   - タイムアウトやメモリ制限の柔軟な設定 