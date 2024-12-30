# templates フォルダ移行に関するTODO

## 変更が必要なファイル

### src/contest/mod.rs
- Line 111: `templates/template` のパスを `contest_template/template` に変更する必要があります
```rust
let source = PathBuf::from("templates/template").join(&template_path.solution);
```

### tests/helpers/mod.rs
- Line 13-36: テストテンプレートのセットアップ関数で使用されているパスを更新する必要があります
```rust
pub fn setup_test_templates() {
    let templates_dir = PathBuf::from("tests/fixtures/templates");
    // ...
    let python_dir = templates_dir.join("python");
    // ...
    let rust_dir = templates_dir.join("rust");
}
```

### テストファイルでの参照
以下のファイルでテストテンプレートのセットアップ関数が呼び出されています：
- tests/lib.rs
- tests/docker/runners/mod.rs
- tests/docker/io_test.rs

これらのファイルについては、`setup_test_templates()`関数自体の実装を変更すれば、呼び出し側の変更は不要です。

## 移行手順
1. src/contest/mod.rs のパス参照を更新
2. tests/helpers/mod.rs のテストテンプレートセットアップ処理を更新
3. テストが正常に動作することを確認 