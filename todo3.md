# ハードコードされた言語設定の一覧

## src/contest/mod.rs
- 20行目: デフォルト言語として"rust"がハードコードされている
- 71行目: 言語と拡張子のマッピングがハードコードされている

## src/docker/config.rs
- 46-47行目: 拡張子と言語のマッピングがハードコードされている
  ```rust
  "py" => self.languages.languages.get("python"),
  "rs" => self.languages.languages.get("rust"),
  ```

## テストファイル
- tests/docker/runners/mod.rs: 複数箇所で"python"がテストケースとしてハードコードされている
- tests/docker/io_test.rs: テストケースで"python"がハードコードされている
- tests/docker/config_test.rs: テストケースで複数の言語設定がハードコードされている

# 改善提案
1. テストケースでも設定ファイルから言語情報を読み込むように変更する
2. 拡張子と言語のマッピングも設定ファイルで管理する
3. デフォルト言語の設定も設定ファイルで管理する 